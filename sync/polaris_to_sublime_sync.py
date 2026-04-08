#!/usr/bin/env python3
"""
polaris_to_sublime_sync.py
Nightly sync: Polaris patron emails → Sublime Security (3 lists by patron type).

Flow:
  1. Connect to Gmail (your sync service account) via IMAP
  2. For each of 3 SSRS subscription emails (matched by subject line),
     extract the CSV attachment
  3. Parse and normalize email addresses from each CSV
  4. Apply cross-list priority dedup: FULL > DIGITAL > LIMITED
     (a patron with multiple accounts only appears in their highest-priority list)
  5. Bulk PATCH each list to Sublime Security
  6. Delete processed report emails from inbox

Patron groups (adapt PatronCodeIDs to match your Polaris instance):
  patron_emails_full    — Full cardholder      (RHPL example: PatronCodes 1,3,6,8,14,24,25,26,29)
  patron_emails_digital — Digital/eCard only   (RHPL example: PatronCodes 15,20,27)
  patron_emails_limited — Limited/restricted   (RHPL example: PatronCodes 2,4,9,17)
  Excluded (no banner)  — Staff-only cards     (RHPL example: PatronCodes 7,19,22)

See ssrs/ for the SQL queries that produce each CSV and the discover-patron-codes.sql
helper to identify which PatronCodeIDs apply at your library.

Credentials are loaded from .env in the same directory.
See .env.template for the required variables.
"""

import csv
import email
import imaplib
import io
import logging
import logging.handlers
import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
GMAIL_ADDRESS      = os.environ['GMAIL_ADDRESS']
GMAIL_APP_PASSWORD = os.environ['GMAIL_APP_PASSWORD']
STAFF_EMAIL_DOMAIN = os.environ.get('STAFF_EMAIL_DOMAIN', 'yourlibrary.org')

SUBLIME_API_KEY  = os.environ['SUBLIME_API_KEY']
SUBLIME_BASE_URL = os.environ.get('SUBLIME_BASE_URL', 'https://platform.sublime.security')

SCRIPT_DIR    = os.path.dirname(os.path.abspath(__file__))
LOG_FILE      = os.path.join(SCRIPT_DIR, 'polaris_sync.log')
LOG_MAX_BYTES = 5 * 1024 * 1024  # 5 MB

# One entry per patron group — order defines priority (index 0 = highest).
# List names must match the names you create in the Sublime dashboard.
# Subject lines must match your SSRS subscription subjects exactly.
LISTS = [
    {
        'name':        'patron_emails_full',
        'subject':     os.environ.get('SSRS_SUBJECT_FULL',    'Sublime Full Patron Export'),
        'list_id_key': 'SUBLIME_LIST_ID_FULL',
    },
    {
        'name':        'patron_emails_digital',
        'subject':     os.environ.get('SSRS_SUBJECT_DIGITAL', 'Sublime Digital Patron Export'),
        'list_id_key': 'SUBLIME_LIST_ID_DIGITAL',
    },
    {
        'name':        'patron_emails_limited',
        'subject':     os.environ.get('SSRS_SUBJECT_LIMITED', 'Sublime Limited Patron Export'),
        'list_id_key': 'SUBLIME_LIST_ID_LIMITED',
    },
]


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
def setup_logging() -> logging.Logger:
    logger = logging.getLogger('polaris_sync')
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE, maxBytes=LOG_MAX_BYTES, backupCount=3, encoding='utf-8'
    )
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(fmt)
    logger.addHandler(console_handler)

    return logger


# ---------------------------------------------------------------------------
# Gmail / IMAP helpers
# ---------------------------------------------------------------------------
def connect_gmail(logger: logging.Logger) -> imaplib.IMAP4_SSL:
    logger.info(f'Connecting to Gmail as {GMAIL_ADDRESS}...')
    mail = imaplib.IMAP4_SSL('imap.gmail.com', 993)
    mail.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
    mail.select('INBOX')
    return mail


def fetch_csv_for_subject(mail: imaplib.IMAP4_SSL, subject: str,
                          logger: logging.Logger) -> tuple[str | None, list]:
    """
    Find emails matching `subject`, extract CSV from the most recent one.
    Returns (csv_text, all_msg_ids) — csv_text is None if no matching email found.
    """
    status, data = mail.search(None, f'SUBJECT "{subject}"')
    if status != 'OK' or not data[0]:
        logger.warning(f'No email found with subject "{subject}" — skipping this list')
        return None, []

    msg_ids = data[0].split()
    logger.info(f'Subject "{subject}": found {len(msg_ids)} email(s) — using most recent')

    latest_id = msg_ids[-1]
    status, msg_data = mail.fetch(latest_id, '(RFC822)')
    raw_email = msg_data[0][1]
    msg = email.message_from_bytes(raw_email)

    for part in msg.walk():
        content_type = part.get_content_type()
        filename     = part.get_filename() or ''
        if content_type == 'text/csv' or filename.lower().endswith('.csv'):
            payload  = part.get_payload(decode=True)
            csv_text = payload.decode('utf-8-sig')
            logger.info(f'  CSV attachment: {filename} ({len(payload)} bytes)')
            return csv_text, msg_ids

    logger.warning(f'Email found for "{subject}" but no CSV attachment — skipping')
    return None, msg_ids


