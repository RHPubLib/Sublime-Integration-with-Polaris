# SSRS Setup

SQL Server Reporting Services (SSRS) is the bridge between your Polaris database
and the sync script. Because Clarivate-hosted Polaris runs in a fully isolated
network (no direct SQL access from outside), SSRS email subscriptions are the only
reliable automated path for extracting patron data. This approach also works fine
for self-hosted Polaris environments.

## How it fits in

```
Polaris SQL (w/ Polaris data source in SSRS)
  → SSRS report runs on nightly subscription
  → renders as CSV
  → delivered via SSRS email to your sync mailbox
  → polaris_to_sublime_sync.py reads it via IMAP
```

Three separate reports, three subscriptions, three CSVs — one per patron tier.

## Step 1: Discover your PatronCode IDs

Run `discover-patron-codes.sql` against your Polaris database. This shows every
active patron code at your library and how many patrons with email addresses use
each one. Use the results to decide which codes belong in each tier:

| Tier | Banner shown | What it means |
|------|-------------|---------------|
| Full | Verified Patron | Full library card — checkout, holds, rooms, events |
| Digital | E-Card / Digital Card | eContent access only |
| Limited | Restricted Card | Card type that limits holds, rooms, or events |

Note which codes represent staff-only accounts — those should **not** appear in
any of the three reports.

## Step 2: Create the SSRS reports

You need three reports, one per tier. In Report Builder (or SSRS web portal):

1. Create a new report against your **Polaris data source** (already configured
   in most Polaris SSRS environments — look for `PolarisNorthStar` or similar).
2. Add a dataset using the appropriate SQL from this folder:
   - `full-patrons.sql`
   - `digital-patrons.sql`
   - `limited-patrons.sql`
3. **Update the `PatronCodeID IN (...)` list** with your library's code IDs.
4. **Update the `NOT LIKE '%@rhpl.org'`** filter with your staff email domain.
5. Add a single table column: `EmailAddress`.
6. Save to your SSRS report server (e.g. under `Polaris/Custom/IT`).

## Step 3: Create SSRS subscriptions

For each report, create a **data-driven subscription** (or standard subscription):

| Setting | Value |
|---------|-------|
| Render format | **CSV (comma delimited)** |
| Delivery | Email |
| To | your sync mailbox (e.g. `sublime-sync@yourlibrary.org`) |
| Subject | Must match your `.env` exactly (see below) |
| Schedule | Nightly, before the sync script fires |

Default subject lines (match `.env.template`):

| Report | Subject |
|--------|---------|
| Full patrons | `Sublime Full Patron Export` |
| Digital patrons | `Sublime Digital Patron Export` |
| Limited patrons | `Sublime Limited Patron Export` |

You can change the subject lines — just update both the SSRS subscription and the
corresponding `SSRS_SUBJECT_*` variable in your `.env`.

## Step 4: Test

Trigger each subscription manually and confirm:
- The sync mailbox receives an email with a `.csv` attachment
- The CSV has a single column `EmailAddress` with one address per row
- Row count is reasonable for your patron population

Once all three CSVs arrive, run the sync script manually to verify end-to-end:

```bash
python3 polaris_to_sublime_sync.py
```

## Notes

- `RecordStatusID = 1` in all queries filters to **active** patron records only.
  Change or remove this if your library uses a different status convention.
- The `WITH (NOLOCK)` hint prevents the reports from blocking Polaris transactions.
  It is standard practice for Polaris read-only reporting.
- If a patron holds accounts under multiple card types (e.g., both a full card and
  an e-card), the sync script places their email in the highest-priority list only.
  The SQL does **not** need to handle this — deduplication happens in the script.
