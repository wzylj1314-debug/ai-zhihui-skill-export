const state = {
  cards: [],
  batches: [],
  allowedFiles: [],
  currentBatch: "",
  latestBatch: "",
  processStartedAt: 0,
  currentStage: "",
  progressPercent: 0,
  elapsedTimer: null,
  scanTimers: new Map(),
  scanHits: new Map(),
};

const stageProgress = {
  upload: 10,
  ocr: 30,
  scrub: 45,
  structure: 70,
  rescan: 90,
  done: 100,
};

const stageLabels = {
  upload: "准备上传",
  ocr: "OCR 识别中",
  scrub: "本地脱敏中",
  structure: "整理 FAQ 中",
  rescan: "敏感信息复扫中",
  done: "整理完成",
};

const today = new Date().toISOString().slice(0, 10);
const draftDate = document.querySelector("#draftDate");
const fileInput = document.querySelector("#fileInput");
const dropZone = document.querySelector("#dropZone");
const uploadBtn = document.querySelector("#uploadBtn");
const processBtn = document.querySelector("#processBtn");
const loadDraftsBtn = document.querySelector("#loadDraftsBtn");
const batchFilter = document.querySelector("#batchFilter");
const latestBatchBtn = document.querySelector("#latestBatchBtn");
const cardsEl = document.querySelector("#cards");
const warningEl = document.querySelector("#warning");
const processMessage = document.querySelector("#processMessage");
const saveMessage = document.querySelector("#saveMessage");
const progressText = document.querySelector("#progressText");
const elapsedText = document.querySelector("#elapsedText");
const progressBar = document.querySelector("#progressBar");
const progressHint = document.querySelector("#progressHint");

draftDate.value = today;
init();

async function init() {
  bindEvents();
  try {
    await loadAllowedFiles();
    await loadDrafts();
  } catch (error) {
    showError(processMessage, error);
  }
}

function bindEvents() {
  dropZone.addEventListener("click", () => fileInput.click());
  dropZone.addEventListener("dragover", (event) => {
    event.preventDefault();
    dropZone.classList.add("active");
  });
  dropZone.addEventListener("dragleave", () => dropZone.classList.remove("active"));
  dropZone.addEventListener("drop", (event) => {
    event.preventDefault();
    dropZone.classList.remove("active");
    fileInput.files = event.dataTransfer.files;
    showSelectedFiles();
  });
  fileInput.addEventListener("change", showSelectedFiles);
  uploadBtn.addEventListener("click", uploadFiles);
  processBtn.addEventListener("click", startProcess);
  loadDraftsBtn.addEventListener("click", () => loadDrafts());
  batchFilter.addEventListener("change", () => {
    state.currentBatch = batchFilter.value;
    renderCards();
  });
  latestBatchBtn.addEventListener("click", () => {
    state.currentBatch = state.latestBatch || "";
    batchFilter.value = state.currentBatch;
    renderCards();
  });
  document.querySelector("#saveBtn").addEventListener("click", saveDrafts);
  document.querySelector("#downloadBtn").addEventListener("click", downloadDraft);
  document.querySelector("#clearBtn").addEventListener("click", clearDrafts);
}

function showSelectedFiles() {
  const files = [...fileInput.files];
  document.querySelector("#uploadList").textContent = files.map((file) => file.name).join("，") || "未选择文件";
}

async function uploadFiles() {
  try {
    const files = [...fileInput.files];
    if (!files.length) {
      setUploadMessage("请选择截图。");
      return;
    }
    const form = new FormData();
    files.forEach((file) => form.append("files", file));
    const result = await api("/api/upload", { method: "POST", body: form });
    setUploadMessage(`已上传：${result.files.join("，")}`);
  } catch (error) {
    setUploadMessage(error.message);
  }
}

function setUploadMessage(text) {
  document.querySelector("#uploadList").textContent = text;
}

async function startProcess() {
  try {
    resetSteps();
    state.processStartedAt = Date.now();
    startElapsedTimer();
    setStep("upload", "running");
    updateProgress("upload", "running");
    processMessage.textContent = "";
    const { job_id } = await api("/api/process", { method: "POST" });
    pollJob(job_id);
  } catch (error) {
    stopElapsedTimer();
    updateProgress(state.currentStage || "upload", "failed");
    showError(processMessage, error);
  }
}

