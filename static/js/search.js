/**
 * Real semantic search: embeds the query and hits Pinecone via the
 * chatbot's FastAPI service. Groq first classifies greeting vs case query
 * and extracts keywords used to highlight matches in snippets.
 *
 * Clicking a result opens the source PDF at the matched page and tries to
 * jump/search to the keyword. A highlight preview modal always shows the
 * matched text with keywords marked (browser PDF highlight support varies).
 */
document.addEventListener("DOMContentLoaded", () => {
  let scope = "all";
  let cases = [];
  let searchTimer = null;
  let lastKeywords = [];

  function highlightSnippet(snippet, words) {
    let out = escapeHtml(snippet || "");
    const unique = Array.from(new Set((words || []).filter(Boolean))).sort((a, b) => b.length - a.length);
    unique.forEach((w) => {
      const re = new RegExp(`(${w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")})`, "ig");
      out = out.replace(re, "<mark>$1</mark>");
    });
    return out;
  }

  function absoluteFileUrl(url) {
    if (!url) return null;
    if (/^https?:\/\//i.test(url)) return url;
    return window.location.origin + (url.startsWith("/") ? url : "/" + url);
  }

  function similarityPct(score) {
    // Pinecone cosine similarity is typically 0–1 for these embeddings.
    const pct = Math.max(0, Math.min(100, Math.round(Number(score || 0) * 100)));
    return pct;
  }

  function openPdfAtMatch(item, keywords) {
    const fileUrl = absoluteFileUrl(item.file_url);
    const page = Math.max(1, Number(item.page) || 1);
    const search = (keywords || []).slice(0, 4).join(" ");

    if (!fileUrl) {
      window.location.href = `/cases/${item.case_id}/`;
      return;
    }

    const isPdf = (item.file_type || "").toLowerCase() === "pdf" || /\.pdf($|\?)/i.test(fileUrl);
    let openUrl = fileUrl;
    if (isPdf) {
      // Chrome/Edge built-in PDF viewer supports page + search fragments.
      openUrl = `${fileUrl}#page=${page}&search=${encodeURIComponent(search || item.doc_name || "")}`;
    }
    window.open(openUrl, "_blank", "noopener");
  }

  function ensurePreviewModal() {
    let backdrop = qs("#search-preview-modal");
    if (backdrop) return backdrop;
    backdrop = el("div", { class: "modal-backdrop", id: "search-preview-modal" });
    backdrop.innerHTML = `
      <div class="modal" style="max-width:720px;">
        <div class="modal-head">
          <h3 id="sp-title">Matched passage</h3>
          <button class="icon-btn" data-close-modal type="button">✕</button>
        </div>
        <div class="modal-body">
          <div class="text-sm text-muted" id="sp-meta" style="margin-bottom:10px;"></div>
          <div class="card card-pad" style="max-height:340px;overflow:auto;line-height:1.7;font-size:13.5px;" id="sp-snippet"></div>
          <p class="text-xs text-muted" style="margin-top:10px;">
            Similarity % = how closely this passage’s meaning matches your query (Pinecone cosine score × 100).
            20–40% is common for useful semantic matches; higher is stronger.
          </p>
        </div>
        <div class="modal-foot">
          <button class="btn btn-secondary" type="button" id="sp-open-case">Open case</button>
          <button class="btn btn-primary" type="button" id="sp-open-pdf">Open PDF at page</button>
        </div>
      </div>`;
    document.body.appendChild(backdrop);
    backdrop.addEventListener("click", (e) => {
      if (e.target === backdrop || e.target.closest("[data-close-modal]")) {
        backdrop.classList.remove("open");
      }
    });
    return backdrop;
  }

  function showMatchPreview(item, keywords) {
    const backdrop = ensurePreviewModal();
    const pct = similarityPct(item.score);
    qs("#sp-title").textContent = item.doc_name || "Matched passage";
    qs("#sp-meta").textContent = `${item.case_title} · page ${item.page || "?"} · similarity ${pct}%`;
    qs("#sp-snippet").innerHTML = highlightSnippet(item.text, keywords);

    qs("#sp-open-case").onclick = () => {
      window.location.href = `/cases/${item.case_id}/`;
    };
    qs("#sp-open-pdf").onclick = () => {
      openPdfAtMatch(item, keywords);
    };

    backdrop.classList.add("open");
  }

  function resultCard(item, words) {
    const pct = similarityPct(item.score);
    const card = el("div", {
      class: "result-card",
      style: "cursor:pointer;",
      title: "View matched passage",
      onclick: () => showMatchPreview(item, words),
    });
    card.appendChild(el("div", { class: "top-row" }, [
      el("div", {}, [
        el("div", { class: "title" }, [item.doc_name]),
        el("div", { class: "case-tag" }, [item.case_title, ` · page ${item.page}`]),
      ]),
      el("div", {
        class: "relevance",
        title: "Semantic similarity to your query (not keyword count). Higher = closer meaning.",
      }, [
        el("div", { class: "bar" }, [el("i", { style: `width:${pct}%` })]),
        el("span", { class: "pct" }, [`${pct}%`]),
      ]),
    ]));
    card.appendChild(el("div", { class: "snippet", html: "…" + highlightSnippet(item.text, words) + "…" }));
    card.appendChild(el("div", { class: "foot" }, [
      el("span", { class: "text-xs text-faint" }, [`Similarity ${pct}% · page ${item.page || "?"}`]),
      el("span", { class: "text-xs", style: "color:var(--accent);font-weight:600;" }, ["View match →"]),
    ]));
    return card;
  }

  function renderGreeting(reply, query) {
    const box = qs("#search-results");
    const meta = qs("#search-meta");
    box.innerHTML = "";
    meta.textContent = `Not a case search · "${query}"`;
    box.appendChild(el("div", { class: "empty" }, [
      el("h4", {}, ["Please ask a case-related query"]),
      el("p", { class: "text-sm" }, [reply || "Try searching for evidence, witnesses, hearings, contracts, or FIR details."]),
    ]));
  }

  function renderResults(payload, query) {
    const box = qs("#search-results");
    const meta = qs("#search-meta");
    box.innerHTML = "";

    if (!query) {
      meta.textContent = "";
      return;
    }

    if (payload && payload.query_type === "greeting") {
      renderGreeting(payload.reply, query);
      return;
    }

    const list = (payload && payload.results) || (Array.isArray(payload) ? payload : []);
    const keywords = (payload && payload.keywords) || [];
    lastKeywords = keywords;

    if (!list.length) {
      meta.textContent = `No results for "${query}"`;
      box.appendChild(el("div", { class: "empty" }, [
        el("h4", {}, ["No matches found"]),
        el("p", { class: "text-sm" }, ["Try a broader phrase describing what you're looking for, or check that your documents have finished indexing."]),
      ]));
      return;
    }

    const kwLabel = keywords.length ? ` · keywords: ${keywords.join(", ")}` : "";
    meta.textContent = `${list.length} result${list.length !== 1 ? "s" : ""} for "${query}" · ranked by meaning similarity${kwLabel}`;
    list.forEach((item) => box.appendChild(resultCard(item, keywords)));
  }

  function renderLoading() {
    const box = qs("#search-results");
    qs("#search-meta").textContent = "Analyzing query & searching…";
    box.innerHTML = "";
    box.appendChild(el("div", { class: "empty" }, [el("h4", {}, ["Searching indexed documents…"])]));
  }

  async function runSearch(query) {
    const q = query.trim();
    if (!q) { renderResults(null, q); return; }
    renderLoading();
    const caseId = scope === "all" ? null : Number(scope);
    try {
      const res = await fetch(window.SEMANTIC_SEARCH_API_URL, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json", "X-CSRFToken": getCookie("csrftoken") },
        body: JSON.stringify({ query: q, case_id: caseId }),
      });
      const result = await res.json();
      if (!res.ok || !result.success) {
        qs("#search-meta").textContent = result.detail || result.message || "Search failed";
        qs("#search-results").innerHTML = "";
        return;
      }
      renderResults(result.data || {}, q);
    } catch (err) {
      qs("#search-meta").textContent = "Could not reach the search service — check that the chatbot service is running.";
      qs("#search-results").innerHTML = "";
    }
  }

  function scheduleSearch(query) {
    if (searchTimer) clearTimeout(searchTimer);
    searchTimer = setTimeout(() => runSearch(query), 450);
  }

  function renderScopeChips() {
    const box = qs("#search-scope");
    box.innerHTML = "";
    box.appendChild(el("button", { class: "filter-chip active", "data-scope": "all", onclick: () => selectScope("all") }, ["All cases"]));
    cases.forEach((c) => {
      box.appendChild(el("button", { class: "filter-chip", "data-scope": String(c.id), onclick: () => selectScope(String(c.id)) }, [c.case_title]));
    });
  }

  function selectScope(value) {
    scope = value;
    qsa("#search-scope [data-scope]").forEach((c) => c.classList.toggle("active", c.getAttribute("data-scope") === value));
    if (qs("#search-input").value.trim()) runSearch(qs("#search-input").value);
  }

  async function loadCases() {
    try {
      const res = await fetch(`${window.CASES_LIST_API_URL}?page_size=100`, { headers: { Accept: "application/json" } });
      const result = await res.json();
      if (res.ok && result.success) {
        cases = result.data.cases || [];
        renderScopeChips();
      }
    } catch (err) {
      // Scope stays "All cases" only — non-critical.
    }
  }

  qs("#search-go-btn").addEventListener("click", () => runSearch(qs("#search-input").value));
  qs("#search-input").addEventListener("input", () => scheduleSearch(qs("#search-input").value));
  qs("#search-input").addEventListener("keydown", (e) => { if (e.key === "Enter") runSearch(qs("#search-input").value); });
  qsa("[data-example]").forEach((chip) => chip.addEventListener("click", () => {
    qs("#search-input").value = chip.getAttribute("data-example");
    runSearch(chip.getAttribute("data-example"));
  }));

  loadCases();
});
