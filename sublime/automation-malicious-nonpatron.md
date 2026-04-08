# Automation: Remediate Malicious Non-Patron Mail

This automation replaces Sublime Security's built-in "Remediate malicious flagged
messages" core automation with a custom version that **excludes patron senders**.

---

## Why replace the core automation?

Sublime's built-in core automation quarantines mail that the ML scores as
malicious. Once you deploy the patron Benign automation, you need to disable the
core automation and replace it with a custom version — otherwise the core
automation and the patron Benign automation will conflict (core tries to quarantine
what the patron rule just marked Benign).

This approach was confirmed as the recommended architecture by Sublime Security's
Customer Success Engineering team.

---

## Step 1: Disable the core automation

**Location:** Automations → find "Remediate malicious flagged messages" (authored
by Sublime Security) → toggle **Inactive**.

Core automations are read-only (cannot be edited) but can be toggled on/off.

---

## Step 2: Create the replacement automation

**Location:** Automations → Create Automation

| Field | Value |
|-------|-------|
| Name | `Custom: Remediate malicious flagged messages` |
| Trigger | Detection Rule Matched |
| Status | Active |

### MQL Source

```
type.inbound
and not (
  any(triage.flagged_rules, .name == "Known Library Patron — Full Card")
  or any(triage.flagged_rules, .name == "Known Library Patron — Digital Card")
  or any(triage.flagged_rules, .name == "Known Library Patron — Limited Card")
)
and ml.attack_score().verdict == "malicious"
```

Replace the rule names in quotes with whatever you named your three detection
rules in the dashboard.

### Action

| Setting | Value |
|---------|-------|
| Action type | Auto-review |
| Classification | **Malicious** |

---

## Result

- Patron mail → always marked Benign, never quarantined
- Non-patron mail scored malicious by ML → quarantined as before
- No functional change to security posture for non-patron senders
