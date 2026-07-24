# Legacy Skill Restructure Map

The original 8 skills are retained under `legacy-skills/` as legacy prototypes for traceability. They are not active skills and are not the final acceptance boundary.

| Legacy skill | Final handling | Reason |
|---|---|---|
| `zhihui-product-router` | Merge into `zhihui-customer-intent-resolution` | Feature routing is one step inside customer-service intent resolution. |
| `zhihui-feature-playbooks` | Move knowledge into `references/product-features/` | Feature manuals are reference knowledge, not a standalone judgment workflow. |
| `zhihui-faq-answering` | Merge into `zhihui-customer-intent-resolution` | FAQ answering is one branch of customer-service resolution. |
| `zhihui-risk-handoff` | Move policy into `references/risk-policy/` | Risk rules are shared policy used by all final skills. |
| `zhihui-prompt-coach` | Move examples into `references/prompt-examples/` | Prompt coaching is useful reference, but not yet proven as an independent high-frequency skill. |
| `zhihui-troubleshooting` | Merge into `zhihui-customer-intent-resolution` | Troubleshooting is a support branch triggered by customer failure reports. |
| `zhihui-sales-assistant` | Merge judgment into `zhihui-business-signal-extraction`; keep wording as `references/sales-playbook/` | Sales value comes from identifying signals and next actions, while scripts are reference. |
| `zhihui-ops-tools` | Split deterministic tools into `tools-portable/`; merge knowledge decisions into `zhihui-knowledge-capture-decision` | Tool launch is not a skill; knowledge intake judgment is. |

## Migration Principle

Do not delete legacy folders until the three final skills pass sample-set validation. Agents should load active skills from `skills/`, where only the final three skills should remain.
