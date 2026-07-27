# AI Zhihui Skill Restructure Execution Report

Date: 2026-07-27

## Execution Summary

The portable AI Zhihui package has been restructured into 3 scenario-based core skills.

Only the 3 final skills remain under `skills/`. Only v2 bundles remain under `bundles/`. Old prototype skill folders and old bundle files have been removed from the v2 package.

This execution did not modify the production AI Zhihui or OpenClaw runtime. All changes are contained inside `skill-export/`.

## What Changed

### Added Final Core Skills

| Skill | Purpose |
|---|---|
| `skills/zhihui-customer-intent-resolution/` | Resolve live customer-support intent, answer safely, troubleshoot, and decide human handoff. |
| `skills/zhihui-business-signal-extraction/` | Extract opportunity, pain, budget, timeline, decision-chain, product-feedback, risk, and next actions from customer communication. |
| `skills/zhihui-knowledge-capture-decision/` | Decide whether OCR, screenshots, FAQ drafts, and conversation summaries should become reusable knowledge. |

Each final skill now includes:

- `SKILL.md`
- `agents/openai.yaml`
- Trigger and non-trigger boundaries
- Required input/output structure
- Reference usage guidance
- Safety red lines

### Added Top-Level References

Reusable reference materials were organized into a shared reference taxonomy:

```text
references/
  product-features/
  faq/
  real-user-questions/
  risk-policy/
  troubleshooting/
  sales-playbook/
  prompt-examples/
  knowledge-capture/
```

### Added Routing and Acceptance Rules

Added `ROUTING_AND_ACCEPTANCE.md` to define:

- Which skill should be used for which scenario.
- How to handle mixed support/sales/knowledge-capture cases.
- Minimum sample-set requirements.
- Acceptance criteria and red-line failures.

### Added Validation Sample Sets

Added starter sample files:

```text
samples/customer-intent/sample-set.md
samples/business-signal/sample-set.md
samples/knowledge-capture/sample-set.md
```

These are templates. They need real business samples before final acceptance.

### Added v2 Bundles

Added:

```text
bundles/customer-service-v2.json
bundles/business-analysis-v2.json
bundles/knowledge-maintainer-v2.json
bundles/portable-full-v2.json
```

### Updated Manifest

Updated `manifest.json` to reflect:

- 3 final skills
- reference groups
- portable tools
- v2 bundles
- sample sets
- excluded sensitive assets

## What Was Not Changed

The following were not modified:

- Production AI Zhihui runtime files outside `skill-export/`
- Existing portable tool scripts
- Runtime cache and local environment files

## Non-Impact Guarantee

This execution is additive and export-package-only.

No existing feature should be affected because:

- No production directory was edited.
- Existing portable tool folder names remain unchanged.
- v2 bundles are the only active bundle files.
- References live in top-level `references/` folders.

## Remaining Work Before Final Acceptance

1. Fill the three sample sets with real customer, sales, and knowledge-capture cases.
2. Validate the three final skills against those samples.
3. Record pass/fail results and red-line failures.
4. Only after validation, update downstream agents to use the 3 final skills and v2 bundles.

## Acceptance Gate

Do not accept the package only because the folder structure exists.

Accept it only after:

- `zhihui-customer-intent-resolution` passes at least 20 real support samples.
- `zhihui-business-signal-extraction` passes at least 10 real customer/sales conversations.
- `zhihui-knowledge-capture-decision` passes at least 20 OCR, screenshot, FAQ draft, or conversation-summary samples.
- No red-line cases are answered with unauthorized promises or stored as reusable knowledge.

## Final Status

The v2 execution structure is in place.

The package is ready for sample-based validation and later agent integration.
