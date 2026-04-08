# Automation: Auto-Review Patron Emails as Benign

This automation prevents patron emails from being auto-quarantined by Sublime's
malicious mail remediation. Without it, a patron email that scores as "Suspicious"
in Sublime's ML model could be quarantined before staff see it.

---

## Why this is needed

Sublime Security's core "Remediate malicious flagged messages" automation
quarantines mail that the ML scores as malicious. Patron emails sometimes
generate false positives (e.g., a patron email with a link to a local business
may trigger signals). This automation marks all patron emails as **Benign**,
which prevents auto-quarantine while still allowing staff to see any ML signals
in the Sublime dashboard.

> **Important:** This is a calculated tradeoff. A compromised patron account
> sending phishing will also be marked Benign. See the root README for notes on
> mitigating this with Sublime's NLU and link-analysis enrichment functions.

---

## Sublime Dashboard Setup

**Location:** Automations → Create Automation

| Field | Value |
|-------|-------|
| Name | `Known Patron — Auto-Review Benign` |
| Trigger | Detection Rule Matched |
| Status | Active |

### MQL Source

```
type.inbound
and any(triage.flagged_rules, .name == "Known Library Patron — Full Card")
   or any(triage.flagged_rules, .name == "Known Library Patron — Digital Card")
   or any(triage.flagged_rules, .name == "Known Library Patron — Limited Card")
```

Replace the rule names in quotes with whatever you named your three detection
rules in the dashboard.

### Action

| Setting | Value |
|---------|-------|
| Action type | Auto-review |
| Classification | **Benign** |

> Note: "Benign" is only available as a classification in **Automations**, not
> in Detection Rules. This is intentional per Sublime Security's design.
