const state = {
  current: null,
  currentSummary: null,
  activeTab: "business",
};

const fieldLabels = {
  business_opportunity: "业务机会",
  customer_core_scene: "客户核心场景",
  customer_real_need: "客户真实需求",
  current_workflow: "客户当前工作方式",
  customer_role: "客户角色",
  personal_intent: "客户个人意向",
  product_fit: "产品适配",
  clear_commitment: "客户明确承诺",
  sales_stage: "当前销售阶段",
  lead_level: "线索等级",
  next_action: "下一步动作",
  confidence: "分析可信度",
  effectiveness: "销售是否有效推动",
  biggest_loss: "最关键失分点",
  stage_changed: "本通电话是否发生阶段跃迁",
  stage_change_evidence: "跃迁证据",
  industry: "客户所属行业/品类",
  business_task: "客户需要完成的业务任务",
  operator: "当前由谁完成",
  current_tools: "当前使用的工具或方式",
  current_time_cost: "当前耗时",
  current_money_cost: "当前成本",
  current_problem: "当前结果存在的问题",
  ai_entry_point: "AI智绘可能进入的环节",
  function_fit: "功能适配",
  function_fit_basis: "功能适配依据",
  effect_fit: "效果适配",
  effect_fit_basis: "效果适配依据",
  workflow_fit: "流程适配",
  workflow_fit_basis: "流程适配依据",
  commercial_fit: "商业适配",
  commercial_fit_basis: "商业适配依据",
  overall_fit: "综合适配",
  verification_method: "建议验证方式",
  category: "反馈分类",
  customer_quote: "客户原话",
  affects_purchase_or_usage: "是否影响购买或使用",
  common_need: "是否可能为共性需求",
  evidence_level: "当前证据充分度",
  suggested_handling: "建议处理方式",
  reason: "判断理由",
  needed: "是否需要测试",
  test_goal: "测试目标",
  required_materials: "客户需提供的素材",
  test_features: "测试功能",
  impact_on_next_judgement: "测试结果如何影响后续判断",
};

const schemas = {
  business: [
    {
      title: "1. 项目结论",
      path: "project_conclusion",
      fields: [
        "business_opportunity",
        "customer_core_scene",
        "customer_real_need",
        "current_workflow",
        "customer_role",
        "personal_intent",
        "product_fit",
        "clear_commitment",
        { key: "key_blockers", type: "array", label: "当前关键阻断", max: 3 },
        "sales_stage",
        "lead_level",
        "next_action",
        "confidence",
      ],
    },
    { title: "2. 关键证据", path: "key_evidence", type: "evidence" },
    {
      title: "3. 销售推进判断",
      path: "sales_judgement",
      fields: [
        "effectiveness",
        { key: "right_actions", type: "array", label: "做对的关键动作", max: 5 },
        "biggest_loss",
        "stage_changed",
        "stage_change_evidence",
        { key: "risk_responses", type: "risk", label: "功能错配/错误表达/过度承诺", max: 3 },
      ],
    },
    { title: "4. 下一步必须验证", path: "must_verify_next", type: "verify" },
  ],
  product: [
    {
      title: "1. 用户场景与当前工作流",
      path: "user_scene_workflow",
      fields: [
        "industry",
        "business_task",
        "operator",
        "current_tools",
        "current_time_cost",
        "current_money_cost",
        "current_problem",
        "ai_entry_point",
      ],
    },
    {
      title: "2. 产品适配判断",
      path: "fit_judgement",
      fields: [
        "function_fit",
        "function_fit_basis",
        "effect_fit",
        "effect_fit_basis",
        "workflow_fit",
        "workflow_fit_basis",
        "commercial_fit",
        "commercial_fit_basis",
        "overall_fit",
        { key: "main_risks", type: "array", label: "主要风险", max: 5 },
        "verification_method",
      ],
    },
    {
      title: "3. 产品反馈判断",
      path: "feedback_judgement",
      fields: [
        "category",
        "customer_quote",
        "affects_purchase_or_usage",
        "common_need",
        "evidence_level",
        "suggested_handling",
        "reason",
      ],
    },
    {
      title: "4. 产品测试建议",
      path: "test_suggestion",
      fields: [
        { key: "needed", type: "boolean", label: "是否需要测试" },
        "test_goal",
        "required_materials",
        "test_features",
        { key: "success_criteria", type: "array", label: "关键成功标准", max: 6 },
        { key: "focus_points", type: "array", label: "需要重点观察的问题", max: 6 },
        "impact_on_next_judgement",
      ],
    },
  ],
};

document.addEventListener("DOMContentLoaded", () => {
  bindEvents();
  loadConfig();
  loadHistory();
});

