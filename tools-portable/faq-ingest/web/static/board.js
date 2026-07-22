const state = {
  rows: [],
  allowedFiles: [],
  dateRange: { from: "", to: "", pickerMonth: null },
};

const boardRows = document.querySelector("#boardRows");
const boardMessage = document.querySelector("#boardMessage");
const statsGrid = document.querySelector("#statsGrid");
const fileFilter = document.querySelector("#fileFilter");
const selectAllRows = document.querySelector("#selectAllRows");
const dateRangeText = document.querySelector("#dateRangeText");
const dateRangePicker = document.querySelector("#dateRangePicker");
const fromDateInput = document.querySelector("#fromDate");
const toDateInput = document.querySelector("#toDate");

init();

function init() {
  initDateRange();
  bindEvents();
  loadBoard();
}

function bindEvents() {
  document.querySelector("#refreshBoardBtn")?.addEventListener("click", loadBoard);
  document.querySelector("#batchCommitBtn")?.addEventListener("click", batchCommit);
  document.querySelector("#batchDeleteBtn")?.addEventListener("click", batchDelete);
  selectAllRows?.addEventListener("change", () => {
    document.querySelectorAll("[data-row-check]").forEach((item) => {
      item.checked = selectAllRows.checked && !item.disabled;
    });
  });
  dateRangeText?.addEventListener("click", (event) => {
    event.stopPropagation();
    renderDateRangePicker();
    dateRangePicker?.classList.remove("hidden");
  });
  dateRangeText?.addEventListener("focus", () => {
    renderDateRangePicker();
    dateRangePicker?.classList.remove("hidden");
  });
  document.addEventListener("click", (event) => {
    if (!dateRangePicker || !dateRangeText) return;
    if (dateRangePicker.contains(event.target) || dateRangeText.contains(event.target)) return;
    dateRangePicker.classList.add("hidden");
  });
}

function initDateRange() {
  if (!dateRangeText || !fromDateInput || !toDateInput) return;
  const today = stripTime(new Date());
  const from = addDays(today, -6);
  state.dateRange.from = formatIso(from);
  state.dateRange.to = formatIso(today);
  state.dateRange.pickerMonth = startOfMonth(from);
  syncDateInputs();
}

function syncDateInputs() {
  if (!fromDateInput || !toDateInput || !dateRangeText) return;
  fromDateInput.value = state.dateRange.from || "";
  toDateInput.value = state.dateRange.to || "";
  dateRangeText.value = state.dateRange.from && state.dateRange.to
    ? `${state.dateRange.from} 至 ${state.dateRange.to}`
    : state.dateRange.from || "";
}

function renderDateRangePicker() {
  if (!dateRangePicker) return;
  const leftMonth = state.dateRange.pickerMonth || startOfMonth(new Date());
  const rightMonth = addMonths(leftMonth, 1);
  dateRangePicker.innerHTML = `
    <div class="range-cal-head">
      <button type="button" class="cal-nav" data-cal-prev title="上个月">‹</button>
      <button type="button" class="cal-nav" data-cal-next title="下个月">›</button>
    </div>
    <div class="range-cal-grid">
      ${renderMonth(leftMonth)}
      ${renderMonth(rightMonth)}
    </div>
    <div class="range-cal-actions">
      <button type="button" class="secondary small" data-cal-clear>清空</button>
      <button type="button" class="small" data-cal-apply>查询</button>
    </div>
  `;
  dateRangePicker.querySelector("[data-cal-prev]")?.addEventListener("click", (event) => {
    event.stopPropagation();
    state.dateRange.pickerMonth = addMonths(leftMonth, -1);
    renderDateRangePicker();
  });
  dateRangePicker.querySelector("[data-cal-next]")?.addEventListener("click", (event) => {
    event.stopPropagation();
    state.dateRange.pickerMonth = addMonths(leftMonth, 1);
    renderDateRangePicker();
  });
  dateRangePicker.querySelector("[data-cal-clear]")?.addEventListener("click", (event) => {
    event.stopPropagation();
    state.dateRange.from = "";
    state.dateRange.to = "";
    syncDateInputs();
    renderDateRangePicker();
  });
  dateRangePicker.querySelector("[data-cal-apply]")?.addEventListener("click", async (event) => {
    event.stopPropagation();
    dateRangePicker.classList.add("hidden");
    await loadBoard();
  });
  dateRangePicker.querySelectorAll("[data-date]").forEach((button) => {
    button.addEventListener("click", async (event) => {
      event.stopPropagation();
      chooseDate(button.dataset.date);
      syncDateInputs();
      renderDateRangePicker();
      if (state.dateRange.from && state.dateRange.to) {
        dateRangePicker.classList.add("hidden");
        await loadBoard();
      }
    });
  });
}

