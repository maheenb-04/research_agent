function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str || "";
  return div.innerHTML;
}

function render(state) {
  const content = document.getElementById("content");

  if (!state || !state.status) {
    return; // leave the default empty-state message
  }

  if (state.status === "loading") {
    content.innerHTML = `
      <p class="topic-label">${escapeHtml(state.topic)}</p>
      <div class="loading">
        <div class="spinner"></div>
        <span>Researching...</span>
      </div>
    `;
    return;
  }

  if (state.status === "error") {
    content.innerHTML = `
      <p class="topic-label">${escapeHtml(state.topic)}</p>
      <div class="error-box">${escapeHtml(state.error)}</div>
    `;
    return;
  }

  if (state.status === "done" && state.data) {
    const d = state.data;
    let html = `<p class="topic-label">${escapeHtml(state.topic)}</p>`;

    if (d.sources_analysis && d.sources_analysis.length > 0) {
      html += `<div class="section-title">Sources</div>`;
      d.sources_analysis.slice(0, 5).forEach((s) => {
        html += `
          <div class="source-card">
            <a href="${escapeHtml(s.link)}" target="_blank">${escapeHtml(s.title)}</a>
            ${s.why_it_matters ? `<p>${escapeHtml(s.why_it_matters)}</p>` : ""}
          </div>
        `;
      });
    }

    if (d.insights && d.insights.length > 0) {
      html += `<div class="section-title">Insights</div><div>`;
      d.insights.slice(0, 4).forEach((item) => {
        const text = typeof item === "string" ? item : item.text;
        html += `<span class="tag-chip">${escapeHtml(text)}</span>`;
      });
      html += `</div>`;
    }

    html += `<a class="open-app-link" href="http://localhost:5173" target="_blank">Open full results in Research Agent →</a>`;

    content.innerHTML = html;
  }
}

chrome.storage.local.get(["status", "topic", "data", "error"], (state) => {
  render(state);
});

chrome.storage.onChanged.addListener((changes, area) => {
  if (area !== "local") return;
  chrome.storage.local.get(["status", "topic", "data", "error"], (state) => {
    render(state);
  });
});

function triggerSearch() {
  const input = document.getElementById("search-input");
  const topic = input.value.trim();
  if (!topic) return;
  chrome.runtime.sendMessage({ action: "search", topic });
  input.value = "";
}

document.getElementById("search-btn").addEventListener("click", triggerSearch);
document.getElementById("search-input").addEventListener("keydown", (e) => {
  if (e.key === "Enter") triggerSearch();
});