def cleanup_gmail(mail: imaplib.IMAP4_SSL, all_msg_ids: list,
                  logger: logging.Logger) -> None:
    """Delete all collected report emails after a successful sync."""
    if not all_msg_ids:
        return
    try:
        for msg_id in all_msg_ids:
            mail.store(msg_id, '+FLAGS', '\\Deleted')
        mail.expunge()
        logger.info(f'Deleted {len(all_msg_ids)} processed report email(s) from inbox')
    except Exception as exc:
        logger.warning(f'Email cleanup failed (non-fatal): {exc}')
    finally:
        mail.logout()


# ---------------------------------------------------------------------------
# Email parsing
# ---------------------------------------------------------------------------
def parse_emails(csv_text: str, logger: logging.Logger) -> set:
    """Parse a single-column CSV of email addresses into a normalized set."""
    reader  = csv.reader(io.StringIO(csv_text))
    cleaned = set()
    skipped = 0

    for row in reader:
        if not row:
            continue
        addr = row[0].strip()
        if '@' not in addr:   # skip header rows and blanks
            continue
        normalized = addr.lower()
        if normalized.endswith(f'@{STAFF_EMAIL_DOMAIN}'):
            skipped += 1
            continue
        cleaned.add(normalized)

    if skipped:
        logger.info(f'  Filtered {skipped} @{STAFF_EMAIL_DOMAIN} address(es)')
    return cleaned


# ---------------------------------------------------------------------------
# Sublime Security helpers
# ---------------------------------------------------------------------------
def _sublime_headers() -> dict:
    return {
        'Authorization': f'Bearer {SUBLIME_API_KEY}',
        'Content-Type':  'application/json',
    }


def get_list_id(list_name: str, env_key: str, logger: logging.Logger) -> str:
    """Prefer .env override; fall back to API name lookup."""
    list_id = os.environ.get(env_key, '').strip()
    if list_id:
        logger.info(f'  List "{list_name}" id from .env: {list_id}')
        return list_id

    resp = requests.get(
        f'{SUBLIME_BASE_URL}/v1/lists',
        headers=_sublime_headers(),
        timeout=30,
    )
    resp.raise_for_status()
    for lst in resp.json():
        if lst.get('name') == list_name:
            logger.info(f'  Found "{list_name}" via API (id: {lst["id"]})')
            return lst['id']

    raise RuntimeError(
        f'List "{list_name}" not found in Sublime Security. '
        f'Create it in the Sublime dashboard (Manage > Lists) or set {env_key} in .env.'
    )


def push_to_sublime(list_name: str, list_id: str, emails: list,
                    logger: logging.Logger) -> None:
    resp = requests.patch(
        f'{SUBLIME_BASE_URL}/v1/lists/{list_id}',
        json={'entries': emails},
        headers=_sublime_headers(),
        timeout=120,
    )
    resp.raise_for_status()
    logger.info(f'Pushed {len(emails):,} emails → "{list_name}"')


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    logger = setup_logging()
    logger.info('=' * 60)
    logger.info('Polaris → Sublime Security sync started')

    try:
        # Step 1 — Fetch CSVs from Gmail
        mail        = connect_gmail(logger)
        buckets     = {}   # list_name → set of emails
        all_msg_ids = []   # accumulate all report email IDs for cleanup

        for lst in LISTS:
            csv_text, msg_ids = fetch_csv_for_subject(mail, lst['subject'], logger)
            all_msg_ids.extend(msg_ids)
            if csv_text:
                buckets[lst['name']] = parse_emails(csv_text, logger)
                logger.info(f'  {lst["name"]}: {len(buckets[lst["name"]]):,} raw emails')
            else:
                buckets[lst['name']] = set()

        # Step 2 — Cross-list priority dedup: FULL > DIGITAL > LIMITED
        # A patron with multiple accounts may share one email across groups.
        # Each email must appear in exactly one list — the highest-priority match.
        full_set    = buckets['patron_emails_full']
        digital_set = buckets['patron_emails_digital']
        limited_set = buckets['patron_emails_limited']

        removed = len(digital_set & full_set) + len(limited_set & (full_set | digital_set))
        if removed:
            logger.info(
                f'Cross-list dedup: removed {removed} email(s) from lower-priority '
                f'list(s) — highest-priority group wins'
            )

        final = {
            'patron_emails_full':    sorted(full_set),
            'patron_emails_digital': sorted(digital_set - full_set),
            'patron_emails_limited': sorted(limited_set - full_set - digital_set),
        }

        # Step 3 — Push each list to Sublime Security
        for lst in LISTS:
            emails  = final[lst['name']]
            list_id = get_list_id(lst['name'], lst['list_id_key'], logger)
            push_to_sublime(lst['name'], list_id, emails, logger)

        # Step 4 — Delete processed emails from inbox
        cleanup_gmail(mail, all_msg_ids, logger)

        logger.info('Sync completed successfully')
        logger.info('=' * 60)

    except Exception as exc:
        logger.error(f'Sync FAILED: {exc}', exc_info=True)
        logger.info('=' * 60)
        sys.exit(1)


if __name__ == '__main__':
    main()
