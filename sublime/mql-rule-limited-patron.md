# Detection Rule: Limited / Restricted Patron

**Banner shown:**

![Restricted Card Banner](../images/banner-restricted.png)

This rule fires when an inbound email arrives from a patron whose card type
restricts their borrowing or service privileges. Staff see a banner indicating
the sender is a known patron but has a limited account.

---

## Sublime Dashboard Setup

**Location:** Detection Rules → Create Rule

| Field | Value |
|-------|-------|
| Name | `Known Library Patron — Limited Card` (or your preferred name) |
| Severity | No severity / Informational |
| Status | Active |

### MQL Source

```
type.inbound
and sender.email.email in $patron_emails_limited
and not (sender.email.email in $patron_emails_full)
and not (sender.email.email in $patron_emails_digital)
```

Both `not in` conditions act as safety nets, enforcing the Full > Digital > Limited
priority hierarchy. The sync script already deduplicates before pushing, so these
guards are rarely triggered — but they guarantee the right banner shows if the
lists ever diverge.

### Warning Banner Action

After entering the MQL, add a **Warning Banner** action:

| Field | Value |
|-------|-------|
| Title | `RHPL Account — Restricted Card` (replace RHPL with your library name) |
| Body | `This patron has a limited card. They may not be able to place holds, book meeting rooms, or register for events. Verify in LEAP before processing requests.` |
| Severity / color | Use your preferred style |

---

## What this banner tells staff

A patron with a **limited/restricted card** may not be able to:
- Place holds on physical items
- Book meeting rooms
- Register for programs and events

The exact restrictions depend on the patron's specific card type in Polaris. The
banner is a prompt for staff to verify in LEAP before processing a service request
— not a definitive block.

Staff can look up the patron's record directly in LEAP to see their card type and
any associated restrictions before responding.