function renderMonth(monthDate) {
  const monthStart = startOfMonth(monthDate);
  const gridStart = addDays(monthStart, -monthStart.getDay());
  const title = `${monthStart.getFullYear()} 年 ${monthStart.getMonth() + 1} 月`;
  const weekdays = ["日", "一", "二", "三", "四", "五", "六"];
  const days = [];
  for (let index = 0; index < 42; index += 1) {
    const day = addDays(gridStart, index);
    const iso = formatIso(day);
    const inMonth = day.getMonth() === monthStart.getMonth();
    const selected = iso === state.dateRange.from || iso === state.dateRange.to;
    const inRange = isInSelectedRange(iso);
    const classes = [
      "cal-day",
      inMonth ? "" : "muted-day",
      selected ? "selected-day" : "",
      inRange ? "range-day" : "",
    ].filter(Boolean).join(" ");
    days.push(`<button type="button" class="${classes}" data-date="${iso}">${day.getDate()}</button>`);
  }
  return `
    <section class="range-month">
      <h3>${title}</h3>
      <div class="cal-weekdays">${weekdays.map((day) => `<span>${day}</span>`).join("")}</div>
      <div class="cal-days">${days.join("")}</div>
    </section>
  `;
}

function chooseDate(iso) {
  const from = state.dateRange.from;
  const to = state.dateRange.to;
  if (!from || (from && to)) {
    state.dateRange.from = iso;
    state.dateRange.to = "";
    state.dateRange.pickerMonth = startOfMonth(parseIso(iso));
    return;
  }
  if (iso < from) {
    state.dateRange.to = from;
    state.dateRange.from = iso;
  } else {
    state.dateRange.to = iso;
  }
}

function isInSelectedRange(iso) {
  const { from, to } = state.dateRange;
  return Boolean(from && to && iso > from && iso < to);
}

async function loadBoard() {
  try {
    const params = new URLSearchParams();
    const from = document.querySelector("#fromDate").value;
    const to = document.querySelector("#toDate").value;
    const feature = document.querySelector("#featureFilter").value.trim();
    const file = fileFilter.value;
    const commitState = document.querySelector("#commitStateFilter").value;
    const keyword = document.querySelector("#keywordFilter").value.trim();
    if (from) params.set("from", from);
    if (to) params.set("to", to);
    if (feature) params.set("function", feature);
    if (file) params.set("file", file);
    if (commitState) params.set("commit_state", commitState);
    if (keyword) params.set("q", keyword);
    const data = await api(`/api/board?${params.toString()}`);
    state.rows = data.rows || [];
    state.allowedFiles = data.allowed_files || [];
    renderFileFilter();
    renderStats(data.stats || {});
    renderRows();
    boardMessage.textContent = `共 ${state.rows.length} 条。`;
  } catch (error) {
    boardMessage.textContent = error.message;
  }
}

function renderFileFilter() {
  const current = fileFilter.value;
  const options = ['<option value="">全部</option>'];
  state.allowedFiles.forEach((file) => {
    options.push(`<option value="${escapeAttr(file)}">${escapeHtml(file)}</option>`);
  });
  fileFilter.innerHTML = options.join("");
  fileFilter.value = state.allowedFiles.includes(current) ? current : "";
}

function renderStats(stats) {
  const distribution = (stats["按功能分布"] || []).slice(0, 5).map(([name, count]) => `${name} ${count}`).join(" / ") || "暂无";
  const duplicates = (stats["疑似重复top"] || []).slice(0, 3).map(([name, count]) => `${name} ${count}`).join(" / ") || "暂无";
  statsGrid.innerHTML = `
    ${statCard("近7天通过", stats["近7天通过数"] || 0)}
    ${statCard("待入库", stats["待入库数"] || 0)}
    ${statCard("转人工占比", `${Math.round((stats["转人工占比"] || 0) * 100)}%`)}
    ${statCard("功能分布", distribution)}
    ${statCard("疑似重复", duplicates)}
  `;
}

function statCard(label, value) {
  return `<article class="stat-card"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></article>`;
}

function renderRows() {
  if (!state.rows.length) {
    boardRows.innerHTML = '<tr><td colspan="8" class="empty">没有符合条件的台账记录。</td></tr>';
    return;
  }
  boardRows.innerHTML = state.rows.map((row) => {
    const canCommit = commitAllowed(row);
    const disabledReason = commitReason(row);
    const canDelete = deleteAllowed(row);
    const deleteDisabledReason = deleteReason(row);
    return `
      <tr>
        <td><input type="checkbox" data-row-check="${escapeAttr(row["台账ID"])}" ${canCommit || canDelete ? "" : "disabled"} /></td>
        <td>${escapeHtml(row["草稿日期"])}</td>
        <td>
          <details>
            <summary>${escapeHtml(row["问题"])}</summary>
            <div class="answer-preview">${escapeHtml(row["回答"])}</div>
          </details>
        </td>
        <td>${escapeHtml(row["适用功能"])}</td>
        <td>${escapeHtml(row["归属文件"])}</td>
        <td>${escapeHtml(row["建议ID"])}</td>
        <td>${escapeHtml(displayCommitState(row))}</td>
        <td>
          <div class="row-actions">
            <button type="button" data-commit-one="${escapeAttr(row["台账ID"])}" ${canCommit ? "" : "disabled title=\"" + escapeAttr(disabledReason) + "\""}>入库</button>
            <button class="link-danger row-delete" type="button" data-delete-one="${escapeAttr(row["台账ID"])}" ${canDelete ? "" : "disabled title=\"" + escapeAttr(deleteDisabledReason) + "\""}>删除</button>
          </div>
          ${canCommit ? "" : `<div class="muted small-note">${escapeHtml(disabledReason)}</div>`}
          ${canDelete ? "" : `<div class="muted small-note">${escapeHtml(deleteDisabledReason)}</div>`}
        </td>
      </tr>
    `;
  }).join("");
  document.querySelectorAll("[data-commit-one]").forEach((button) => {
    button.addEventListener("click", () => commitIds([button.dataset.commitOne]));
  });
  document.querySelectorAll("[data-delete-one]").forEach((button) => {
    button.addEventListener("click", () => deleteIds([button.dataset.deleteOne]));
  });
}