function bindEvents() {
  document.querySelectorAll(".nav-item").forEach((button) => {
    button.addEventListener("click", () => showView(button.dataset.view));
  });
  document.querySelectorAll(".tab").forEach((button) => {
    button.addEventListener("click", () => showTab(button.dataset.tab));
  });
  document.querySelectorAll(".summary-tab").forEach((button) => {
    button.addEventListener("click", () => showSummaryTab(button.dataset.summaryTab));
  });
  document.querySelectorAll(".prompt-tab").forEach((button) => {
    button.addEventListener("click", () => showPromptTab(button.dataset.promptTab));
  });
  document.getElementById("analyzeBtn").addEventListener("click", createAnalysis);
  document.getElementById("analyzeFilesBtn").addEventListener("click", analyzeFiles);
  document.getElementById("saveBtn").addEventListener("click", saveAnalysis);
  document.getElementById("refreshMetaBtn").addEventListener("click", refreshMeta);
  document.getElementById("sendBusinessBtn").addEventListener("click", () => sendAnalysis("business"));
  document.getElementById("sendProductBtn").addEventListener("click", () => sendAnalysis("product"));
  document.getElementById("refreshHistoryBtn").addEventListener("click", loadHistory);
  document.getElementById("filterHistoryBtn").addEventListener("click", loadHistory);
  document.getElementById("clearHistoryFilterBtn").addEventListener("click", clearHistoryFilter);
  document.getElementById("deleteSelectedHistoryBtn").addEventListener("click", deleteSelectedHistory);
  document.getElementById("selectAllHistory").addEventListener("change", toggleAllHistoryRows);
  document.getElementById("loadSummaryBtn").addEventListener("click", loadDailySummary);
  document.getElementById("generateSummaryBtn").addEventListener("click", generateDailySummary);
  document.getElementById("saveSummaryBtn").addEventListener("click", saveDailySummary);
  document.getElementById("sendSummaryBusinessBtn").addEventListener("click", () => sendDailySummary("business"));
  document.getElementById("sendSummaryProductBtn").addEventListener("click", () => sendDailySummary("product"));
  document.getElementById("savePromptBtn").addEventListener("click", savePrompt);
  document.getElementById("resetPromptBtn").addEventListener("click", resetPrompt);
  document.getElementById("saveSummaryPromptBtn").addEventListener("click", saveSummaryPrompt);
  document.getElementById("resetSummaryPromptBtn").addEventListener("click", resetSummaryPrompt);
  document.getElementById("summaryDate").value = todayDate();
}

async function loadConfig() {
  const data = await api("/api/config");
  const rows = [
    `GPT：${data.has_openai_key ? "已配置" : "未配置 OPENAI_API_KEY"}`,
    `接口：${data.base_url}`,
    `模式：${data.endpoint_mode}`,
    `模型：${data.model}`,
    `业务群：${data.has_business_channel ? "已配置" : "未配置"}`,
    `产品群：${data.has_product_channel ? "已配置" : "未配置"}`,
  ];
  document.getElementById("configState").innerHTML = rows.map((item) => `<div>${escapeHtml(item)}</div>`).join("");
}

function showView(name) {
  document.querySelectorAll(".nav-item").forEach((item) => item.classList.toggle("active", item.dataset.view === name));
  document.getElementById("createView").classList.toggle("hidden", name !== "create");
  document.getElementById("historyView").classList.toggle("hidden", name !== "history");
  document.getElementById("summaryView").classList.toggle("hidden", name !== "summary");
  document.getElementById("resultView").classList.toggle("hidden", name !== "result");
  document.getElementById("promptView").classList.toggle("hidden", name !== "prompt");
  if (name === "history") loadHistory();
  if (name === "summary") loadDailySummary();
  if (name === "prompt") loadPrompt();
}

function showPromptTab(name) {
  document.querySelectorAll(".prompt-tab").forEach((button) => {
    button.classList.toggle("active", button.dataset.promptTab === name);
  });
  document.getElementById("singlePromptPanel").classList.toggle("hidden", name !== "single");
  document.getElementById("summaryPromptPanel").classList.toggle("hidden", name !== "summary");
}

async function loadPrompt() {
  setMessage("promptMessage", "正在加载提示词。");
  try {
    const [data, summaryData] = await Promise.all([api("/api/prompt"), api("/api/summary-prompt")]);
    document.getElementById("promptText").value = data.prompt || "";
    document.getElementById("summaryPromptText").value = summaryData.prompt || "";
    setMessage("promptMessage", "");
  } catch (error) {
    setMessage("promptMessage", error.message);
  }
}