async function pollJob(jobId) {
  try {
    const result = await api(`/api/process/${jobId}`);
    setStep(result.stage, result.status);
    updateProgress(result.stage, result.status, result);
    processMessage.textContent = result.message || "";
    if (result.status === "running") {
      setTimeout(() => pollJob(jobId), 1500);
      return;
    }
    if (result.status === "failed") {
      stopElapsedTimer();
      setStep(result.stage, "failed");
      return;
    }
    if (result.status === "done") {
      stopElapsedTimer();
      draftDate.value = result.draft_date;
      state.latestBatch = result.batch || "";
      state.currentBatch = state.latestBatch;
      await loadDrafts({ keepBatch: true });
    }
  } catch (error) {
    stopElapsedTimer();
    updateProgress(state.currentStage || "upload", "failed");
    showError(processMessage, error);
  }
}

function resetSteps() {
  document.querySelectorAll("#steps li").forEach((item) => {
    item.classList.remove("active", "done", "failed");
  });
  state.currentStage = "";
  state.processStartedAt = 0;
  state.progressPercent = 0;
  stopElapsedTimer();
  updateProgress("", "idle");
}

function setStep(stage, status) {
  document.querySelectorAll("#steps li").forEach((item) => {
    item.classList.remove("active", "done", "failed");
    if (item.dataset.stage === stage) item.classList.add(status === "failed" ? "failed" : "active");
  });
  if (status === "done") {
    document.querySelectorAll("#steps li").forEach((item) => item.classList.add("done"));
  }
}

function startElapsedTimer() {
  stopElapsedTimer();
  updateElapsed();
  state.elapsedTimer = setInterval(() => {
    updateElapsed();
    updateProgress(state.currentStage, "running");
  }, 1000);
}

function stopElapsedTimer() {
  if (state.elapsedTimer) {
    clearInterval(state.elapsedTimer);
    state.elapsedTimer = null;
  }
  updateElapsed();
}

function updateElapsed() {
  if (!elapsedText) return;
  const elapsed = state.processStartedAt ? Date.now() - state.processStartedAt : 0;
  elapsedText.textContent = `已用时 ${formatDuration(elapsed)}`;
}

function updateProgress(stage, status, detail = {}) {
  if (!progressText || !progressBar || !progressHint) return;
  if (status === "idle") {
    state.currentStage = "";
    state.progressPercent = 0;
    progressBar.style.width = "0%";
    progressBar.classList.remove("done", "failed");
    progressText.textContent = "等待开始";
    progressHint.textContent = "";
    return;
  }
  state.currentStage = stage || state.currentStage || "";
  const effectiveStage = stage || state.currentStage;
  let percent = stageProgress[effectiveStage] || 0;
  if (effectiveStage === "ocr" && detail.ocr_tiles) {
    const tileRatio = Math.min(1, Math.max(0, Number(detail.ocr_tile || 0) / Number(detail.ocr_tiles)));
    percent = Math.round(10 + tileRatio * 35);
  }
  if (status === "done") percent = 100;
  if (status === "failed") percent = Math.max(percent, 8);
  if (status === "running") {
    percent = Math.max(percent, state.progressPercent || 0);
  }
  state.progressPercent = percent;

  progressBar.style.width = `${percent}%`;
  progressBar.classList.toggle("done", status === "done");
  progressBar.classList.toggle("failed", status === "failed");

  if (status === "failed") {
    progressText.textContent = `${stageLabels[effectiveStage] || "处理中"}失败`;
    progressHint.textContent = "下面黑色日志里有失败原因。";
    return;
  }
  if (status === "done") {
    progressText.textContent = "100% · 整理完成";
    progressHint.textContent = "草稿已写入，可以加载本次结果。";
    return;
  }

  const detailText = effectiveStage === "ocr" && detail.ocr_detail ? `：${detail.ocr_detail}` : "";
  progressText.textContent = `${percent}% · ${stageLabels[effectiveStage] || "处理中"}${detailText}`;
  const elapsed = state.processStartedAt ? Date.now() - state.processStartedAt : 0;
  if (effectiveStage === "ocr") {
    if (detail.ocr_detail?.startsWith("命中缓存")) {
      progressHint.textContent = "这张图已有 OCR 缓存，会直接复用。";
    } else {
      progressHint.textContent = elapsed > 15000 ? "OCR 首次加载模型会慢一些，分片数字还在变化就说明还在跑。" : "";
    }
  } else if (effectiveStage === "structure") {
    progressHint.textContent = elapsed > 30000 ? "正在等待模型整理问答，截图多或网关忙时这一步会更久。" : "";
  } else {
    progressHint.textContent = "";
  }
}