function commitAllowed(row) {
  return !commitReason(row);
}

function commitReason(row) {
  if (row["状态"] !== "通过") return "状态不是通过";
  if (!state.allowedFiles.includes(row["归属文件"])) {
    return "不可一键入库：归属文件不在 FAQ 入库白名单，请先改为 09 或 10，或人工整理到专题文档。";
  }
  if (row["入库状态"] === "已入库") return "已入库";
  if (!/^(FAQ|UQ)-F\d{2}-\d{3}$/.test(row["建议ID"] || "")) return "正式ID格式不正确";
  if (row["归属文件"].startsWith("09_") && !row["建议ID"].startsWith("FAQ-")) return "09 文件需要 FAQ- ID";
  if (row["归属文件"].startsWith("10_") && !row["建议ID"].startsWith("UQ-")) return "10 文件需要 UQ- ID";
  if (row["是否需要转人工"] === "是") return "需要转人工";
  return "";
}

function deleteAllowed(row) {
  return !deleteReason(row);
}

function deleteReason(row) {
  if (row["入库状态"] === "已入库") return "已入库记录不能永久删除";
  return "";
}

function displayCommitState(row) {
  if (row["入库状态"] === "已入库" && row["入库时间"]) return `已入库 (${row["入库时间"]})`;
  return row["入库状态"] || "待入库";
}

async function batchCommit() {
  const checkedIds = [...document.querySelectorAll("[data-row-check]:checked")].map((item) => item.dataset.rowCheck);
  const ids = checkedIds.filter((id) => {
    const row = state.rows.find((item) => item["台账ID"] === id);
    return row && commitAllowed(row);
  });
  if (!ids.length) {
    boardMessage.textContent = "请选择可入库的记录。";
    return;
  }
  await commitIds(ids);
}

async function batchDelete() {
  const checkedIds = [...document.querySelectorAll("[data-row-check]:checked")].map((item) => item.dataset.rowCheck);
  const ids = checkedIds.filter((id) => {
    const row = state.rows.find((item) => item["台账ID"] === id);
    return row && deleteAllowed(row);
  });
  if (!ids.length) {
    boardMessage.textContent = "请选择可删除的记录。";
    return;
  }
  await deleteIds(ids);
}

async function commitIds(ids) {
  if (!confirm(`确定入库 ${ids.length} 条吗？会写入 09/10 知识库文件。`)) return;
  try {
    const result = await api("/api/board/commit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ids }),
    });
    const summary = result.results.map((item) => `${item.id}: ${item.ok ? "成功" : item.reason}`).join("；");
    boardMessage.textContent = summary;
    await loadBoard();
  } catch (error) {
    boardMessage.textContent = error.message;
  }
}

async function deleteIds(ids) {
  if (!confirm(`确定删除 ${ids.length} 条记录吗？会从台账历史和草稿残留中移除，删除前会自动备份。`)) return;
  if (!confirm("再次确认：删除后只能从 _trash 备份手动找回。继续吗？")) return;
  try {
    const result = await api("/api/board/delete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ids }),
    });
    const summary = result.results.map((item) => `${item.id}: ${item.ok ? "已删除" : item.reason}`).join("；");
    const backup = result.backup ? ` 备份：${result.backup}` : "";
    boardMessage.textContent = `${summary}${backup}`;
    await loadBoard();
  } catch (error) {
    boardMessage.textContent = error.message;
  }
}

async function api(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) {
    let detail = await response.text();
    try {
      detail = JSON.parse(detail).detail || detail;
    } catch (_error) {
      // Keep raw response.
    }
    throw new Error(detail);
  }
  return response.json();
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char]));
}

function escapeAttr(value) {
  return escapeHtml(value).replace(/\n/g, " ");
}

function stripTime(date) {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate());
}

function startOfMonth(date) {
  return new Date(date.getFullYear(), date.getMonth(), 1);
}

function addDays(date, amount) {
  const result = new Date(date);
  result.setDate(result.getDate() + amount);
  return result;
}

function addMonths(date, amount) {
  const result = new Date(date);
  result.setMonth(result.getMonth() + amount);
  return startOfMonth(result);
}

function parseIso(value) {
  const [year, month, day] = value.split("-").map(Number);
  return new Date(year, month - 1, day || 1);
}

function formatIso(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}
