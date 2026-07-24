# AI Zhihui Reference Index

This folder contains reusable knowledge for the three final AI Zhihui skills.

References are not skills. They provide evidence, wording, rules, and product facts that skills load only when needed.

| Folder | Purpose | Used by |
|---|---|---|
| `product-features/` | F01-F27/T01 feature facts, routing, synonyms, and operation guidance | Customer intent, business signal, knowledge capture |
| `faq/` | High-frequency standard answers | Customer intent, knowledge capture |
| `real-user-questions/` | Real customer wording and intent examples | Customer intent, knowledge capture |
| `risk-policy/` | Price, contract, copyright, refund, API, privacy, complaint, and handoff boundaries | All three skills |
| `troubleshooting/` | Failure symptoms, causes, retry paths, and escalation rules | Customer intent, knowledge capture |
| `sales-playbook/` | Value statements, customer scenarios, package boundaries, and sales wording | Business signal |
| `prompt-examples/` | AI Remix prompt methods and examples | Customer intent, future creative guidance |
| `knowledge-capture/` | Knowledge intake rules, dedupe criteria, and review gates | Knowledge capture |

## Usage Rule

Keep `SKILL.md` concise. Load reference files only after a skill triggers and only for the active task.