function formatDuration(ms) {
  const totalSeconds = Math.max(0, Math.floor(ms / 1000));
  const minutes = String(Math.floor(totalSeconds / 60)).padStart(2, "0");
  const seconds = String(totalSeconds % 60).padStart(2, "0");
  return `${minutes}:${seconds}`;
}

async function loadAllowedFiles() {
  const data = await api("/api/allowed-files");
  state.allowedFiles = ["待确认", ...data.files];
}

async function loadDrafts(options = {}) {
  try {
    const data = await api(`/api/drafts?date=${encodeURIComponent(draftDate.value)}`);
    state.cards = data.cards;
    state.cards.forEach((card) => {
      if (!state.allowedFiles.includes(card["归属文件"])) card["归属文件"] = "待确认";
    });
    state.batches = data.batches || [];
    if (!options.keepBatch && !state.batches.includes(state.currentBatch)) {
      state.currentBatch = "";
    }
    if (!state.latestBatch && state.batches.length) {
      state.latestBatch = state.batches[0];
    }
    renderBatchFilter();
    state.scanHits.clear();
    renderCards();
    updateWarning();
  } catch (error) {
    cardsEl.innerHTML = `<div class="empty">${escapeHtml(error.message)}</div>`;
  }
}

function renderBatchFilter() {
  const options = ['<option value="">全部草稿</option>'];
  state.batches.forEach((batch) => {
    options.push(`<option value="${escapeAttr(batch)}">${escapeHtml(displayBatch(batch))}</option>`);
  });
  batchFilter.innerHTML = options.join("");
  batchFilter.value = state.currentBatch || "";
}

function displayedCards() {
  return state.cards
    .map((card, index) => ({ card, index }))
    .filter((item) => !state.currentBatch || item.card["批次"] === state.currentBatch);
}

function renderCards() {
  cardsEl.innerHTML = "";
  const visible = displayedCards();
  if (!visible.length) {
    cardsEl.innerHTML = '<div class="empty">没有草稿。上传截图并开始整理后会出现在这里。</div>';
    return;
  }
  visible.forEach(({ card, index }) => {
    const el = document.createElement("article");
    el.className = "card";
    el.dataset.index = index;
    el.innerHTML = `
      <div class="card-head">
        <h3>${escapeHtml(card.id_title)}</h3>
        <div class="card-flags">
          <span class="quality-state ${answerQualityProblem(card) ? "bad" : ""}" id="quality-${index}">${answerQualityText(card)}</span>
          <span class="scan-state" id="scan-${index}">脱敏检查：待检查</span>
          <button class="danger small" type="button" data-delete-card="${index}">删除此条</button>
        </div>
      </div>
      ${readonlyRow("台账ID", card["台账ID"] || "未同步")}
      ${readonlyRow("整理批次", displayBatch(card["批次"]))}
      ${selectRow(index, "状态", ["待审", "通过", "丢弃"], card["状态"] || "待审")}
      ${readonlyRow("入库状态", card["入库状态"] || "未入台账")}
      ${selectRow(index, "归属文件", state.allowedFiles, card["归属文件"] || "待确认")}
      ${inputRow(index, "建议ID", card["建议ID"], true, "正式ID")}
      <div class="row hint-row"><span></span><div class="muted" id="id-hint-${index}"></div></div>
      ${inputRow(index, "疑似重复", card["疑似重复"])}
      ${readonlyRow("来源", card["来源"])}
      ${readonlyRow("脱敏复扫", card["脱敏复扫"])}
      ${textareaRow(index, "证据片段", card["证据片段"], true)}
      ${inputRow(index, "问题", card["问题"])}
      ${textareaRow(index, "回答", card["回答"])}
      ${inputRow(index, "适用功能", card["适用功能"])}
      ${inputRow(index, "关键词", card["关键词"])}
      ${selectRow(index, "是否需要转人工", ["否", "是"], card["是否需要转人工"] || "否")}
    `;
    cardsEl.appendChild(el);
  });
  bindCardEvents();
  visible.forEach(({ index }) => scheduleScan(index));
}

