/**
 * Renders every tab of the case detail page from demo data. One case is
 * rendered per page load (window.CASE_ID, set inline by the template).
 * Cases without hand-authored demo content (documents/summary/timeline/
 * chat/activity) fall back to plausible generic content so every case in
 * the list is fully explorable.
 */
document.addEventListener("DOMContentLoaded", () => {
  const caseObj = DEMO.cases.find((c) => c.id === window.CASE_ID) || DEMO.cases[0];

  const GENERIC_DOCS = [
    { id: "g1", name: "Case_filing.pdf", type: "pdf", pages: 6, uploadedAt: "2 weeks ago", ocr: "complete", size: "980 KB" },
    { id: "g2", name: "Client_statement.docx", type: "docx", pages: 3, uploadedAt: "2 weeks ago", ocr: "n/a", size: "210 KB" },
    { id: "g3", name: "Evidence_photo_01.jpg", type: "img", pages: 1, uploadedAt: "10 days ago", ocr: "complete", size: "3.2 MB" },
    { id: "g4", name: "Correspondence.pdf", type: "pdf", pages: 4, uploadedAt: "6 days ago", ocr: "complete", size: "540 KB" },
  ];
  let docs = DEMO.documents[caseObj.id] ? [...DEMO.documents[caseObj.id]] : GENERIC_DOCS.map((d) => ({ ...d }));

  function getSummary() {
    if (DEMO.summaries[caseObj.id]) return DEMO.summaries[caseObj.id];
    return {
      overview: `${caseObj.title} is a ${caseObj.type.toLowerCase()} matter before ${caseObj.court}. ${caseObj.description}`,
      evidence: [
        { label: "Primary filing reviewed", detail: `The initial filing establishes the core dispute between ${caseObj.client} and ${caseObj.opposite}.`, doc: `${docs[0]?.name} · p.1` },
        { label: "Supporting correspondence", detail: "Additional correspondence supports the sequence of events described in the filing.", doc: `${(docs[3] || docs[1] || docs[0])?.name} · p.2` },
      ],
      witnesses: [{ name: "Primary witness", summary: "Statement on file corroborates the general timeline of events." }],
      pending: ["Awaiting next hearing date confirmation", "Additional document review recommended"],
    };
  }

  function getTimeline() {
    if (DEMO.timelines[caseObj.id]) return DEMO.timelines[caseObj.id];
    const items = [
      { date: "Case opened", title: "Case filed", desc: `${caseObj.title} initiated at ${caseObj.court}.`, major: true, attach: docs[0]?.name },
      { date: "Ongoing", title: "Documents under review", desc: "Supporting documents uploaded and indexed for AI review.", major: false, attach: null },
    ];
    if (caseObj.hearingDate) items.push({ date: formatDateLong(caseObj.hearingDate), title: "Upcoming hearing", desc: `Hearing scheduled at ${caseObj.court}.`, major: true, attach: null });
    return items;
  }

  function getActivity() {
    if (DEMO.activity[caseObj.id]) return DEMO.activity[caseObj.id];
    return [
      { type: "case", text: "Case created", time: caseObj.updatedAt },
      { type: "upload", text: `${docs.length} documents uploaded`, time: caseObj.updatedAt },
    ];
  }

  function getChats() {
    if (DEMO.chats[caseObj.id]) return DEMO.chats[caseObj.id];
    return [{ role: "ai", text: `Hi Ananya — I've indexed ${docs.length} documents for ${caseObj.title}. Ask me anything about the case.`, sources: [] }];
  }

  function generateAiResponse(question) {
    const q = question.toLowerCase();
    if (q.includes("summar")) {
      return { text: getSummary().overview, sources: docs.slice(0, 2).map((d) => ({ doc: d.name, page: 1 })), confidence: 0.9 };
    }
    if (q.includes("evidence")) {
      return { text: `The strongest evidence includes ${docs[0]?.name}${docs[1] ? " and " + docs[1].name : ""}, which together establish the key facts of the case.`, sources: docs.slice(0, 2).map((d, i) => ({ doc: d.name, page: i + 1 })), confidence: 0.87 };
    }
    if (q.includes("witness")) {
      const wDocs = docs.filter((d) => d.name.toLowerCase().includes("witness"));
      const src = (wDocs.length ? wDocs : docs.slice(0, 1)).map((d) => ({ doc: d.name, page: 1 }));
      return { text: "Witness statements on file corroborate the general sequence of events described in the primary filing.", sources: src, confidence: 0.8 };
    }
    if (q.includes("fingerprint")) {
      return { text: "One reference to fingerprint evidence was found in the indexed documents; it does not confirm a conclusive match.", sources: docs.slice(0, 1).map((d) => ({ doc: d.name, page: 1 })), confidence: 0.74 };
    }
    if (q.includes("timeline") || q.includes("fir") || q.includes("before")) {
      return { text: "Based on the indexed documents, the earliest recorded event precedes the formal filing by several days. See the Timeline tab for the full sequence.", sources: docs.slice(0, 1).map((d) => ({ doc: d.name, page: 1 })), confidence: 0.82 };
    }
    if (q.includes("postmortem") || q.includes("explain")) {
      return { text: "The report describes findings consistent with the incident narrative on file. Key medical findings are cross-referenced against the FIR timeline.", sources: docs.slice(0, 1).map((d) => ({ doc: d.name, page: 3 })), confidence: 0.85 };
    }
    return { text: `Based on the ${docs.length} indexed documents for ${caseObj.title}, here's what's most relevant to your question. For a full breakdown, see the AI Case Summary tab.`, sources: docs.slice(0, 2).map((d, i) => ({ doc: d.name, page: i + 1 })), confidence: 0.7 };
  }

  const DIFF_DEMO = {
    left: [
      { t: "The Supplier shall deliver the goods within " }, { t: "15", type: "del" },
      { t: " business days of order confirmation. Payment terms are net " }, { t: "30", type: "del" },
      { t: " days from invoice date. This agreement may be terminated by either party with " }, { t: "7", type: "del" },
      { t: " days written notice." },
    ],
    right: [
      { t: "The Supplier shall deliver the goods within " }, { t: "45", type: "add" },
      { t: " business days of order confirmation. Payment terms are net " }, { t: "60", type: "add" },
      { t: " days from invoice date. This agreement may be terminated by either party with " }, { t: "30", type: "add" },
      { t: " days written notice. " }, { t: "A late delivery penalty of 2% per week shall apply.", type: "add" },
    ],
  };
  function buildDiffHtml(segments) {
    return segments.map((s) => {
      if (s.type === "add") return `<span class="diff-add">${escapeHtml(s.t)}</span>`;
      if (s.type === "del") return `<span class="diff-del">${escapeHtml(s.t)}</span>`;
      return escapeHtml(s.t);
    }).join("");
  }

  // ---- Hero ----
  function renderHero() {
    qs("#case-number").textContent = caseObj.number;
    qs("#case-title").textContent = caseObj.title;
    qs("#case-status-badge").innerHTML = statusBadge(caseObj.status);
    qs("#case-description").textContent = caseObj.description;
    qs("#case-client").textContent = caseObj.client;
    qs("#case-opposite").textContent = caseObj.opposite;
    qs("#case-court").textContent = caseObj.court;
    qs("#case-hearing").textContent = caseObj.hearingDate ? `${formatDateLong(caseObj.hearingDate)} · ${caseObj.hearingTime || ""}` : "Not scheduled";
    qs("#case-type").textContent = caseObj.type;
    document.title = caseObj.title;
  }

  // ---- Overview ----
  function fieldBlock(label, value) {
    return el("div", {}, [
      el("div", { class: "text-xs text-faint font-semibold", style: "text-transform:uppercase;letter-spacing:.04em;margin-bottom:3px;" }, [label]),
      el("div", { style: "font-size:13.5px;font-weight:600;" }, [value || "—"]),
    ]);
  }
  function renderOverview() {
    const box = qs("#overview-fields");
    box.innerHTML = "";
    [
      ["Case number", caseObj.number], ["Case title", caseObj.title], ["Case type", caseObj.type],
      ["Status", caseObj.status], ["Client name", caseObj.client], ["Opposite party", caseObj.opposite],
      ["Court name", caseObj.court], ["Judge", caseObj.judge || "—"],
      ["Hearing date", caseObj.hearingDate ? formatDateLong(caseObj.hearingDate) : "Not scheduled"],
    ].forEach(([l, v]) => box.appendChild(fieldBlock(l, v)));
    box.appendChild(el("div", { style: "grid-column: 1 / -1;" }, [fieldBlock("Description", caseObj.description)]));

    const act = qs("#overview-activity");
    act.innerHTML = "";
    getActivity().slice(0, 5).forEach((a) => act.appendChild(activityRow(a)));
  }

  function activityIcon(type) { return { ai: "sparkle", chat: "chat", upload: "upload", note: "edit", hearing: "calendar", case: "file" }[type] || "file"; }
  function activityRow(a) {
    return el("div", { class: "activity-item" }, [
      el("div", { class: "ic", html: icon(activityIcon(a.type)) }),
      el("div", { class: "body flex-1" }, [el("b", {}, [a.text])]),
      el("div", { class: "time" }, [a.time]),
    ]);
  }
  function renderActivity() {
    const list = qs("#activity-list");
    list.innerHTML = "";
    getActivity().forEach((a) => list.appendChild(activityRow(a)));
  }

  // ---- Documents ----
  function docCard(d) {
    const card = el("div", { class: "doc-card" });
    card.appendChild(el("div", { class: "top" }, [
      el("div", { class: `doc-icon ${docIconClass(d.type)}` }, [d.type.toUpperCase()]),
      d.ocr && d.ocr !== "n/a" ? (() => { const s = document.createElement("span"); s.innerHTML = statusBadge(d.ocr); return s.firstChild; })() : null,
    ]));
    card.appendChild(el("div", { class: "name" }, [d.name]));
    card.appendChild(el("div", { class: "meta" }, [`${d.pages} page${d.pages !== 1 ? "s" : ""} · ${d.size} · ${d.uploadedAt}`]));
    card.appendChild(el("div", { class: "flex gap-8" }, [
      el("button", { class: "btn btn-secondary btn-sm", html: icon("eye") + " Preview", onclick: (e) => { e.stopPropagation(); toast(`Previewing ${d.name}`); } }),
      el("button", { class: "btn btn-ghost btn-sm btn-icon-only", html: icon("download"), onclick: (e) => { e.stopPropagation(); toast(`Downloading ${d.name}`); } }),
      el("button", { class: "btn btn-ghost btn-sm btn-icon-only", html: icon("trash"), onclick: (e) => { e.stopPropagation(); docs = docs.filter((x) => x.id !== d.id); renderDocuments(); toast("Document deleted", "success"); } }),
    ]));
    return card;
  }
  function renderDocuments() {
    qs("#doc-count-label").textContent = `${docs.length} document${docs.length !== 1 ? "s" : ""}`;
    qs("#tab-count-documents").textContent = String(docs.length);
    const grid = qs("#doc-grid");
    grid.innerHTML = "";
    qs("#doc-empty").classList.toggle("hidden", docs.length > 0);
    docs.forEach((d) => grid.appendChild(docCard(d)));
    renderChatContext();
    renderCompare();
  }

  // ---- AI Assistant ----
  let chatState = [];
  function chatBubble(msg) {
    const wrap = el("div", { class: `msg ${msg.role === "user" ? "user" : "ai"}` });
    wrap.appendChild(el("div", { class: "bubble", html: escapeHtml(msg.text).replace(/\n/g, "<br/>") }));
    if (msg.sources && msg.sources.length) {
      const src = el("div", { class: "msg-sources" });
      msg.sources.forEach((s) => src.appendChild(el("span", { class: "source-chip" }, [`${s.doc} · p.${s.page}`])));
      wrap.appendChild(src);
    }
    if (typeof msg.confidence === "number") {
      wrap.appendChild(el("div", { class: "msg-confidence" }, [`Confidence score: ${Math.round(msg.confidence * 100)}%`]));
    }
    return wrap;
  }
  function renderChatContext() {
    const ctx = qs("#chat-context-docs");
    ctx.innerHTML = "";
    docs.forEach((d) => ctx.appendChild(el("div", { class: "ctx-doc" }, [
      el("span", { html: icon(d.type === "img" ? "image" : "file") }),
      el("span", { class: "flex-1" }, [d.name]),
      el("span", { class: "dim text-xs" }, [`${d.pages}p`]),
    ])));
  }
  function renderChat() {
    chatState = [...getChats()];
    const stream = qs("#chat-stream");
    stream.innerHTML = "";
    chatState.forEach((m) => stream.appendChild(chatBubble(m)));
    stream.scrollTop = stream.scrollHeight;
    renderChatContext();
  }
  function sendMessage(text) {
    if (!text || !text.trim()) return;
    const stream = qs("#chat-stream");
    const userMsg = { role: "user", text: text.trim() };
    chatState.push(userMsg);
    stream.appendChild(chatBubble(userMsg));
    qs("#chat-input").value = "";
    stream.scrollTop = stream.scrollHeight;

    const typing = el("div", { class: "msg ai" }, [el("div", { class: "bubble" }, [el("span", { class: "typing-dots" }, [el("i"), el("i"), el("i")])])]);
    stream.appendChild(typing);
    stream.scrollTop = stream.scrollHeight;

    setTimeout(() => {
      typing.remove();
      const resp = generateAiResponse(text);
      const aiMsg = { role: "ai", text: resp.text, sources: resp.sources, confidence: resp.confidence };
      chatState.push(aiMsg);
      stream.appendChild(chatBubble(aiMsg));
      stream.scrollTop = stream.scrollHeight;
    }, 850 + Math.random() * 500);
  }

  // ---- Summary ----
  function renderSummary() {
    const s = getSummary();
    const box = qs("#summary-content");
    box.innerHTML = "";
    const grid = el("div", { class: "summary-grid" });
    const left = el("div", {});
    left.appendChild(el("div", { class: "summary-section" }, [
      el("h4", { html: icon("sparkle") + " Case overview" }),
      el("p", {}, [s.overview]),
    ]));
    const evSec = el("div", { class: "summary-section" });
    evSec.appendChild(el("h4", {}, ["Important evidence"]));
    s.evidence.forEach((ev) => evSec.appendChild(el("div", { class: "evidence-item" }, [
      el("div", { class: "ic", html: icon("file") }),
      el("div", {}, [
        el("div", { style: "font-weight:600;font-size:13px;" }, [ev.label]),
        el("div", { class: "text-sm text-muted" }, [ev.detail]),
        el("div", { class: "text-xs", style: "color:var(--accent-ink);margin-top:2px;font-weight:600;" }, [ev.doc]),
      ]),
    ])));
    left.appendChild(evSec);
    const witSec = el("div", { class: "summary-section" });
    witSec.appendChild(el("h4", {}, ["Witness summary"]));
    const ul = el("ul", {});
    s.witnesses.forEach((w) => ul.appendChild(el("li", {}, [el("b", {}, [w.name + ": "]), w.summary])));
    witSec.appendChild(ul);
    left.appendChild(witSec);

    const right = el("div", { class: "card card-pad" });
    right.appendChild(el("h4", { style: "margin-bottom:10px;font-size:13px;" }, ["Pending issues"]));
    const pl = el("ul", {});
    s.pending.forEach((p) => pl.appendChild(el("li", {}, [p])));
    right.appendChild(pl);
    right.appendChild(el("div", { style: "height:1px;background:var(--border);margin:14px 0;" }));
    right.appendChild(el("button", { class: "btn btn-secondary btn-sm btn-block", onclick: () => toast("Summary refreshed with latest documents", "success") }, ["Regenerate summary"]));

    grid.appendChild(left);
    grid.appendChild(right);
    box.appendChild(grid);
  }

  // ---- Timeline ----
  function renderTimeline() {
    const list = qs("#timeline-list");
    list.innerHTML = "";
    getTimeline().forEach((item) => {
      const li = el("div", { class: `tl-item ${item.major ? "" : "minor"}` });
      li.appendChild(el("div", { class: "date" }, [item.date]));
      li.appendChild(el("div", { class: "title" }, [item.title]));
      li.appendChild(el("div", { class: "desc" }, [item.desc]));
      if (item.attach) li.appendChild(el("div", { class: "attach", html: icon("paperclip") + " " + escapeHtml(item.attach) }));
      list.appendChild(li);
    });
  }

  // ---- Compare ----
  function renderCompare() {
    const a = qs("#compare-doc-a"), b = qs("#compare-doc-b");
    a.innerHTML = ""; b.innerHTML = "";
    docs.forEach((d) => {
      a.appendChild(el("option", { value: d.id }, [d.name]));
      b.appendChild(el("option", { value: d.id }, [d.name]));
    });
    if (docs.length > 1) b.selectedIndex = 1;
    qs("#compare-grid").innerHTML = '<div class="empty" style="grid-column:1/-1;"><h4>Select two documents and click Compare</h4><p class="text-sm">AI will highlight added, removed, and materially changed text.</p></div>';
  }

  // ---- Notes ----
  let notesState = [];
  let editingNoteId = null;
  function noteCard(n) {
    const card = el("div", { class: `note-card ${n.ai ? "ai-note" : ""}` });
    card.appendChild(el("div", { class: "hd" }, [
      el("b", { style: "font-size:13px;" }, [(n.ai ? "✦ " : "") + n.title]),
      el("div", { class: "flex gap-6" }, [
        el("button", { class: "icon-btn btn-icon-only", style: "width:24px;height:24px;", html: icon("edit"), onclick: (e) => { e.stopPropagation(); openNoteEditor(n); } }),
        el("button", { class: "icon-btn btn-icon-only", style: "width:24px;height:24px;", html: icon("trash"), onclick: (e) => { e.stopPropagation(); notesState = notesState.filter((x) => x.id !== n.id); renderNotes(); toast("Note deleted", "success"); } }),
      ]),
    ]));
    card.appendChild(el("p", {}, [n.body]));
    card.appendChild(el("div", { class: "ft" }, [el("span", {}, [n.ai ? "AI generated" : "Private note"]), el("span", {}, [n.updatedAt])]));
    return card;
  }
  function renderNotes() {
    qs("#notes-count-label").textContent = `${notesState.length} note${notesState.length !== 1 ? "s" : ""}`;
    qs("#tab-count-notes").textContent = String(notesState.length);
    const grid = qs("#notes-grid");
    grid.innerHTML = "";
    if (!notesState.length) {
      grid.appendChild(el("div", { class: "empty", style: "grid-column:1/-1;" }, [
        el("div", { class: "ic", html: icon("edit") }),
        el("h4", {}, ["No notes yet"]),
        el("p", { class: "text-sm" }, ["Add a private note or generate one with AI."]),
      ]));
      return;
    }
    notesState.forEach((n) => grid.appendChild(noteCard(n)));
  }
  function openNoteEditor(n) {
    editingNoteId = n ? n.id : null;
    qs("#note-modal-title").textContent = n ? "Edit note" : "New note";
    qs("#note-title-input").value = n ? n.title : "";
    qs("#note-body-input").value = n ? n.body : "";
    openModal("note-modal");
  }

  // ---- Wire up static controls ----
  function setupControls() {
    qsa(".tab-btn").forEach((btn) => {
      btn.addEventListener("click", () => activateTab(btn.getAttribute("data-tab")));
    });
    function activateTab(name) {
      qsa(".tab-btn").forEach((t) => t.classList.toggle("active", t.getAttribute("data-tab") === name));
      qsa(".tab-panel").forEach((p) => p.classList.toggle("active", p.getAttribute("data-panel") === name));
      history.replaceState(null, "", "#" + name);
    }
    const hash = location.hash.replace("#", "");
    if (hash && qs(`.tab-btn[data-tab="${hash}"]`)) activateTab(hash);

    qs("#upload-doc-btn").addEventListener("click", () => qs("#dropzone").classList.toggle("hidden"));
    qs("#simulate-upload-btn").addEventListener("click", () => {
      const newDoc = { id: "up" + Date.now(), name: `New_upload_${docs.length + 1}.pdf`, type: "pdf", pages: 1, uploadedAt: "just now", ocr: "processing", size: "640 KB" };
      docs.unshift(newDoc);
      renderDocuments();
      toast("Uploading document…");
      setTimeout(() => { newDoc.ocr = "complete"; renderDocuments(); toast("Document processed — text extracted & embedded", "success"); }, 1800);
    });

    qs("#chat-send-btn").addEventListener("click", () => sendMessage(qs("#chat-input").value));
    qs("#chat-input").addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(qs("#chat-input").value); }
    });
    qsa(".suggestion-chip").forEach((chip) => chip.addEventListener("click", () => sendMessage(chip.getAttribute("data-q"))));

    qs("#regen-timeline-btn").addEventListener("click", () => toast("Timeline regenerated from latest documents", "success"));

    qs("#compare-run-btn").addEventListener("click", () => {
      const nameA = docs.find((d) => d.id === qs("#compare-doc-a").value)?.name || "Document A";
      const nameB = docs.find((d) => d.id === qs("#compare-doc-b").value)?.name || "Document B";
      const grid = qs("#compare-grid");
      grid.innerHTML = "";
      grid.appendChild(el("div", { class: "compare-doc" }, [el("div", { class: "hd" }, [nameA]), el("div", { class: "body", html: buildDiffHtml(DIFF_DEMO.left) })]));
      grid.appendChild(el("div", { class: "compare-doc" }, [el("div", { class: "hd" }, [nameB]), el("div", { class: "body", html: buildDiffHtml(DIFF_DEMO.right) })]));
      toast("Comparison complete — 3 changes highlighted", "success");
    });

    qs("#new-note-btn").addEventListener("click", () => openNoteEditor(null));
    qs("#save-note-btn").addEventListener("click", () => {
      const title = qs("#note-title-input").value.trim() || "Untitled note";
      const body = qs("#note-body-input").value.trim();
      if (editingNoteId) {
        const n = notesState.find((x) => x.id === editingNoteId);
        n.title = title; n.body = body; n.updatedAt = "just now";
      } else {
        notesState.unshift({ id: "n" + Date.now(), title, body, ai: false, updatedAt: "just now" });
      }
      closeModal("note-modal");
      renderNotes();
      toast("Note saved", "success");
    });

    qs("#edit-case-btn").addEventListener("click", () => {
      qs("#e-number").value = caseObj.number;
      qs("#e-title").value = caseObj.title;
      qs("#e-client").value = caseObj.client;
      qs("#e-opposite").value = caseObj.opposite;
      qs("#e-court").value = caseObj.court;
      qs("#e-hearing").value = caseObj.hearingDate || "";
      qs("#e-desc").value = caseObj.description;
      openModal("edit-case-modal");
    });
    qs("#save-case-edit-btn").addEventListener("click", () => {
      caseObj.number = qs("#e-number").value;
      caseObj.title = qs("#e-title").value;
      caseObj.client = qs("#e-client").value;
      caseObj.opposite = qs("#e-opposite").value;
      caseObj.court = qs("#e-court").value;
      caseObj.hearingDate = qs("#e-hearing").value || null;
      caseObj.description = qs("#e-desc").value;
      renderHero();
      renderOverview();
      closeModal("edit-case-modal");
      toast("Case updated", "success");
    });
  }

  renderHero();
  renderOverview();
  renderDocuments();
  renderChat();
  renderSummary();
  renderTimeline();
  notesState = DEMO.notes[caseObj.id] ? [...DEMO.notes[caseObj.id]] : [];
  renderNotes();
  renderActivity();
  setupControls();
});
