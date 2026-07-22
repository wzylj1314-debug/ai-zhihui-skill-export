const grid = document.getElementById("toolsGrid");

const text = {
  loading: "\u6b63\u5728\u8bfb\u53d6\u5de5\u5177\u72b6\u6001...",
  statusFailed: "\u72b6\u6001\u8bfb\u53d6\u5931\u8d25",
  empty: "\u6682\u65e0\u5de5\u5177\u3002",
  online: "\u8fd0\u884c\u4e2d",
  offline: "\u672a\u542f\u52a8",
  port: "\u672c\u673a\u7aef\u53e3",
  owner: "\u8d1f\u8d23\u89d2\u8272",
};

loadTools();

async function loadTools() {
  grid.innerHTML = `<div class="loading">${text.loading}</div>`;
  try {
    const response = await fetch("/api/tools");
    if (!response.ok) throw new Error(`${text.statusFailed}: ${response.status}`);
    const data = await response.json();
    renderTools(data.tools || []);
  } catch (error) {
    grid.innerHTML = `<div class="error">${escapeHtml(error.message)}</div>`;
  }
}

function renderTools(tools) {
  if (!tools.length) {
    grid.innerHTML = `<div class="empty">${text.empty}</div>`;
    return;
  }

  grid.innerHTML = tools
    .map((tool) => {
      const statusClass = tool.online ? "online" : "offline";
      const statusText = tool.online ? text.online : text.offline;
      const primaryUrl = resolveToolUrl(tool.primary_url);
      const secondaryUrl = resolveToolUrl(tool.secondary_url);
      return `
        <article class="tool-card" data-url="${escapeAttribute(primaryUrl)}" tabindex="0">
          <div class="card-head">
            <div>
              <h3>${escapeHtml(tool.title)}</h3>
            </div>
            <span class="status ${statusClass}">${statusText}</span>
          </div>
          <div class="tags">
            ${renderTags(tool)}
          </div>
          <div class="meta-list">
            <div><span>${text.owner}</span><strong>${escapeHtml(tool.owner)}</strong></div>
            <div><span>${text.port}</span><strong>${escapeHtml(String(tool.port))}</strong></div>
          </div>
          <a class="secondary-link" href="${escapeAttribute(secondaryUrl)}">${escapeHtml(tool.secondary_label)}</a>
        </article>
      `;
    })
    .join("");
  bindCards();
}

function renderTags(tool) {
  const parts = String(tool.subtitle || "")
    .split(/[,，、]/)
    .map((item) => item.trim())
    .filter(Boolean)
    .slice(0, 4);
  return parts.map((item) => `<span>${escapeHtml(item)}</span>`).join("");
}

function bindCards() {
  document.querySelectorAll(".tool-card").forEach((card) => {
    card.addEventListener("click", (event) => {
      if (event.target.closest("a")) return;
      window.location.href = card.dataset.url;
    });
    card.addEventListener("keydown", (event) => {
      if (event.key !== "Enter" && event.key !== " ") return;
      event.preventDefault();
      window.location.href = card.dataset.url;
    });
  });
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function escapeAttribute(value) {
  return escapeHtml(value).replaceAll("`", "&#096;");
}

function resolveToolUrl(url) {
  try {
    const target = new URL(url);
    const currentHost = window.location.hostname;
    if (target.hostname === "127.0.0.1" && currentHost && currentHost !== "127.0.0.1" && currentHost !== "localhost") {
      target.hostname = currentHost;
    }
    return target.toString();
  } catch {
    return url;
  }
}
