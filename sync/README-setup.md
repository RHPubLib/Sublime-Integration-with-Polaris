# Sync Script Setup

## 1. Deploy the script

Copy the contents of this `sync/` directory to your Linux server. A suggested path:

```bash
sudo mkdir -p /opt/sublime-sync
sudo cp polaris_to_sublime_sync.py requirements.txt .env.template .gitignore /opt/sublime-sync/
sudo chown -R youruser:youruser /opt/sublime-sync
```

Replace `youruser` with the account that will run the sync.

## 2. Install Python dependencies

```bash
cd /opt/sublime-sync
pip3 install -r requirements.txt
```

Or in a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

If using a venv, update the `ExecStart` path in the systemd service file to use
`/opt/sublime-sync/venv/bin/python3` instead of `/usr/bin/python3`.

## 3. Configure credentials

```bash
cp .env.template .env
nano .env   # or your preferred editor
```

Fill in all required values:

| Variable | Where to get it |
|----------|----------------|
| `GMAIL_ADDRESS` | The sync mailbox you created in Google Workspace Admin |
| `GMAIL_APP_PASSWORD` | Sign into the sync account → myaccount.google.com/apppasswords |
| `SUBLIME_API_KEY` | Sublime dashboard → Automate > API → Create key |
| `SUBLIME_BASE_URL` | Shown next to your API key in the Sublime dashboard |
| `STAFF_EMAIL_DOMAIN` | Your library's staff email domain (e.g. `yourlibrary.org`) |

Leave the `SSRS_SUBJECT_*` and `SUBLIME_LIST_ID_*` values at their defaults
unless you changed the subscription subject lines in SSRS.

## 4. Set up the Gmail sync mailbox

In Google Workspace Admin:

1. Create a dedicated service account (e.g. `sublime-sync@yourlibrary.org`).
   Place it in an org unit with appropriate policies — it only needs Gmail access.
2. Sign into the account and enable **2-Step Verification**
   (required for App Passwords).
3. Go to `myaccount.google.com/apppasswords`, create a new App Password, and
   paste it into `.env` as `GMAIL_APP_PASSWORD`.
4. Enable IMAP in Gmail settings for this account:
   Gmail Settings → See all settings → Forwarding and POP/IMAP → Enable IMAP.

## 5. Test manually

Before scheduling, trigger the SSRS subscriptions manually and wait for the
three CSVs to arrive in the sync mailbox, then run:

```bash
python3 /opt/sublime-sync/polaris_to_sublime_sync.py
```

Expected output:

```
INFO Connecting to Gmail as sublime-sync@yourlibrary.org...
INFO Subject "Sublime Full Patron Export": found 1 email(s) — using most recent
INFO   patron_emails_full: 48,000 raw emails
INFO Subject "Sublime Digital Patron Export": found 1 email(s) — using most recent
INFO   patron_emails_digital: 4,200 raw emails
INFO Subject "Sublime Limited Patron Export": found 1 email(s) — using most recent
INFO   patron_emails_limited: 7,100 raw emails
INFO Pushed 48,000 emails → "patron_emails_full"
INFO Pushed 4,200 emails → "patron_emails_digital"
INFO Pushed 7,100 emails → "patron_emails_limited"
INFO Deleted 3 processed report email(s) from inbox
INFO Sync completed successfully
```

Row counts will vary by library. As long as the three lists populate in the
Sublime dashboard (Manage > Lists), the integration is working.

## 6. Schedule

See [../systemd/README.md](../systemd/README.md) for the systemd timer setup.
