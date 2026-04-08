# Sublime Security Setup

This section covers everything you configure inside the Sublime Security dashboard:
three custom lists, three detection rules, and two automations.

## Overview

```
Sublime Lists (3)
  patron_emails_full      ← fed nightly by the sync script
  patron_emails_digital
  patron_emails_limited

Detection Rules (3)
  Full Card rule    → reads patron_emails_full    → shows Verified Patron banner
  Digital Card rule → reads patron_emails_digital → shows E-Card banner
  Limited Card rule → reads patron_emails_limited → shows Restricted Card banner

Automations (2)
  Known Patron — Auto-Review Benign        ← prevents patron mail from being quarantined
  Custom: Remediate malicious flagged messages  ← replaces the built-in core automation
```

---

## Step 1: Create the three lists

**Location:** Manage > Lists > Create List

Create each list with these settings:

| List name | Entry type | Editable |
|-----------|-----------|---------|
| `patron_emails_full` | String | Yes |
| `patron_emails_digital` | String | Yes |
| `patron_emails_limited` | String | Yes |

The names must match the values in your `.env` file (which default to the names
above). The lists start empty — the sync script populates them on first run.

> **API note:** Sublime Security uses regional subdomains. When you create your
> API key under Automate > API, the dashboard shows your base URL (e.g.
> `https://na-east-3.platform.sublime.security`). Use that URL as `SUBLIME_BASE_URL`
> in your `.env` — the generic `platform.sublime.security` URL will return 401.

---

## Step 2: Create the three detection rules

Create each rule in order. See the individual rule files for full MQL and banner
configuration:

1. [Full / Verified Patron rule](mql-rule-full-patron.md)
2. [Digital / E-Card rule](mql-rule-digital-patron.md)
3. [Limited / Restricted rule](mql-rule-limited-patron.md)

Each rule:
- Uses `type.inbound` to scope to incoming mail only
- Checks `sender.email.email in $<list_name>`
- Adds a **Warning Banner** action (title + body text describing the patron tier)
- Has No Severity / Informational severity (these are informational, not threats)

---

## Step 3: Configure the automations

The automations ensure patron mail is never auto-quarantined and that non-patron
malicious mail is still handled correctly.

1. [Auto-Review Patron Emails as Benign](automation-patron-benign.md)
2. [Remediate Malicious Non-Patron Mail](automation-malicious-nonpatron.md)
   — includes the step to **disable the core automation** first

Complete both automations before going live. Running only Step 1 without
disabling the core automation can cause conflicts.

---

## Step 4: Test

1. Run the sync script manually to populate all three lists.
2. Send a test email to a staff Gmail account from an address you know is in
   `patron_emails_full`. The Verified Patron banner should appear within a few
   minutes (Sublime re-evaluates as mail arrives).
3. Repeat for a digital-card and limited-card patron email if you have test
   addresses available.
4. Confirm no patron email is being quarantined by checking Sublime's mail log.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| No banner on patron mail | Lists are empty or rule is inactive | Run sync script; confirm rule is Active |
| `401` on API calls | Wrong base URL or expired API key | Check `SUBLIME_BASE_URL` in `.env`; regenerate key |
| `List "..." not found` | List name mismatch | List name in `.env` must match the Sublime dashboard exactly |
| Multiple banners on one email | Lists overlap | Re-run sync (dedup enforced); check MQL `not in` guards |
| Patron mail quarantined | Core automation still active | Disable core "Remediate malicious" automation; create the custom replacement |
| ML verdict shows "Suspicious" | Expected — Sublime's ML label is separate from classification | The Benign classification prevents quarantine; the ML label is informational |
