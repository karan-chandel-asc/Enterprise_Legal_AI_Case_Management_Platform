document.addEventListener("DOMContentLoaded", () => {
  let scope = "all";

  function highlightSnippet(snippet, words) {
    let out = escapeHtml(snippet);
    words.forEach((w) => {
      if (!w) return;
      const re = new RegExp(`(${w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")})`, "ig");
      out = out.replace(re, "<mark>$1</mark>");
    });
    return out;
  }

  function resultCard(item, words) {
    const card = el("div", { class: "result-card", onclick: () => (window.location.href = `/cases/${item.caseId}/`) });
    card.appendChild(el("div", { class: "top-row" }, [
      el("div", {}, [
        el("div", { class: "title" }, [item.doc]),
        el("div", { class: "case-tag" }, [item.caseTitle, ` · page ${item.page}`]),
      ]),
      el("div", { class: "relevance" }, [
        el("div", { class: "bar" }, [el("i", { style: `width:${Math.round(item.adjScore * 100)}%` })]),
        el("span", { class: "pct" }, [`${Math.round(item.adjScore * 100)}%`]),
      ]),
    ]));
    card.appendChild(el("div", { class: "snippet", html: "…" + highlightSnippet(item.snippet, words) + "…" }));
    card.appendChild(el("div", { class: "foot" }, [
      el("span", { class: "text-xs text-faint" }, ["Semantic match"]),
      el("span", { class: "text-xs", style: "color:var(--accent);font-weight:600;" }, ["Open in case →"]),
    ]));
    return card;
  }

  function renderResults(list, query) {
    const box = qs("#search-results");
    const meta = qs("#search-meta");
    box.innerHTML = "";
    if (!query) {
      meta.textContent = "";
      return;
    }
    if (!list.length) {
      meta.textContent = `No results for "${query}"`;
      box.appendChild(el("div", { class: "empty" }, [el("h4", {}, ["No matches found"]), el("p", { class: "text-sm" }, ["Try a broader phrase describing what you're looking for."])]));
      return;
    }
    meta.textContent = `${list.length} result${list.length !== 1 ? "s" : ""} for "${query}" · ranked by semantic relevance`;
    const words = query.toLowerCase().split(/\s+/).filter((w) => w.length > 2);
    list.forEach((item) => box.appendChild(resultCard(item, words)));
  }

  function runSearch(query) {
    const q = query.trim();
    const pool = DEMO.searchIndex.filter((i) => scope === "all" || i.caseId === scope);
    if (!q) { renderResults([], q); return; }
    const words = q.toLowerCase().split(/\s+/).filter((w) => w.length > 2);
    const scored = pool.map((item) => {
      const hay = `${item.snippet} ${item.caseTitle} ${item.doc}`.toLowerCase();
      const matchCount = words.filter((w) => hay.includes(w)).length;
      const adjScore = item.score * (0.45 + 0.55 * Math.min(1, matchCount / Math.max(1, words.length)));
      return { ...item, adjScore };
    }).sort((a, b) => b.adjScore - a.adjScore);
    renderResults(scored, q);
  }

  qs("#search-go-btn").addEventListener("click", () => runSearch(qs("#search-input").value));
  qs("#search-input").addEventListener("keydown", (e) => { if (e.key === "Enter") runSearch(qs("#search-input").value); });
  qsa("[data-example]").forEach((chip) => chip.addEventListener("click", () => {
    qs("#search-input").value = chip.getAttribute("data-example");
    runSearch(chip.getAttribute("data-example"));
  }));
  qsa("[data-scope]").forEach((chip) => chip.addEventListener("click", () => {
    qsa("[data-scope]").forEach((c) => c.classList.remove("active"));
    chip.classList.add("active");
    scope = chip.getAttribute("data-scope");
    if (qs("#search-input").value.trim()) runSearch(qs("#search-input").value);
  }));

  // seed with an initial example so the page never looks empty on first load
  qs("#search-input").value = "Find documents discussing the murder weapon";
  runSearch(qs("#search-input").value);
});
