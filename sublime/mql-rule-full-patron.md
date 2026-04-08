# Detection Rule: Full / Verified Patron

**Banner shown:**

![Verified Patron Banner](../images/banner-verified.png)

This rule fires when an inbound email arrives from a patron with a full-privilege
library card on file. Staff see a banner identifying the sender as a verified
cardholder.

---

## Sublime Dashboard Setup

**Location:** Detection Rules → Create Rule

| Field | Value |
|-------|-------|
| Name | `Known Library Patron — Full Card` (or your preferred name) |
| Severity | No severity / Informational |
| Status | Active |

### MQL Source

```
type.inbound
and sender.email.email in $patron_emails_full
```

> **Note:** The cross-list deduplication in the sync script guarantees a patron's
> email appears in only one list. The `not in` safety net in the lower-tier rules
> is the belt-and-suspenders approach — this rule for the top-priority tier
> does not need one.

### Warning Banner Action

After entering the MQL, add a **Warning Banner** action:

| Field | Value |
|-------|-------|
| Title | `Verified RHPL Library Patron` (replace RHPL with your library name) |
| Body | `This sender is a verified full-privilege library card holder.` |
| Severity / color | Use your preferred style — RHPL uses the default informational style |

---

## What this banner tells staff

A patron with a **full card** can:
- Check out physical items
- Place holds
- Book meeting rooms
- Register for programs and events

Staff receiving email from this sender can proceed with full-service transactions
without needing to look up the account in LEAP first.