function bindCardEvents() {
  cardsEl.querySelectorAll("[data-field]").forEach((input) => {
    input.addEventListener("input", onCardInput);
    input.addEventListener("change", onCardInput);
  });
  cardsEl.querySelectorAll("[data-next-id]").forEach((button) => {
    button.addEventListener("click", async () => {
      try {
        const index = Number(button.dataset.nextId);
        const card = state.cards[index];
        const file = card["归属文件"];
        const hint = document.querySelector(`#id-hint-${index}`);
        if (!state.allowedFiles.includes(file) || file === "待确认") {
          if (hint) hint.textContent = "先把归属文件选成 09_高频_FAQ.md 或 10_用户真实问法库.md。";
          return;
        }
        const prefix = card["建议ID"]?.startsWith("UQ-") ? "UQ" : "FAQ";
        const effectivePrefix = file === "10_用户真实问法库.md" ? "UQ" : prefix;
        const result = await api(`/api/next-id?file=${encodeURIComponent(file)}&prefix=${encodeURIComponent(effectivePrefix)}&feature=${encodeURIComponent(card["适用功能"] || "")}`);
        if (result.suggestion === "TODO-ID") {
          if (hint) hint.textContent = result.reason || "无法建议 ID";
          return;
        }
        const allocated = allocateDraftId(result.suggestion, index);
        card["建议ID"] = allocated.id;
        const currentInput = button.closest(".card")?.querySelector('[data-field="建议ID"]');
        if (currentInput) currentInput.value = allocated.id;
        if (hint) {
          hint.textContent = allocated.bumped
            ? `已按当前草稿顺延，避免重复：${allocated.id}`
            : `已按 ${result.feature_code || "功能"} 生成。`;
        }
      } catch (error) {
        const index = Number(button.dataset.nextId);
        const hint = document.querySelector(`#id-hint-${index}`);
        if (hint) hint.textContent = error.message;
      }
    });
  });
  cardsEl.querySelectorAll("[data-delete-card]").forEach((button) => {
    button.addEventListener("click", () => {
      const index = Number(button.dataset.deleteCard);
      const title = state.cards[index]?.id_title || "这条草稿";
      if (!confirm(`确定删除 ${title} 吗？保存后会从当天 Markdown 草稿里移除。`)) return;
      state.cards.splice(index, 1);
      state.scanHits.delete(index);
      renderCards();
      saveMessage.textContent = "已从页面移除。点“保存草稿”后写入文件。";
    });
  });
}

function onCardInput(event) {
  const index = Number(event.target.dataset.index);
  const field = event.target.dataset.field;
  state.cards[index][field] = event.target.value;
  if (field === "状态" && event.target.value === "通过" && hasHits(index)) {
    state.cards[index][field] = "待审";
    event.target.value = "待审";
    alert("脱敏检查有命中，不能设为通过。");
  }
  if (field === "状态" && event.target.value === "通过" && answerQualityProblem(state.cards[index])) {
    state.cards[index][field] = "待审";
    event.target.value = "待审";
    alert("答案内容不足，不能设为通过。");
  }
  if (field === "回答") updateQuality(index);
  if (["问题", "回答"].includes(field)) scheduleScan(index);
}

function scheduleScan(index) {
  clearTimeout(state.scanTimers.get(index));
  state.scanTimers.set(index, setTimeout(() => scanCard(index), 350));
}