async function savePrompt() {
  const button = document.getElementById("savePromptBtn");
  const prompt = document.getElementById("promptText").value.trim();
  button.disabled = true;
  setMessage("promptMessage", "正在保存提示词。");
  try {
    const data = await api("/api/prompt", { method: "PUT", body: { prompt } });
    document.getElementById("promptText").value = data.prompt || "";
    setMessage("promptMessage", "已保存。下一次新建分析会使用这版提示词。");
  } catch (error) {
    setMessage("promptMessage", error.message);
  } finally {
    button.disabled = false;
  }
}

async function saveSummaryPrompt() {
  const button = document.getElementById("saveSummaryPromptBtn");
  const prompt = document.getElementById("summaryPromptText").value.trim();
  button.disabled = true;
  setMessage("promptMessage", "正在保存汇总提示词。");
  try {
    const data = await api("/api/summary-prompt", { method: "PUT", body: { prompt } });
    document.getElementById("summaryPromptText").value = data.prompt || "";
    setMessage("promptMessage", "已保存。下一次生成汇总会使用这版提示词。");
  } catch (error) {
    setMessage("promptMessage", error.message);
  } finally {
    button.disabled = false;
  }
}

async function resetPrompt() {
  const button = document.getElementById("resetPromptBtn");
  button.disabled = true;
  setMessage("promptMessage", "正在恢复默认提示词。");
  try {
    const data = await api("/api/prompt/reset", { method: "POST" });
    document.getElementById("promptText").value = data.prompt || "";
    setMessage("promptMessage", "已恢复默认提示词。");
  } catch (error) {
    setMessage("promptMessage", error.message);
  } finally {
    button.disabled = false;
  }
}

async function resetSummaryPrompt() {
  const button = document.getElementById("resetSummaryPromptBtn");
  button.disabled = true;
  setMessage("promptMessage", "正在恢复默认汇总提示词。");
  try {
    const data = await api("/api/summary-prompt/reset", { method: "POST" });
    document.getElementById("summaryPromptText").value = data.prompt || "";
    setMessage("promptMessage", "已恢复默认汇总提示词。");
  } catch (error) {
    setMessage("promptMessage", error.message);
  } finally {
    button.disabled = false;
  }
}

function showTab(name) {
  if (!name) return;
  state.activeTab = name;
  document.querySelectorAll(".tab[data-tab]").forEach((item) => item.classList.toggle("active", item.dataset.tab === name));
  document.getElementById("businessPanel").classList.toggle("hidden", name !== "business");
  document.getElementById("productPanel").classList.toggle("hidden", name !== "product");
  document.getElementById("rawPanel").classList.toggle("hidden", name !== "raw");
}

function showSummaryTab(name) {
  document.querySelectorAll(".summary-tab").forEach((item) => item.classList.toggle("active", item.dataset.summaryTab === name));
  document.getElementById("summaryBusinessPanel").classList.toggle("hidden", name !== "business");
  document.getElementById("summaryProductPanel").classList.toggle("hidden", name !== "product");
}

async function createAnalysis() {
  const form = document.getElementById("analysisForm");
  const payload = Object.fromEntries(new FormData(form).entries());
  if (!String(payload.raw_text || "").trim() && document.getElementById("batchFiles").files.length) {
    await analyzeFiles();
    return;
  }
  const button = document.getElementById("analyzeBtn");
  setMessage("createMessage", "正在调用 GPT 分析，请稍等。");
  button.disabled = true;
  try {
    const record = await api("/api/analyses", { method: "POST", body: payload });
    setCurrent(record);
    setMessage("createMessage", "");
    showView("result");
    loadHistory();
  } catch (error) {
    setMessage("createMessage", error.message);
  } finally {
    button.disabled = false;
  }
}

async function analyzeFiles() {
  const input = document.getElementById("batchFiles");
  const files = Array.from(input.files || []);
  const button = document.getElementById("analyzeFilesBtn");
  const singleButton = document.getElementById("analyzeBtn");
  const progress = document.getElementById("batchProgress");
  if (!files.length) {
    setMessage("createMessage", "请先选择要分析的文本文件。");
    return;
  }
  if (files.length > 20) {
    setMessage("createMessage", "一次最多建议分析 20 个文件，请分批处理。");
    return;
  }

  progress.innerHTML = "";
  button.disabled = true;
  singleButton.disabled = true;
  setMessage("createMessage", `开始批量分析 ${files.length} 个文件。`);
  let lastRecord = null;
  let successCount = 0;

  for (let index = 0; index < files.length; index += 1) {
    const file = files[index];
    const row = renderBatchRow(progress, file.name, `等待分析 ${index + 1}/${files.length}`);
    try {
      updateBatchRow(row, "读取文本");
      const text = await readTextFile(file);
      if (text.trim().length < 30) {
        throw new Error("文本内容太短，无法分析");
      }
      updateBatchRow(row, "GPT 分析中");
      const record = await api("/api/analyses", {
        method: "POST",
        body: { raw_text: text, source_filename: file.name },
      });
      lastRecord = record;
      successCount += 1;
      updateBatchRow(row, `完成：${record.title}`, "done");
    } catch (error) {
      updateBatchRow(row, error.message, "failed");
    }
  }

  await loadHistory();
  if (lastRecord) {
    setCurrent(lastRecord);
    showView("result");
  }
  setMessage("createMessage", `批量分析完成：成功 ${successCount} 个，失败 ${files.length - successCount} 个。`);
  button.disabled = false;
  singleButton.disabled = false;
}

