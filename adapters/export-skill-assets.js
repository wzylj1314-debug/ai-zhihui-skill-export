const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..", "..");
const exportRoot = path.join(root, "skill-export");
const skillsRoot = path.join(exportRoot, "skills");
const kbDir = path.join(root, "openclaw-local", "state", "workspace", "v1_0_3");
const workspaceDir = path.join(root, "openclaw-local", "state", "workspace");

const skillMeta = {
  "zhihui-product-router": {
    display: "AI Zhihui Feature Router",
    short: "Routes fashion-design requests to the right AI Zhihui feature.",
    prompt: "Route the user's AI Zhihui request to the best product feature and explain key distinctions.",
  },
  "zhihui-feature-playbooks": {
    display: "AI Zhihui Feature Playbooks",
    short: "Explains feature inputs, workflows, outputs, and known boundaries.",
    prompt: "Explain how to use an AI Zhihui feature based on its playbook and known limits.",
  },
  "zhihui-faq-answering": {
    display: "AI Zhihui FAQ Answering",
    short: "Answers common AI Zhihui support questions from FAQ assets.",
    prompt: "Answer the customer's AI Zhihui question using the FAQ and real user-question references.",
  },
  "zhihui-risk-handoff": {
    display: "AI Zhihui Risk Handoff",
    short: "Applies compliance boundaries and human handoff rules safely.",
    prompt: "Decide whether the AI Zhihui request is safe to answer or needs human handoff.",
  },
  "zhihui-prompt-coach": {
    display: "AI Zhihui Prompt Coach",
    short: "Coaches AI Remix prompt writing for local edits and retention.",
    prompt: "Rewrite AI Remix requests into stable prompts with retention and edit targets.",
  },
  "zhihui-troubleshooting": {
    display: "AI Zhihui Troubleshooting",
    short: "Troubleshoots failed, unstable, distorted, or unclear generations.",
    prompt: "Diagnose AI Zhihui generation issues and provide practical next steps before handoff.",
  },
  "zhihui-sales-assistant": {
    display: "AI Zhihui Sales Assistant",
    short: "Supports value explanation, sales talk tracks, packages, and comparisons.",
    prompt: "Answer sales or value questions about AI Zhihui without quoting final prices or promises.",
  },
  "zhihui-ops-tools": {
    display: "AI Zhihui Operations Tools",
    short: "Guides portable FAQ ingest, conversation analysis, and evaluation workflows.",
    prompt: "Use portable AI Zhihui operations workflows for FAQ maintenance and regression checks.",
  },
};

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function read(file) {
  return fs.readFileSync(file, "utf8").replace(/^\uFEFF/, "");
}

function write(file, text) {
  ensureDir(path.dirname(file));
  fs.writeFileSync(file, text.replace(/\r\n/g, "\n").trimEnd() + "\n", "utf8");
}

function copyKb(sourceName, targetFile) {
  write(targetFile, read(path.join(kbDir, sourceName)));
}

