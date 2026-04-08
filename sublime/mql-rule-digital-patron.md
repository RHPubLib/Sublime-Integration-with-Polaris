# Detection Rule: Digital / E-Card Patron

**Banner shown:**

![E-Card Banner](../images/banner-ecard.png)

This rule fires when an inbound email arrives from a patron whose account is
restricted to digital/eContent access only. Staff see a banner that signals the
sender is a known patron but cannot use physical services.

---

## Sublime Dashboard Setup

**Location:** Detection Rules → Create Rule

| Field | Value |
|-------|-------|
| Name | `Known Library Patron — Digital Card` (or your preferred name) |
| Severity | No severity / Informational |
| Status | Active |

### MQL Source

```
type.inbound
and sender.email.email in $patron_emails_digital
and not (sender.email.email in $patron_emails_full)
```

The `not in $patron_emails_full` condition is a safety net. The sync script
already deduplicates at push time, so a patron whose email appears in
`patron_emails_full` will never be in `patron_emails_digital`. This guard ensures
the correct banner shows even if the lists ever fall out of sync.

### Warning Banner Action

After entering the MQL, add a **Warning Banner** action:

| Field | Value |
|-------|-------|
| Title | `RHPL E-Card / Digital Card` (replace RHPL with your library name) |
| Body | `This patron has eContent access only. Physical checkout, holds, room booking, and event registration are not available on this card.` |
| Severity / color | Use your preferred style |

---

## What this banner tells staff

A patron with a **digital/e-card** can:
- Access eBooks, eAudiobooks, and other digital resources

A patron with a **digital/e-card** cannot:
- Check out physical items
- Place holds on physical materials
- Book meeting rooms
- Register for programs and events

Staff receiving a room booking or holds request from this sender can quickly
identify that it falls outside their card privileges without opening LEAP.