function renderBatchRow(parent, filename, status) {
  const row = document.createElement("div");
  row.className = "batch-row";
  row.innerHTML = `<strong>${escapeHtml(filename)}</strong><span>${escapeHtml(status)}</span>`;
  parent.appendChild(row);
  return row;
}

function updateBatchRow(row, status, stateName = "") {
  row.classList.toggle("done", stateName === "done");
  row.classList.toggle("failed", stateName === "failed");
  const statusEl = row.querySelector("span");
  statusEl.textContent = status;
}

async function readTextFile(file) {
  const buffer = await file.arrayBuffer();
  const decoders = ["utf-8", "gb18030", "gbk"];
  for (const encoding of decoders) {
    try {
      return new TextDecoder(encoding, { fatal: true }).decode(buffer);
    } catch (error) {
      // Try the next common Chinese text encoding.
    }
  }
  return new TextDecoder("utf-8").decode(buffer);
}

async function loadHistory() {
  const date = document.getElementById("historyDate")?.value || "";
  const url = date ? `/api/analyses?analysis_date=${encodeURIComponent(date)}` : "/api/analyses";
  const data = await api(url);
  const body = document.getElementById("historyRows");
  const selectAll = document.getElementById("selectAllHistory");
  body.innerHTML = "";
  if (selectAll) selectAll.checked = false;
  for (const row of data.rows) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td class="select-col"><input class="history-select" type="checkbox" value="${escapeHtml(row.id)}" aria-label="选择 ${escapeHtml(row.title)}" /></td>
      <td>${escapeHtml(row.title)}</td>
      <td>${escapeHtml(row.customer_name || "-")}</td>
      <td>${escapeHtml(row.sales_name || "-")}</td>
      <td>${escapeHtml(row.business_opportunity || "-")}</td>
      <td>${escapeHtml(row.lead_level || "-")}</td>
      <td>${escapeHtml(row.sales_stage || "-")}</td>
      <td>${escapeHtml(row.product_fit || "-")}</td>
      <td>${escapeHtml(row.business_sent_status)} / ${escapeHtml(row.product_sent_status)}</td>
      <td>${escapeHtml(row.created_at)}</td>
      <td><button type="button" class="danger small delete-history-btn">删除</button></td>
    `;
    tr.addEventListener("click", async () => {
      const record = await api(`/api/analyses/${row.id}`);
      setCurrent(record);
      showView("result");
    });
    tr.querySelector(".delete-history-btn").addEventListener("click", async (event) => {
      event.stopPropagation();
      await deleteHistoryRecord(row);
    });
    tr.querySelector(".history-select").addEventListener("click", (event) => {
      event.stopPropagation();
      updateSelectAllHistoryState();
    });
    body.appendChild(tr);
  }
}

function clearHistoryFilter() {
  document.getElementById("historyDate").value = "";
  loadHistory();
}

function toggleAllHistoryRows(event) {
  document.querySelectorAll(".history-select").forEach((checkbox) => {
    checkbox.checked = event.target.checked;
  });
}

function updateSelectAllHistoryState() {
  const checkboxes = Array.from(document.querySelectorAll(".history-select"));
  const selectAll = document.getElementById("selectAllHistory");
  if (!selectAll || !checkboxes.length) {
    if (selectAll) selectAll.checked = false;
    return;
  }
  selectAll.checked = checkboxes.every((item) => item.checked);
}

async function deleteSelectedHistory() {
  const ids = Array.from(document.querySelectorAll(".history-select:checked")).map((item) => item.value);
  if (!ids.length) {
    alert("请先勾选要删除的分析记录。");
    return;
  }
  const confirmed = window.confirm(`确定删除选中的 ${ids.length} 条分析记录吗？`);
  if (!confirmed) return;
  try {
    await api("/api/analyses/batch-delete", { method: "POST", body: { ids } });
    if (state.current && ids.includes(state.current.id)) {
      state.current = null;
      showView("history");
    }
    await loadHistory();
  } catch (error) {
    alert(error.message);
  }
}

async function deleteHistoryRecord(row) {
  const confirmed = window.confirm(`确定删除这条分析记录吗？\n\n${row.title}`);
  if (!confirmed) return;
  try {
    await api(`/api/analyses/${row.id}`, { method: "DELETE" });
    if (state.current?.id === row.id) {
      state.current = null;
      showView("history");
    }
    await loadHistory();
  } catch (error) {
    alert(error.message);
  }
}

async function loadDailySummary() {
  const date = document.getElementById("summaryDate").value || todayDate();
  setMessage("summaryMessage", "正在读取汇总。");
  try {
    const data = await api(`/api/summaries?summary_date=${encodeURIComponent(date)}`);
    renderDailySummary(data.summary, data.record_count);
    setMessage("summaryMessage", data.summary ? "已读取已保存汇总。" : "这一天还没有汇总，可点击生成。");
  } catch (error) {
    setMessage("summaryMessage", error.message);
  }
}

async function generateDailySummary() {
  const button = document.getElementById("generateSummaryBtn");
  const date = document.getElementById("summaryDate").value || todayDate();
  button.disabled = true;
  setMessage("summaryMessage", "正在调用 GPT 生成今日汇总。");
  try {
    const summary = await api("/api/summaries/generate", {
      method: "POST",
      body: { summary_date: date },
    });
    renderDailySummary(summary, summary.record_count);
    setMessage("summaryMessage", "汇总已生成，可编辑后保存并发送。");
  } catch (error) {
    setMessage("summaryMessage", error.message);
  } finally {
    button.disabled = false;
  }
}

async function saveDailySummary() {
  if (!state.currentSummary) {
    setMessage("summaryMessage", "请先生成汇总。");
    return;
  }
  const payload = {
    business_summary: document.getElementById("businessSummaryText").value.trim(),
    product_summary: document.getElementById("productSummaryText").value.trim(),
  };
  setMessage("summaryMessage", "正在保存汇总。");
  try {
    const summary = await api(`/api/summaries/${state.currentSummary.id}`, { method: "PUT", body: payload });
    renderDailySummary(summary, summary.record_count);
    setMessage("summaryMessage", "汇总已保存。");
  } catch (error) {
    setMessage("summaryMessage", error.message);
  }
}

async function sendDailySummary(channel) {
  if (!state.currentSummary) {
    setMessage("summaryMessage", "请先生成汇总。");
    return;
  }
  await saveDailySummary();
  const button = document.getElementById(channel === "business" ? "sendSummaryBusinessBtn" : "sendSummaryProductBtn");
  button.disabled = true;
  setMessage("summaryMessage", "正在发送钉钉群。");
  try {
    await api(`/api/summaries/${state.currentSummary.id}/send/${channel}`, { method: "POST" });
    const data = await api(`/api/summaries?summary_date=${encodeURIComponent(state.currentSummary.summary_date)}`);
    renderDailySummary(data.summary, data.record_count);
    setMessage("summaryMessage", "钉钉发送成功。");
  } catch (error) {
    setMessage("summaryMessage", error.message);
  } finally {
    button.disabled = false;
  }
}

function renderDailySummary(summary, recordCount = 0) {
  state.currentSummary = summary || null;
  document.getElementById("summaryRecordCount").textContent = recordCount || summary?.record_count || 0;
  document.getElementById("summaryBusinessStatus").textContent = summary?.business_sent_status || "未生成";
  document.getElementById("summaryProductStatus").textContent = summary?.product_sent_status || "未生成";
  document.getElementById("businessSummaryText").value = summary?.business_summary || "";
  document.getElementById("productSummaryText").value = summary?.product_summary || "";
}

function setCurrent(record) {
  state.current = record;
  document.getElementById("resultTitle").textContent = record.title;
  document.getElementById("resultMeta").textContent = [
    record.customer_name && `客户：${record.customer_name}`,
    record.sales_name && `销售：${record.sales_name}`,
    record.call_type && `通话类型：${record.call_type}`,
    `创建：${record.created_at}`,
    `发送：${record.business_sent_status}/${record.product_sent_status}`,
  ].filter(Boolean).join(" · ");
  document.getElementById("metaTitle").value = record.title || "";
  document.getElementById("metaCallType").value = record.call_type || "";
  document.getElementById("metaCustomer").value = record.customer_name || "";
  document.getElementById("metaSales").value = record.sales_name || "";
  document.getElementById("rawText").value = record.raw_text || "";
  renderSummary(record.business_result);
  renderMessageEditor("businessPanel", "businessMessageText", record.business_message || "");
  renderMessageEditor("productPanel", "productMessageText", record.product_message || "");
  showTab(state.activeTab);
}

function renderMessageEditor(targetId, textareaId, value) {
  const target = document.getElementById(targetId);
  target.innerHTML = "";
  const textarea = document.createElement("textarea");
  textarea.id = textareaId;
  textarea.className = "message-editor";
  textarea.value = value || "";
  target.appendChild(textarea);
}

function renderSummary(business) {
  const pc = business.project_conclusion || {};
  document.getElementById("sumOpportunity").textContent = pc.business_opportunity || "-";
  document.getElementById("sumLead").textContent = pc.lead_level || "-";
  document.getElementById("sumStage").textContent = pc.sales_stage || "-";
  document.getElementById("sumFit").textContent = pc.product_fit || "-";
  document.getElementById("sumConfidence").textContent = pc.confidence || "-";
}

function renderEditor(targetId, root, data) {
  const target = document.getElementById(targetId);
  target.innerHTML = "";
  for (const section of schemas[root]) {
    const block = document.createElement("section");
    block.className = "section";
    block.innerHTML = `<h3>${escapeHtml(section.title)}</h3>`;
    if (section.type === "evidence") {
      block.appendChild(renderEvidence(root, section.path, getPath(data, section.path) || []));
    } else if (section.type === "verify") {
      block.appendChild(renderVerify(root, section.path, getPath(data, section.path) || []));
    } else {
      block.appendChild(renderFields(root, section.path, getPath(data, section.path) || {}, section.fields));
    }
    target.appendChild(block);
  }
}

function renderFields(root, path, obj, fields) {
  const wrap = document.createElement("div");
  wrap.className = "field-grid";
  for (const field of fields) {
    const config = typeof field === "string" ? { key: field } : field;
    if (config.type === "array") {
      const item = document.createElement("label");
      item.className = "wide";
      item.innerHTML = `<span>${escapeHtml(config.label || fieldLabels[config.key] || config.key)}</span>`;
      item.appendChild(renderArray(root, `${path}.${config.key}`, obj[config.key] || [], config.max || 5));
      wrap.appendChild(item);
      continue;
    }
    if (config.type === "risk") {
      const item = document.createElement("label");
      item.className = "wide";
      item.innerHTML = `<span>${escapeHtml(config.label)}</span>`;
      item.appendChild(renderRisk(root, `${path}.${config.key}`, obj[config.key] || [], config.max || 3));
      wrap.appendChild(item);
      continue;
    }
    const label = document.createElement("label");
    if (["next_action", "reason", "verification_method", "customer_quote"].includes(config.key)) {
      label.className = "wide";
    }
    label.innerHTML = `<span>${escapeHtml(config.label || fieldLabels[config.key] || config.key)}</span>`;
    const input = document.createElement(config.type === "boolean" ? "input" : "textarea");
    if (config.type === "boolean") {
      input.type = "checkbox";
      input.checked = Boolean(obj[config.key]);
    } else {
      input.value = obj[config.key] || "";
    }
    input.dataset.path = `${root}.${path}.${config.key}`;
    label.appendChild(input);
    wrap.appendChild(label);
  }
  return wrap;
}

function renderArray(root, path, values, max) {
  const wrap = document.createElement("div");
  wrap.className = "array-list";
  for (let index = 0; index < max; index += 1) {
    const row = document.createElement("div");
    row.className = "array-row";
    row.innerHTML = `<span>${index + 1}</span>`;
    const textarea = document.createElement("textarea");
    textarea.value = values[index] || "";
    textarea.dataset.path = `${root}.${path}.${index}`;
    row.appendChild(textarea);
    wrap.appendChild(row);
  }
  return wrap;
}

function renderEvidence(root, path, values) {
  const wrap = document.createElement("div");
  for (let index = 0; index < 6; index += 1) {
    const item = values[index] || {};
    const row = document.createElement("div");
    row.className = "evidence-row";
    row.innerHTML = `
      <label><span>原话 ${index + 1}</span><textarea data-path="${root}.${path}.${index}.quote">${escapeHtml(item.quote || "")}</textarea></label>
      <label><span>能够确认的事实 ${index + 1}</span><textarea data-path="${root}.${path}.${index}.confirmed_fact">${escapeHtml(item.confirmed_fact || "")}</textarea></label>
    `;
    wrap.appendChild(row);
  }
  return wrap;
}

function renderVerify(root, path, values) {
  const wrap = document.createElement("div");
  for (let index = 0; index < 3; index += 1) {
    const item = values[index] || {};
    const row = document.createElement("div");
    row.className = "field-grid section";
    for (const key of ["question", "need_to_confirm", "why_important", "suggested_question"]) {
      const label = document.createElement("label");
      label.className = key === "suggested_question" ? "wide" : "";
      label.innerHTML = `<span>${escapeHtml(verifyLabel(key, index))}</span>`;
      const textarea = document.createElement("textarea");
      textarea.value = item[key] || "";
      textarea.dataset.path = `${root}.${path}.${index}.${key}`;
      label.appendChild(textarea);
      row.appendChild(label);
    }
    wrap.appendChild(row);
  }
  return wrap;
}

function renderRisk(root, path, values, max) {
  const wrap = document.createElement("div");
  for (let index = 0; index < max; index += 1) {
    const item = values[index] || {};
    const row = document.createElement("div");
    row.className = "field-grid section";
    for (const key of ["customer_question_or_node", "sales_response", "problem", "better_response"]) {
      const label = document.createElement("label");
      label.innerHTML = `<span>${escapeHtml(riskLabel(key, index))}</span>`;
      const textarea = document.createElement("textarea");
      textarea.value = item[key] || "";
      textarea.dataset.path = `${root}.${path}.${index}.${key}`;
      label.appendChild(textarea);
      row.appendChild(label);
    }
    wrap.appendChild(row);
  }
  return wrap;
}

async function saveAnalysis() {
  if (!state.current) return;
  const payload = collectEditorData();
  setMessage("resultMessage", "正在保存修改。");
  try {
    const record = await api(`/api/analyses/${state.current.id}`, { method: "PUT", body: payload });
    setCurrent(record);
    setMessage("resultMessage", "已保存。");
    loadHistory();
  } catch (error) {
    setMessage("resultMessage", error.message);
  }
}

async function refreshMeta() {
  if (!state.current) return;
  const button = document.getElementById("refreshMetaBtn");
  button.disabled = true;
  setMessage("resultMessage", "正在根据原文重新识别标题、客户和销售。");
  try {
    const record = await api(`/api/analyses/${state.current.id}/refresh-meta`, { method: "POST" });
    setCurrent(record);
    setMessage("resultMessage", "已重新识别信息。");
    loadHistory();
  } catch (error) {
    setMessage("resultMessage", error.message);
  } finally {
    button.disabled = false;
  }
}

async function sendAnalysis(channel) {
  if (!state.current) return;
  await saveAnalysis();
  const button = document.getElementById(channel === "business" ? "sendBusinessBtn" : "sendProductBtn");
  button.disabled = true;
  setMessage("resultMessage", "正在发送钉钉群。");
  try {
    await api(`/api/analyses/${state.current.id}/send/${channel}`, { method: "POST" });
    const record = await api(`/api/analyses/${state.current.id}`);
    setCurrent(record);
    setMessage("resultMessage", "钉钉发送成功。");
    loadHistory();
  } catch (error) {
    setMessage("resultMessage", error.message);
  } finally {
    button.disabled = false;
  }
}

function collectEditorData() {
  const business = structuredClone(state.current.business_result || {});
  const product = structuredClone(state.current.product_result || {});
  document.querySelectorAll("#businessPanel [data-path], #productPanel [data-path]").forEach((input) => {
    const [root, ...segments] = input.dataset.path.split(".");
    const target = root === "business" ? business : product;
    const value = input.type === "checkbox" ? input.checked : input.value.trim();
    setPath(target, segments, value);
  });
  cleanupArrays(business);
  cleanupArrays(product);
  return {
    title: document.getElementById("metaTitle").value.trim(),
    call_type: document.getElementById("metaCallType").value.trim(),
    customer_name: document.getElementById("metaCustomer").value.trim(),
    sales_name: document.getElementById("metaSales").value.trim(),
    business_message: document.getElementById("businessMessageText")?.value.trim() || "",
    product_message: document.getElementById("productMessageText")?.value.trim() || "",
    business_result: business,
    product_result: product,
  };
}

function cleanupArrays(value) {
  if (Array.isArray(value)) {
    for (let index = value.length - 1; index >= 0; index -= 1) {
      cleanupArrays(value[index]);
      if (value[index] === "" || isEmptyObject(value[index])) value.splice(index, 1);
    }
    return;
  }
  if (value && typeof value === "object") {
    Object.values(value).forEach(cleanupArrays);
  }
}

function isEmptyObject(value) {
  return value && typeof value === "object" && !Array.isArray(value) && Object.values(value).every((item) => item === "" || item == null);
}

function getPath(obj, path) {
  return path.split(".").reduce((acc, key) => acc && acc[key], obj);
}

function setPath(obj, segments, value) {
  let cursor = obj;
  for (let index = 0; index < segments.length - 1; index += 1) {
    const key = segments[index];
    const nextKey = segments[index + 1];
    if (cursor[key] == null) cursor[key] = /^\d+$/.test(nextKey) ? [] : {};
    cursor = cursor[key];
  }
  cursor[segments[segments.length - 1]] = value;
}

function verifyLabel(key, index) {
  const labels = {
    question: `问题 ${index + 1}`,
    need_to_confirm: "需要确认",
    why_important: "为什么重要",
    suggested_question: "建议销售怎么问",
  };
  return labels[key] || key;
}

function riskLabel(key, index) {
  const labels = {
    customer_question_or_node: `客户问题或关键节点 ${index + 1}`,
    sales_response: "销售实际回应",
    problem: "存在的问题",
    better_response: "更合理的回应",
  };
  return labels[key] || key;
}

async function api(url, options = {}) {
  const init = { method: options.method || "GET", headers: {} };
  if (options.body) {
    init.headers["Content-Type"] = "application/json";
    init.body = JSON.stringify(options.body);
  }
  const response = await fetch(url, init);
  const text = await response.text();
  const data = text ? JSON.parse(text) : {};
  if (!response.ok) {
    throw new Error(data.detail || "请求失败");
  }
  return data;
}

function setMessage(id, text) {
  document.getElementById(id).textContent = text || "";
}

function todayDate() {
  const now = new Date();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${now.getFullYear()}-${month}-${day}`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

document.addEventListener("DOMContentLoaded", () => {
  setupUploadZone();
});

function setupUploadZone() {
  const input = document.getElementById("batchFiles");
  const zone = document.getElementById("dropZone");
  if (!input || !zone) return;

  zone.addEventListener("click", () => input.click());
  input.addEventListener("change", () => updateSelectedFiles(input.files));

  for (const eventName of ["dragenter", "dragover"]) {
    zone.addEventListener(eventName, (event) => {
      event.preventDefault();
      zone.classList.add("dragover");
    });
  }

  for (const eventName of ["dragleave", "drop"]) {
    zone.addEventListener(eventName, (event) => {
      event.preventDefault();
      zone.classList.remove("dragover");
    });
  }

  zone.addEventListener("drop", (event) => {
    const files = event.dataTransfer?.files;
    if (!files || !files.length) return;
    input.files = files;
    updateSelectedFiles(files);
  });
}

function updateSelectedFiles(files) {
  const items = Array.from(files || []);
  const label = document.getElementById("selectedFilesText");
  if (!label) return;
  if (!items.length) {
    label.textContent = "未选择文件";
    return;
  }
  const names = items.slice(0, 3).map((file) => file.name).join("、");
  label.textContent = items.length > 3 ? `已选择 ${items.length} 个文件：${names} 等` : `已选择 ${items.length} 个文件：${names}`;
}

async function analyzeFiles() {
  const input = document.getElementById("batchFiles");
  const files = Array.from(input.files || []);
  const button = document.getElementById("analyzeFilesBtn");
  const singleButton = document.getElementById("analyzeBtn");
  const progress = document.getElementById("batchProgress");

  if (!files.length) {
    setMessage("createMessage", "请先选择或拖入要分析的文件。");
    return;
  }
  if (files.length > 20) {
    setMessage("createMessage", "一次最多建议分析 20 个文件，请分批处理。");
    return;
  }

  progress.innerHTML = "";
  button.disabled = true;
  singleButton.disabled = true;
  setMessage("createMessage", `开始解析 ${files.length} 个文件。`);

  const rowMap = new Map();
  for (const file of files) {
    rowMap.set(file.name, renderBatchRow(progress, file.name, "等待解析"));
  }

  let extracted = [];
  try {
    extracted = await extractFiles(files);
  } catch (error) {
    setMessage("createMessage", error.message);
    button.disabled = false;
    singleButton.disabled = false;
    return;
  }

  let lastRecord = null;
  let successCount = 0;
  setMessage("createMessage", `开始批量分析 ${extracted.length} 个文件。`);

  for (let index = 0; index < extracted.length; index += 1) {
    const file = extracted[index];
    const row = rowMap.get(file.name) || renderBatchRow(progress, file.name, "等待分析");
    try {
      if (file.error) {
        throw new Error(file.error);
      }
      const text = String(file.text || "");
      if (text.trim().length < 30) {
        throw new Error("文本内容太短，无法分析");
      }
      updateBatchRow(row, `GPT 分析中 ${index + 1}/${extracted.length}`);
      const record = await api("/api/analyses", {
        method: "POST",
        body: { raw_text: text, source_filename: file.name },
      });
      lastRecord = record;
      successCount += 1;
      updateBatchRow(row, `完成：${record.title}`, "done");
    } catch (error) {
      updateBatchRow(row, error.message, "failed");
    }
  }

  await loadHistory();
  if (lastRecord) {
    setCurrent(lastRecord);
    showView("result");
  }
  setMessage("createMessage", `批量分析完成：成功 ${successCount} 个，失败 ${extracted.length - successCount} 个。`);
  button.disabled = false;
  singleButton.disabled = false;
}

async function extractFiles(files) {
  const form = new FormData();
  for (const file of files) {
    form.append("files", file, file.name);
  }
  const response = await fetch("/api/extract-files", {
    method: "POST",
    body: form,
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "文件解析失败");
  }
  return data.files || [];
}