async function scanCard(index) {
  try {
    const card = state.cards[index];
    const text = `${card["问题"] || ""}\n${card["回答"] || ""}`;
    const result = await api("/api/scan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    state.scanHits.set(index, result.hits || []);
    const el = document.querySelector(`#scan-${index}`);
    if (el) {
      el.textContent = result.ok ? "脱敏检查：通过" : `脱敏检查：命中 ${result.hits.length} 项`;
      el.classList.toggle("bad", !result.ok);
    }
    updateWarning();
  } catch (error) {
    const el = document.querySelector(`#scan-${index}`);
    if (el) {
      el.textContent = `脱敏检查失败：${error.message}`;
      el.classList.add("bad");
    }
  }
}

function updateWarning() {
  const total = [...state.scanHits.values()].reduce((sum, hits) => sum + hits.length, 0);
  warningEl.classList.toggle("hidden", total === 0);
  warningEl.textContent = total ? `发现 ${total} 个敏感信息命中，命中卡片不能设为通过。` : "";
}

function hasHits(index) {
  return (state.scanHits.get(index) || []).length > 0;
}

function answerQualityProblem(card) {
  const answer = String(card["回答"] || "").replace(/\s+/g, "");
  return !answer || answer === "---" || answer === "无" || answer.length < 10;
}

function answerQualityText(card) {
  return answerQualityProblem(card) ? "答案内容不足，不能设为通过" : "答案检查：通过";
}

function updateQuality(index) {
  const el = document.querySelector(`#quality-${index}`);
  if (!el) return;
  el.textContent = answerQualityText(state.cards[index]);
  el.classList.toggle("bad", answerQualityProblem(state.cards[index]));
}

async function saveDrafts() {
  try {
    const duplicates = duplicateFormalIds();
    if (duplicates.length) {
      saveMessage.textContent = `正式ID重复：${duplicates.join("，")}。请先修改后再保存。`;
      return;
    }
    const result = await api(`/api/drafts/${encodeURIComponent(draftDate.value)}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ cards: state.cards }),
    });
    state.cards = result.cards || state.cards;
    renderCards();
    saveMessage.textContent = "已保存；通过项已同步到运营台账。";
  } catch (error) {
    saveMessage.textContent = error.message;
  }
}

async function clearDrafts() {
  if (!confirm("确定清空当天草稿吗？原文件会移入 _trash。运营看板台账不会自动删除，如需移除请到看板撤回。")) return;
  try {
    await api(`/api/drafts/${encodeURIComponent(draftDate.value)}/clear`, { method: "POST" });
    state.cards = [];
    state.batches = [];
    state.currentBatch = "";
    state.latestBatch = "";
    renderBatchFilter();
    renderCards();
    saveMessage.textContent = "当天草稿已清空，原文件已移入 _trash。运营看板台账不会自动删除，如需移除请到看板按日期筛选后批量撤回。";
  } catch (error) {
    saveMessage.textContent = error.message;
  }
}

function downloadDraft() {
  window.location.href = `/api/drafts/${encodeURIComponent(draftDate.value)}/download`;
}

function row(label, body) {
  return `<label class="row"><span>${escapeHtml(label)}</span>${body}</label>`;
}

function selectRow(index, field, options, value) {
  const html = options.map((item) => `<option ${item === value ? "selected" : ""}>${escapeHtml(item)}</option>`).join("");
  return row(field, `<select data-index="${index}" data-field="${field}">${html}</select>`);
}

function inputRow(index, field, value = "", withButton = false, label = field) {
  const button = withButton ? `<button type="button" data-next-id="${index}">生成正式ID</button>` : "";
  return row(label, `<div class="inline"><input data-index="${index}" data-field="${field}" value="${escapeAttr(value || "")}" />${button}</div>`);
}

function readonlyRow(field, value = "") {
  return row(field, `<input value="${escapeAttr(value || "")}" readonly />`);
}

function textareaRow(index, field, value = "", readonly = false) {
  return row(field, `<textarea data-index="${index}" data-field="${field}" ${readonly ? "readonly" : ""}>${escapeHtml(value || "")}</textarea>`);
}

async function api(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) {
    let detail = await response.text();
    try {
      detail = JSON.parse(detail).detail || detail;
    } catch (_error) {
      // Keep the raw response text.
    }
    throw new Error(detail);
  }
  return response.json();
}

function showError(target, error) {
  target.textContent = error.message;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char]));
}

function escapeAttr(value) {
  return escapeHtml(value).replace(/\n/g, " ");
}

function displayBatch(value = "") {
  const match = String(value).match(/^RUN-(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})(\d{2})$/);
  if (!match) return value || "未记录";
  return `${match[1]}-${match[2]}-${match[3]} ${match[4]}:${match[5]}:${match[6]}`;
}

function allocateDraftId(suggestion, currentIndex) {
  const parsed = parseFormalId(suggestion);
  if (!parsed) return { id: suggestion, bumped: false };
  const used = new Set(
    state.cards
      .map((card, index) => (index === currentIndex ? "" : card["建议ID"]))
      .filter(Boolean)
  );
  let number = parsed.number;
  let id = suggestion;
  while (used.has(id)) {
    number += 1;
    id = `${parsed.kind}-${parsed.feature}-${String(number).padStart(3, "0")}`;
  }
  return { id, bumped: id !== suggestion };
}

function duplicateFormalIds() {
  const seen = new Set();
  const duplicated = new Set();
  state.cards.forEach((card) => {
    const id = String(card["建议ID"] || "").trim();
    if (!parseFormalId(id)) return;
    if (seen.has(id)) duplicated.add(id);
    seen.add(id);
  });
  return [...duplicated];
}

function parseFormalId(value) {
  const match = String(value || "").trim().match(/^(FAQ|UQ)-(F\d{2})-(\d{3})$/);
  if (!match) return null;
  return { kind: match[1], feature: match[2], number: Number(match[3]) };
}