function stripFence(text) {
  return text.replace(/```/g, "~~~");
}

function skillMd(name, description, body) {
  return `---\nname: ${name}\ndescription: ${description}\n---\n\n${body}`;
}

function openaiYaml(name) {
  const meta = skillMeta[name];
  return `display_name: ${meta.display}\nshort_description: ${meta.short}\ndefault_prompt: ${JSON.stringify(meta.prompt)}\n`;
}

function parseFeatureSections() {
  const text = read(path.join(kbDir, "05_各功能详细说明.md"));
  const matches = [...text.matchAll(/^###\s+(F\d{2}|T\d{2})\s+(.+)$/gm)];
  const sections = [];
  for (let i = 0; i < matches.length; i += 1) {
    const start = matches[i].index;
    const end = i + 1 < matches.length ? matches[i + 1].index : text.length;
    sections.push({
      id: matches[i][1],
      name: matches[i][2].trim(),
      body: text.slice(start, end).trim(),
    });
  }
  return sections;
}

function slugFeature(id, name) {
  const map = {
    F01: "ai-remix",
    F02: "one-click-remix",
    F03: "style-fusion",
    F04: "similar-style",
    F05: "style-variants",
    F06: "text-to-style",
    F07: "sketch-to-style",
    F08: "style-to-sketch",
    F09: "virtual-tryon",
    F10: "video-tryon",
    F11: "reference-to-video",
    F12: "image-to-video",
    F13: "model-swap",
    F14: "background-swap",
    F15: "background-removal",
    F16: "object-removal",
    F17: "style-deconstruction",
    F18: "pattern-redraw",
    F19: "vectorize",
    F20: "image-to-prompt",
    F21: "text-to-pattern",
    F22: "similar-pattern",
    F23: "pattern-variants",
    F24: "pattern-fusion",
    F25: "pattern-recolor",
    F26: "style-recolor",
    F27: "pattern-on-garment",
    T01: "upscale",
  };
  return `${id}-${map[id] || name}`;
}

function writeSkill(name, description, body) {
  const dir = path.join(skillsRoot, name);
  ensureDir(path.join(dir, "references"));
  ensureDir(path.join(dir, "agents"));
  write(path.join(dir, "SKILL.md"), skillMd(name, description, body));
  write(path.join(dir, "agents", "openai.yaml"), openaiYaml(name));
}

function buildFunctionMap() {
  return {
    "AI改款": "F01",
    "改款": "F01",
    "局部改": "F01",
    "换衣服": "F01",
    "一键改款": "F02",
    "快速改款": "F02",
    "批量出款": "F02",
    "款式融合": "F03",
    "两款合并": "F03",
    "相似款衍生": "F04",
    "类似款": "F04",
    "系列款": "F04",
    "百变款式": "F05",
    "文生款": "F06",
    "文字生成款式": "F06",
    "线稿生款": "F07",
    "线稿上色": "F07",
    "款生线稿": "F08",
    "转线稿": "F08",
    "虚拟试衣": "F09",
    "上身效果": "F09",
    "试穿": "F09",
    "视频试衣": "F10",
    "动态试衣": "F10",
    "参考生视频": "F11",
    "图生视频": "F12",
    "AI换模特": "F13",
    "换模特": "F13",
    "AI换背景": "F14",
    "换背景": "F14",
    "AI褪底": "F15",
    "AI抠底": "F15",
    "褪底": "F15",
    "抠图": "F15",
    "去背景": "F15",
    "涂抹消除": "F16",
    "去杂物": "F16",
    "AI拆款": "F17",
    "拆款": "F17",
    "AI描稿": "F18",
    "描稿": "F18",
    "四方连续": "F18",
    "AI转矢量": "F19",
    "转矢量": "F19",
    "SVG": "F19",
    "EPS": "F19",
    "以图生文": "F20",
    "图片转提示词": "F20",
    "文生图": "F21",
    "文字生成图案": "F21",
    "相似图衍生": "F22",
    "百变花型": "F23",
    "图案融合": "F24",
    "图案配色": "F25",
    "花型改色": "F25",
    "款式配色": "F26",
    "服装配色": "F26",
    "花型上身": "F27",
    "图案上身": "F27",
    "高清放大": "T01",
    "放大": "T01",
    "清晰化": "T01",
  };
}

function main() {
  ensureDir(exportRoot);
  ensureDir(path.join(exportRoot, "bundles"));
  ensureDir(path.join(exportRoot, "adapters"));

  writeSkill(
    "zhihui-product-router",
    "Route AI Zhihui customer requests to the correct product feature and answer feature selection questions. Use when a user asks which AI Zhihui feature to use, describes fashion-design tasks such as garment remixing, virtual try-on, background removal, vectorization, pattern generation, recoloring, or asks about differences between features.",
    `# AI智绘功能路由\n\nUse this skill to identify the user's intent and recommend the correct AI智绘 feature.\n\n## Workflow\n\n1. Read \`references/function-catalog.md\` for the full feature list.\n2. Read \`references/function-router.md\` for routing rules and easy-confusion cases.\n3. Read \`references/synonyms.md\` when the user uses informal feature names or scenario language.\n4. Recommend the feature by standard feature name. In customer-facing answers, avoid exposing internal F-codes unless the user is internal or asks for them.\n5. If the request touches price, contracts, API/private deployment, copyright, legal promises, account permissions, or unknown capability, delegate to \`zhihui-risk-handoff\`.\n\n## Output\n\nKeep the answer concise: recommend the feature first, then give one reason and the next action. Do not invent features not present in the catalog.`
  );
  copyKb("03_功能编号总览.md", path.join(skillsRoot, "zhihui-product-router", "references", "function-catalog.md"));
  copyKb("04_功能选择指南.md", path.join(skillsRoot, "zhihui-product-router", "references", "function-router.md"));
  copyKb("18_同义词表与标签体系.md", path.join(skillsRoot, "zhihui-product-router", "references", "synonyms.md"));
  ensureDir(path.join(skillsRoot, "zhihui-product-router", "assets"));
  write(path.join(skillsRoot, "zhihui-product-router", "assets", "function-map.json"), JSON.stringify(buildFunctionMap(), null, 2));

  writeSkill(
    "zhihui-feature-playbooks",
    "Explain AI Zhihui feature usage, inputs, outputs, workflows, common issues, and boundaries. Use when a user asks how to use a specific AI Zhihui feature from F01-F27 or T01, asks what a feature can do, or needs operation steps and practical usage advice.",
    `# AI智绘功能手册\n\nUse this skill to answer detailed feature usage questions for AI智绘.\n\n## Workflow\n\n1. Identify the target feature with \`zhihui-product-router\` when needed.\n2. Read only the relevant file in \`references/features/\`.\n3. Read \`references/operation-index.md\` when the user asks for step-by-step operation.\n4. Answer with feature name, input requirements, main steps, output result, and one or two practical notes.\n5. For risk or promise boundaries, use \`zhihui-risk-handoff\`.\n\n## Constraints\n\nDo not describe non-existent controls, modes, upload rules, local file paths, or internal IDs. In customer-facing replies, keep the answer direct and avoid long tables.`
  );
  const featuresDir = path.join(skillsRoot, "zhihui-feature-playbooks", "references", "features");
  ensureDir(featuresDir);
  for (const section of parseFeatureSections()) {
    write(path.join(featuresDir, `${slugFeature(section.id, section.name)}.md`), section.body);
  }
  copyKb("06_操作流程说明.md", path.join(skillsRoot, "zhihui-feature-playbooks", "references", "operation-index.md"));

  writeSkill(
    "zhihui-faq-answering",
    "Answer AI Zhihui customer support questions using high-frequency FAQ and real user-question references. Use when a customer asks a known support question about AI Zhihui features, errors, usage, permissions, commercial boundaries, or common wording already captured in the FAQ assets.",
    `# AI智绘 FAQ 问答\n\nUse this skill to answer common customer questions with standard AI智绘 support wording.\n\n## Workflow\n\n1. Search \`references/faq.md\` first for a standard answer.\n2. Search \`references/user-questions.md\` when the user's wording is informal or scenario-based.\n3. If several answers match, prefer the one tied to the newest specific feature or risk boundary.\n4. If the answer involves forbidden promises or handoff conditions, use \`zhihui-risk-handoff\`.\n\n## Output\n\nGive the customer-facing answer only. Keep it short, actionable, and grounded in the references. Do not expose internal reasoning or claim certainty where the reference is conditional.`
  );
  copyKb("09_高频_FAQ.md", path.join(skillsRoot, "zhihui-faq-answering", "references", "faq.md"));
  copyKb("10_用户真实问法库.md", path.join(skillsRoot, "zhihui-faq-answering", "references", "user-questions.md"));

  writeSkill(
    "zhihui-risk-handoff",
    "Apply AI Zhihui answer boundaries, forbidden promises, compliance rules, and human handoff logic. Use when a request involves price, discount, contract, invoice, refund, account opening, API, private deployment, data security, NDA, copyright, commercial use, legal liability, unknown capabilities, customer complaints, repeated failures, or DingTalk customer-service handoff.",
    `# AI智绘风险与转人工\n\nUse this skill before making promises, quoting business terms, or escalating a support issue.\n\n## Workflow\n\n1. Read \`references/boundaries.md\` for what AI may answer and what it must not promise.\n2. Read \`references/handoff-general.md\` for generic escalation rules.\n3. Read \`references/handoff-dingtalk-overlay.md\` only when the target deployment is the current DingTalk customer-service group.\n4. For ordinary generation failures, first ask \`zhihui-troubleshooting\` to provide practical suggestions. Escalate only when the handoff conditions are met.\n\n## Output\n\nGive a safe conclusion first. If handoff is needed, explain the reason and collect the minimum useful information. Never give final prices, legal guarantees, copyright guarantees, account-specific permission claims, or unreleased roadmap promises.`
  );
  copyKb("16_AI回答边界与禁止承诺内容.md", path.join(skillsRoot, "zhihui-risk-handoff", "references", "boundaries.md"));
  copyKb("17_人工转接规则.md", path.join(skillsRoot, "zhihui-risk-handoff", "references", "handoff-general.md"));
  const agents = read(path.join(workspaceDir, "AGENTS.md"));
  const dingTalkOverlay = [
    "# DingTalk Handoff Overlay",
    "",
    "Use this overlay only for the current AI智绘 DingTalk customer-service group deployment.",
    "",
    "Do not load this overlay for generic website chat, sales assistant, documentation, or third-party Agent deployments.",
    "",
    "## Rules",
    "",
    "- In DingTalk group chat, answer the user's current question first, explain likely causes, and give executable suggestions.",
    "- Do not escalate just because the user says failure, abnormal, distorted, inaccurate, or similar words.",
    "- For price, package, quote, discount, contract, invoice, refund, or account opening, do not use the technical @ template. Say the issue needs sales confirmation and collect expected account count, use scenario, and whether contract/invoice is needed.",
    "- For non-price technical/generation abnormality, copyright risk, enterprise security, or unknown-knowledge cases that truly meet handoff conditions, append the exact template: `@韩骁俊 @许景然 @沈依天 @吴泽阳 麻烦看下`.",
    "- The exact template must include all four people: 韩骁俊, 许景然, 沈依天, 吴泽阳. Do not omit names, mention only part of them, or replace them with “等”.",
    "- For technical/generation abnormality, collect at least: feature used, failure time, original image or screenshot, prompt, and error message if available.",
  ].join("\n");
  write(path.join(skillsRoot, "zhihui-risk-handoff", "references", "handoff-dingtalk-overlay.md"), dingTalkOverlay);

  writeSkill(
    "zhihui-prompt-coach",
    "Coach AI Zhihui AI Remix prompt writing for local edits, retention, reference-image use, and effect tuning. Use when a user asks how to write prompts for AI改款, how to change only one part while preserving the rest, how to describe shape/color/material, or how to improve AI改款 results.",
    `# AI智绘提示词教练\n\nUse this skill only for AI改款 prompt coaching.\n\n## Workflow\n\n1. Read \`references/ai-remix-prompt-method.md\`.\n2. Diagnose what is missing: retained elements, edit target, shape/color/material details, main/reference image roles, or too many edits in one pass.\n3. Rewrite the user's own request using: \`保持[保留项]，把[修改对象]改为[目标效果]\`.\n4. Keep the tone gentle and practical.\n\n## Boundaries\n\nDo not use this skill for AI描稿, AI转矢量, AI褪底, 四方连续, or other features that do not need AI改款 prompt teaching.`
  );
  copyKb("07_AI改款提示词参考.md", path.join(skillsRoot, "zhihui-prompt-coach", "references", "ai-remix-prompt-method.md"));
  const promptExamples = parseFeatureSections().find((s) => s.id === "F01")?.body || "";
  write(path.join(skillsRoot, "zhihui-prompt-coach", "references", "prompt-examples.md"), promptExamples);

  writeSkill(
    "zhihui-troubleshooting",
    "Troubleshoot AI Zhihui generation failures and quality issues such as distortion, low clarity, bad try-on fit, background removal errors, vectorization failure, prompt not taking effect, and unstable details. Use when a user reports failed, abnormal, inaccurate, distorted, blurry, or unstable results.",
    `# AI智绘效果排查\n\nUse this skill to diagnose generation or quality issues before escalating.\n\n## Workflow\n\n1. Read \`references/troubleshooting-general.md\` for broad failure handling.\n2. Read \`references/troubleshooting-by-feature.md\` for feature-specific known issues.\n3. Provide likely cause, immediate retry advice, and what information to collect if escalation becomes necessary.\n4. Use \`zhihui-risk-handoff\` only after repeated failure, customer complaint, important delivery, suspected system issue, or account/backend uncertainty.\n\n## Output\n\nDo not escalate just because the user says failure, abnormal, distorted, or inaccurate. First give practical steps.`
  );
  copyKb("11_效果优化与失败排查.md", path.join(skillsRoot, "zhihui-troubleshooting", "references", "troubleshooting-general.md"));
  write(path.join(skillsRoot, "zhihui-troubleshooting", "references", "troubleshooting-by-feature.md"), [
    "# Feature-Specific Troubleshooting",
    "",
    read(path.join(kbDir, "09_高频_FAQ.md")),
    "",
    read(path.join(kbDir, "10_用户真实问法库.md")),
  ].join("\n"));

  writeSkill(
    "zhihui-sales-assistant",
    "Support AI Zhihui sales conversations, value explanation, customer pain-point mapping, package boundary discussion, and competitor comparison. Use when a user asks what AI Zhihui is, who it is for, how it differs from general image tools, how teams can use it, or asks package and purchasing questions that require safe sales handoff.",
    `# AI智绘销售辅助\n\nUse this skill for value explanation, customer scenario matching, package boundary discussion, and competitor comparison.\n\n## Workflow\n\n1. Read \`references/sales-playbook.md\` for talk tracks and pain points.\n2. Read \`references/value-comparison.md\` for competitor or generic tool comparison.\n3. Read \`references/package-boundaries.md\` before answering package, permissions, or purchase questions.\n4. For final price, discounts, contract, invoice, refund, account opening, API, or private deployment, use \`zhihui-risk-handoff\`.\n\n## Output\n\nExplain value by scenario. Do not quote final prices, fixed discounts, guaranteed results, or competitor attacks.`
  );
  copyKb("13_销售沟通话术.md", path.join(skillsRoot, "zhihui-sales-assistant", "references", "sales-playbook.md"));
  copyKb("14_竞品对比与价值解释.md", path.join(skillsRoot, "zhihui-sales-assistant", "references", "value-comparison.md"));
  copyKb("12_会员、套餐、权限说明.md", path.join(skillsRoot, "zhihui-sales-assistant", "references", "package-boundaries.md"));
  copyKb("08_场景化案例库.md", path.join(skillsRoot, "zhihui-sales-assistant", "references", "customer-scenarios.md"));

  writeSkill(
    "zhihui-ops-tools",
    "Guide portable AI Zhihui operations workflows for FAQ screenshot ingest, sensitive-content scanning, review-and-commit gates, conversation analysis, and regression evaluation. Use when maintaining AI Zhihui knowledge assets, turning chat screenshots into FAQ drafts, analyzing customer conversations, or validating answer quality in an isolated export environment.",
    `# AI智绘运营工具\n\nUse this skill for portable maintenance workflows. It does not modify the production OpenClaw workspace unless the operator explicitly points environment variables at that workspace.\n\n## Safety Rule\n\nDefault to isolated paths under the export workspace. Never copy secrets, screenshots, OCR cache, draft ledgers, conversation databases, sessions, credentials, or evaluation responses into a transferable package.\n\n## References\n\n- \`references/faq-ingest-sop.md\`: Screenshot-to-FAQ workflow and commit gates.\n- \`references/conversation-analysis-sop.md\`: Conversation analysis workflow and required environment variables.\n- \`references/eval-sop.md\`: Regression workflow and coverage expectations.\n- \`references/env-vars.md\`: Portable environment variable contract.\n\n## Tooling Boundary\n\nScripts in this skill are placeholders and adapters. The current production scripts remain under \`openclaw-local/\` and are not changed by this export.`
  );
  write(path.join(skillsRoot, "zhihui-ops-tools", "references", "faq-ingest-sop.md"), read(path.join(root, "openclaw-local", "scripts", "faq-ingest", "README.md")));
  write(path.join(skillsRoot, "zhihui-ops-tools", "references", "conversation-analysis-sop.md"), read(path.join(root, "openclaw-local", "scripts", "conversation-analysis", "README.md")));
  write(path.join(skillsRoot, "zhihui-ops-tools", "references", "eval-sop.md"), read(path.join(root, "MAINTENANCE_GUIDE.md")).match(/## 5[\s\S]*?(?=## 6\.)/)?.[0] || "Run quick and agent regression after knowledge changes.");
  write(path.join(skillsRoot, "zhihui-ops-tools", "references", "env-vars.md"), `# Portable Environment Variables\n\nUse these variables when adapting production tools into a transferable Skill environment.\n\n- ZHIHUI_KB_DIR: Path to the target knowledge base directory.\n- ZHIHUI_INBOX_DIR: Path to screenshot, OCR cache, and FAQ draft workspace.\n- ZHIHUI_OUTPUT_DIR: Path for generated reports and exported artifacts.\n- ZHIHUI_EVAL_DIR: Path to evaluation test cases and reports.\n- ZHIHUI_AGENT_BASE_URL: Optional OpenAI-compatible endpoint for target Agent evaluation.\n- ZHIHUI_AGENT_TOKEN: Optional bearer token for the evaluation endpoint.\n- OPENAI_API_KEY: Required only for conversation analysis or LLM-assisted extraction.\n- OPENAI_BASE_URL: Optional OpenAI-compatible API base URL.\n- OPENAI_MODEL: Optional model name.\n\nDo not include .env files or real secrets in a transferable package.`);
  ensureDir(path.join(skillsRoot, "zhihui-ops-tools", "assets"));
  write(path.join(skillsRoot, "zhihui-ops-tools", "assets", "function-map.json"), JSON.stringify(buildFunctionMap(), null, 2));
  write(path.join(skillsRoot, "zhihui-ops-tools", "scripts", "README.md"), `# Scripts Placeholder\n\nDo not run production OpenClaw scripts from this transferable package by default.\n\nWhen tool migration is needed, copy scripts into this folder and adapt paths to the environment variables listed in ../references/env-vars.md.`);

  const bundles = {
    "customer-service": [
      "zhihui-product-router",
      "zhihui-feature-playbooks",
      "zhihui-faq-answering",
      "zhihui-troubleshooting",
      "zhihui-risk-handoff",
    ],
    "sales-assistant": [
      "zhihui-product-router",
      "zhihui-sales-assistant",
      "zhihui-risk-handoff",
    ],
    "prompt-coach": [
      "zhihui-product-router",
      "zhihui-feature-playbooks",
      "zhihui-prompt-coach",
      "zhihui-troubleshooting",
    ],
    "knowledge-maintainer": [
      "zhihui-faq-answering",
      "zhihui-risk-handoff",
      "zhihui-ops-tools",
    ],
  };
  for (const [name, skills] of Object.entries(bundles)) {
    write(path.join(exportRoot, "bundles", `${name}.json`), JSON.stringify({ name, skills }, null, 2));
  }

  write(path.join(exportRoot, "manifest.json"), JSON.stringify({
    name: "ai-zhihui-skill-export",
    version: "1.0.0-draft",
    source: "AI智绘客服机器人",
    source_mode: "read-only export; existing OpenClaw runtime files are not modified",
    generated_at: new Date().toISOString(),
    skills: Object.keys(skillMeta),
    bundles: Object.keys(bundles),
    excluded_sensitive_assets: [
      ".env",
      "tokens",
      "webhooks",
      "customer screenshots",
      "OCR cache",
      "FAQ drafts",
      "conversation analysis databases",
      "sessions",
      "credentials",
      "evaluation responses",
    ],
  }, null, 2));

  write(path.join(exportRoot, "TRANSFER_CHECKLIST.md"), `# Transfer Checklist\n\n- [ ] Copy only skill-export/skills and selected bundle files.\n- [ ] Do not copy .env, tokens, webhooks, screenshots, caches, draft ledgers, sessions, credentials, logs, or databases.\n- [ ] Install only the bundles needed by the target Agent.\n- [ ] Use zhihui-risk-handoff in every customer-facing bundle.\n- [ ] Enable handoff-dingtalk-overlay.md only for the current DingTalk customer-service deployment.\n- [ ] Configure environment variables before adapting any ops scripts.\n- [ ] Run regression tests after changing references.\n`);

  console.log(`Exported ${Object.keys(skillMeta).length} skills to ${skillsRoot}`);
}

main();
