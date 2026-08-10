/**
 * Renders the case detail page from real backend data (overview, edit,
 * delete, documents, notes, activity). The AI Assistant tab is wired to the
 * real LangGraph RAG chatbot (chatbot/fastapi_app + chatbot/services/rag_graph.py).
 */
document.addEventListener("DOMContentLoaded", () => {
  let caseObj = null;
  let docs = [];
  let notesState = [];
  let activityState = [];
  let editingNoteId = null;

  function mapCase(c) {
    return {
      id: c.id,
      number: c.case_id,
      title: c.case_title,
      type: c.case_type ? c.case_type[0].toUpperCase() + c.case_type.slice(1) : "—",
      typeRaw: c.case_type,
      status: c.case_status,
      client: c.client_name,
      opposite: c.opposing_party_name,
      court: c.court_name,
      hearingDate: c.hearing_date,
      description: c.case_description,
      documentCount: c.document_count,
      noteCount: c.note_count,
    };
  }

  function mapDocument(d) {
    return {
      id: d.id,
      name: d.document_name,
      type: d.file_type || "file",
      uploadedAt: d.uploaded_at,
      size: d.file_size,
      url: d.file_url,
      embeddingStatus: d.embedding_status || "pending",
      chunkCount: d.chunk_count || 0,
    };
  }

  function mapNote(n) {
    return { id: n.id, title: n.note_title, body: n.note_content, ai: !!n.ai, updatedAt: n.note_updated_at };
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
    qs("#case-hearing").textContent = caseObj.hearingDate || "Not scheduled";
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
      ["Court name", caseObj.court], ["Hearing date", caseObj.hearingDate || "Not scheduled"],
    ].forEach(([l, v]) => box.appendChild(fieldBlock(l, v)));
    box.appendChild(el("div", { style: "grid-column: 1 / -1;" }, [fieldBlock("Description", caseObj.description)]));

    const act = qs("#overview-activity");
    act.innerHTML = "";
    activityState.slice(0, 5).forEach((a) => act.appendChild(activityRow(a)));
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
    if (!activityState.length) {
      list.appendChild(el("div", { class: "text-sm text-muted" }, ["No activity recorded yet."]));
      return;
    }
    activityState.forEach((a) => list.appendChild(activityRow(a)));
  }

  async function loadActivity() {
    try {
      const res = await fetch(window.CASE_ACTIVITY_API_URL, { headers: { Accept: "application/json" } });
      const result = await res.json();
      if (res.ok && result.success) {
        activityState = result.data || [];
        renderOverview();
        renderActivity();
      }
    } catch (err) {
      // Non-critical — leave activity empty on failure.
    }
  }

  // ---- Documents ----
  function embeddingBadge(d) {
    const map = {
      pending: { label: "Queued for indexing", cls: "badge-neutral" },
      processing: { label: "Indexing…", cls: "badge-info" },
      completed: { label: `Indexed · ${d.chunkCount} chunk${d.chunkCount === 1 ? "" : "s"}`, cls: "badge-success" },
      failed: { label: "Indexing failed", cls: "badge-danger" },
    };
    const info = map[d.embeddingStatus] || map.pending;
    return el("span", { class: `badge ${info.cls}` }, [info.label]);
  }
  function docCard(d) {
    const card = el("div", { class: "doc-card" });
    card.appendChild(el("div", { class: "top" }, [
      el("div", { class: `doc-icon ${docIconClass(d.type)}` }, [d.type.toUpperCase()]),
      embeddingBadge(d),
    ]));
    card.appendChild(el("div", { class: "name" }, [d.name]));
    card.appendChild(el("div", { class: "meta" }, [`${d.size} · ${d.uploadedAt}`]));
    card.appendChild(el("div", { class: "flex gap-8" }, [
      el("button", { class: "btn btn-secondary btn-sm", html: icon("eye") + " Preview", onclick: (e) => { e.stopPropagation(); d.url ? window.open(d.url, "_blank") : toast("No file attached", "error"); } }),
      el("button", { class: "btn btn-ghost btn-sm btn-icon-only", html: icon("download"), onclick: (e) => { e.stopPropagation(); d.url ? window.open(d.url, "_blank") : toast("No file attached", "error"); } }),
      el("button", { class: "btn btn-ghost btn-sm btn-icon-only", html: icon("trash"), onclick: (e) => { e.stopPropagation(); deleteDocument(d.id); } }),
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
    // Refresh the empty-state greeting so it reflects live document counts
    // (loadCase renders chat before documents have been fetched).
    if (!chatState.length) renderChatStream();
  }

  let embedPollTimer = null;

  async function loadDocuments() {
    try {
      const res = await fetch(window.CASE_DOCUMENTS_API_URL, { headers: { Accept: "application/json" } });
      const result = await res.json();
      if (!res.ok || !result.success) {
        toast(result.message || "Could not load documents", "error");
        return;
      }
      docs = (result.data || []).map(mapDocument);
      renderDocuments();
      // scheduleEmbeddingPoll();
    } catch (err) {
      toast("Could not load documents", "error");
    }
  }

  // The Celery worker indexes documents in the background, so keep polling
  // every few seconds while anything is still queued/processing and stop
  // once every document has settled into completed/failed.
  // function scheduleEmbeddingPoll() {
  //   if (embedPollTimer) return;
  //   const stillWorking = docs.some((d) => d.embeddingStatus === "pending" || d.embeddingStatus === "processing");
  //   if (!stillWorking) return;
  //   embedPollTimer = setTimeout(async () => {
  //     embedPollTimer = null;
  //     await loadDocuments();
  //   }, 4000);
  // }

  async function uploadDocument(file) {
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);
    toast("Uploading document…");
    try {
      const res = await fetch(window.DOCUMENT_UPLOAD_API_URL, {
        method: "POST",
        headers: { "X-CSRFToken": getCookie("csrftoken") },
        body: formData,
      });
      const result = await res.json();
      if (!res.ok || !result.success) {
        toast(result.message || "Could not upload document", "error");
        return;
      }
      toast(result.message || "Document uploaded — indexing is running in the background", "success");
      await loadDocuments();
      loadActivity();
    } catch (err) {
      toast("Could not upload document", "error");
    }
  }

  async function deleteDocument(id) {
    try {
      const url = window.CASE_DOCUMENT_DETAIL_API_URL_TEMPLATE.replace("0", id);
      const res = await fetch(url, { method: "DELETE", headers: jsonHeaders() });
      const result = await res.json();
      if (!res.ok || !result.success) {
        toast(result.message || "Could not delete document", "error");
        return;
      }
      // Optimistic UI — Celery finishes file/index cleanup in the background.
      docs = docs.filter((d) => d.id !== id);
      renderDocuments();
      toast(result.message || "Document deletion started in the background", "success");
      loadActivity();
      // Refresh shortly so a completed delete disappears if list was stale.
      setTimeout(() => loadDocuments(), 2500);
    } catch (err) {
      toast("Could not delete document", "error");
    }
  }

  // ---- AI Assistant (real LangGraph RAG chatbot) ----
  let chatState = [];
  let chatLoaded = false;
  function chatBubble(msg) {
    const wrap = el("div", { class: `msg ${msg.role === "user" ? "user" : "ai"}` });
    wrap.appendChild(el("div", { class: "bubble", html: escapeHtml(msg.content).replace(/\n/g, "<br/>") }));
    if (msg.citations && msg.citations.length) {
      const src = el("div", { class: "msg-sources" });
      msg.citations.forEach((c) => src.appendChild(el("span", { class: "source-chip" }, [`${c.doc_name} · p.${c.page}`])));
      wrap.appendChild(src);
    }
    return wrap;
  }
  function renderChatContext() {
    const ctx = qs("#chat-context-docs");
    ctx.innerHTML = "";
    if (!docs.length) {
      ctx.appendChild(el("div", { class: "text-sm text-muted" }, ["No documents indexed yet."]));
      return;
    }
    docs.forEach((d) => ctx.appendChild(el("div", { class: "ctx-doc" }, [
      el("span", { html: icon(d.type === "img" ? "image" : "file") }),
      el("span", { class: "flex-1" }, [d.name]),
    ])));
  }
  function renderChatStream() {
    const stream = qs("#chat-stream");
    if (!stream || !caseObj) return;
    stream.innerHTML = "";
    if (!chatState.length) {
      const indexedCount = docs.filter((d) => d.embeddingStatus === "completed").length;
      const total = docs.length;
      let greeting;
      if (!total) {
        greeting = `Hi — no documents are uploaded for ${caseObj.title} yet. Upload a document first, then ask me anything about the case.`;
      } else if (indexedCount === 0) {
        greeting = `Hi — ${total} document${total === 1 ? " is" : "s are"} uploaded for ${caseObj.title}, but indexing is still in progress. You can ask once indexing completes.`;
      } else if (indexedCount < total) {
        greeting = `Hi — I've indexed ${indexedCount} of ${total} documents for ${caseObj.title}. Ask me anything about the case.`;
      } else {
        greeting = `Hi — I've indexed ${indexedCount} document${indexedCount === 1 ? "" : "s"} for ${caseObj.title}. Ask me anything about the case.`;
      }
      stream.appendChild(el("div", { class: "msg ai" }, [el("div", { class: "bubble" }, [greeting])]));
    } else {
      chatState.forEach((m) => stream.appendChild(chatBubble(m)));
    }
    stream.scrollTop = stream.scrollHeight;
  }
  function renderChat() {
    renderChatStream();
    renderChatContext();
  }

  async function loadChatHistory() {
    if (chatLoaded) return;
    try {
      const res = await fetch(window.CHAT_MESSAGES_API_URL, { headers: { Accept: "application/json" } });
      const result = await res.json();
      if (res.ok && result.success) {
        chatState = result.data || [];
        chatLoaded = true;
        renderChatStream();
      }
    } catch (err) {
      // Chat panel just falls back to the greeting bubble.
    }
  }

  async function sendMessage(text) {
    text = (text || "").trim();
    if (!text) return;
    const stream = qs("#chat-stream");
    if (!chatState.length) stream.innerHTML = "";
    const userMsg = { role: "user", content: text };
    chatState.push(userMsg);
    stream.appendChild(chatBubble(userMsg));
    qs("#chat-input").value = "";
    stream.scrollTop = stream.scrollHeight;

    const typing = el("div", { class: "msg ai" }, [el("div", { class: "bubble" }, [el("span", { class: "typing-dots" }, [el("i"), el("i"), el("i")])])]);
    stream.appendChild(typing);
    stream.scrollTop = stream.scrollHeight;

    try {
      const res = await fetch(window.CHAT_MESSAGES_API_URL, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json", "X-CSRFToken": getCookie("csrftoken") },
        body: JSON.stringify({ message: text }),
      });
      const result = await res.json();
      typing.remove();
      if (!res.ok || !result.success) {
        toast(result.detail || result.message || "Could not get a response", "error");
        return;
      }
      chatState.push(result.data);
      stream.appendChild(chatBubble(result.data));
      stream.scrollTop = stream.scrollHeight;
      loadActivity();
    } catch (err) {
      typing.remove();
      toast("Could not reach the AI Assistant — check that the chatbot service is running.", "error");
    }
  }

  // ---- Notes ----
  function noteCard(n) {
    const card = el("div", { class: `note-card ${n.ai ? "ai-note" : ""}` });
    card.appendChild(el("div", { class: "hd" }, [
      el("b", { style: "font-size:13px;" }, [(n.ai ? "✦ " : "") + n.title]),
      el("div", { class: "flex gap-6" }, [
        el("button", { class: "icon-btn btn-icon-only", style: "width:24px;height:24px;", html: icon("edit"), onclick: (e) => { e.stopPropagation(); openNoteEditor(n); } }),
        el("button", { class: "icon-btn btn-icon-only", style: "width:24px;height:24px;", html: icon("trash"), onclick: (e) => { e.stopPropagation(); deleteNote(n.id); } }),
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
        el("p", { class: "text-sm" }, ["Add a private note to keep track of important details."]),
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

  async function loadNotes() {
    try {
      const res = await fetch(window.CASE_NOTES_API_URL, { headers: { Accept: "application/json" } });
      const result = await res.json();
      if (!res.ok || !result.success) {
        toast(result.message || "Could not load notes", "error");
        return;
      }
      notesState = (result.data || []).map(mapNote);
      renderNotes();
    } catch (err) {
      toast("Could not load notes", "error");
    }
  }

  async function saveNote(title, body) {
    const isEdit = !!editingNoteId;
    const payload = { note_title: title, note_content: body };
    try {
      const url = isEdit ? window.CASE_NOTE_DETAIL_API_URL_TEMPLATE.replace("0", editingNoteId) : window.CASE_NOTES_API_URL;
      const res = await fetch(url, {
        method: isEdit ? "PATCH" : "POST",
        headers: jsonHeaders(),
        body: JSON.stringify(payload),
      });
      const result = await res.json();
      if (!res.ok || !result.success) {
        toast(result.message || "Could not save note", "error");
        return;
      }
      closeModal("note-modal");
      toast("Note saved", "success");
      await loadNotes();
      loadActivity();
    } catch (err) {
      toast("Could not save note", "error");
    }
  }

  async function deleteNote(id) {
    try {
      const url = window.CASE_NOTE_DETAIL_API_URL_TEMPLATE.replace("0", id);
      const res = await fetch(url, { method: "DELETE", headers: jsonHeaders() });
      const result = await res.json();
      if (!res.ok || !result.success) {
        toast(result.message || "Could not delete note", "error");
        return;
      }
      toast("Note deleted", "success");
      await loadNotes();
      loadActivity();
    } catch (err) {
      toast("Could not delete note", "error");
    }
  }

  // ---- Edit / delete case ----
  async function saveCaseEdit() {
    const payload = {
      case_id: qs("#e-number").value.trim(),
      case_title: qs("#e-title").value.trim(),
      client_name: qs("#e-client").value.trim(),
      opposing_party_name: qs("#e-opposite").value.trim(),
      court_name: qs("#e-court").value.trim(),
      hearing_date: qs("#e-hearing").value || undefined,
      case_description: qs("#e-desc").value.trim(),
    };
    try {
      const res = await fetch(window.CASE_DETAIL_API_URL, {
        method: "PATCH",
        headers: jsonHeaders(),
        body: JSON.stringify(payload),
      });
      const result = await res.json();
      if (!res.ok || !result.success) {
        toast(result.message || "Could not update case", "error");
        return;
      }
      caseObj = mapCase(result.data);
      renderHero();
      renderOverview();
      closeModal("edit-case-modal");
      toast("Case updated", "success");
    } catch (err) {
      toast("Could not update case", "error");
    }
  }

  async function deleteCase() {
    try {
      const res = await fetch(window.CASE_DETAIL_API_URL, { method: "DELETE", headers: jsonHeaders() });
      const result = await res.json();
      if (!res.ok || !result.success) {
        toast(result.message || "Could not delete case", "error");
        return;
      }
      toast("Case deleted", "success");
      window.location.href = window.CASES_LIST_URL;
    } catch (err) {
      toast("Could not delete case", "error");
    }
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
    qs("#simulate-upload-btn").addEventListener("click", () => qs("#doc-file-input").click());
    qs("#doc-file-input").addEventListener("change", (e) => {
      const file = e.target.files[0];
      e.target.value = "";
      uploadDocument(file);
    });
    const dropzone = qs("#dropzone");
    dropzone.addEventListener("dragover", (e) => { e.preventDefault(); dropzone.classList.add("drag-over"); });
    dropzone.addEventListener("dragleave", () => dropzone.classList.remove("drag-over"));
    dropzone.addEventListener("drop", (e) => {
      e.preventDefault();
      dropzone.classList.remove("drag-over");
      const file = e.dataTransfer.files[0];
      uploadDocument(file);
    });

    qs("#chat-send-btn").addEventListener("click", () => sendMessage(qs("#chat-input").value));
    qs("#chat-input").addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(qs("#chat-input").value); }
    });
    qsa(".suggestion-chip").forEach((chip) => chip.addEventListener("click", () => sendMessage(chip.getAttribute("data-q"))));

    qs("#new-note-btn").addEventListener("click", () => openNoteEditor(null));
    qs("#save-note-btn").addEventListener("click", () => {
      const title = qs("#note-title-input").value.trim() || "Untitled note";
      const body = qs("#note-body-input").value.trim();
      saveNote(title, body);
    });

    qs("#edit-case-btn").addEventListener("click", () => {
      qs("#e-number").value = caseObj.number;
      qs("#e-title").value = caseObj.title;
      qs("#e-client").value = caseObj.client;
      qs("#e-opposite").value = caseObj.opposite;
      qs("#e-court").value = caseObj.court;
      qs("#e-hearing").value = "";
      qs("#e-desc").value = caseObj.description;
      openModal("edit-case-modal");
    });
    qs("#save-case-edit-btn").addEventListener("click", saveCaseEdit);

    qs("#delete-case-link").addEventListener("click", (e) => { e.preventDefault(); openModal("delete-case-modal"); });
    qs("#confirm-delete-case-btn").addEventListener("click", deleteCase);
  }

  async function loadCase() {
    try {
      const res = await fetch(window.CASE_DETAIL_API_URL, { headers: { Accept: "application/json" } });
      const result = await res.json();
      if (!res.ok || !result.success) {
        toast(result.message || "Could not load case", "error");
        return;
      }
      caseObj = mapCase(result.data);
      renderHero();
      renderOverview();
      renderChat();
    } catch (err) {
      toast("Could not load case. Please refresh.", "error");
    }
  }

  (async function init() {
    await loadCase();
    if (!caseObj) return;
    await loadDocuments();
    await loadNotes();
    await loadActivity();
    await loadChatHistory();
    setupControls();
  })();
});
