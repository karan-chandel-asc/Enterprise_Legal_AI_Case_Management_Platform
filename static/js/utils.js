/** Small shared helpers used across all page scripts. */

function qs(sel, root) { return (root || document).querySelector(sel); }
function qsa(sel, root) { return Array.from((root || document).querySelectorAll(sel)); }

function el(tag, attrs, children) {
  const node = document.createElement(tag);
  if (attrs) {
    for (const [k, v] of Object.entries(attrs)) {
      if (k === "class") node.className = v;
      else if (k === "html") node.innerHTML = v;
      else if (k.startsWith("on") && typeof v === "function") node.addEventListener(k.slice(2), v);
      else node.setAttribute(k, v);
    }
  }
  (children || []).forEach((c) => {
    if (c == null) return;
    node.appendChild(typeof c === "string" ? document.createTextNode(c) : c);
  });
  return node;
}

function escapeHtml(str) {
  return String(str).replace(/[&<>"']/g, (m) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[m]));
}

function formatDateLong(iso) {
  if (!iso) return "—";
  const d = new Date(iso + "T00:00:00");
  return d.toLocaleDateString("en-US", { day: "2-digit", month: "short", year: "numeric" });
}

function formatDateShort(iso) {
  if (!iso) return "—";
  const d = new Date(iso + "T00:00:00");
  return { day: d.getDate(), month: d.toLocaleDateString("en-US", { month: "short" }).toUpperCase() };
}

function daysUntil(iso) {
  if (!iso) return null;
  const today = new Date(); today.setHours(0, 0, 0, 0);
  const target = new Date(iso + "T00:00:00");
  return Math.round((target - today) / 86400000);
}

function statusBadge(status) {
  const map = {
    active: { cls: "badge-success", label: "Active" },
    hearing: { cls: "badge-warning", label: "Hearing" },
    closed: { cls: "badge-neutral", label: "Closed" },
    confirmed: { cls: "badge-info", label: "Confirmed" },
    urgent: { cls: "badge-danger", label: "Urgent" },
    processing: { cls: "badge-warning", label: "Processing" },
    complete: { cls: "badge-success", label: "Complete" },
    "n/a": { cls: "badge-neutral", label: "N/A" },
  };
  const m = map[status] || { cls: "badge-neutral", label: status };
  return `<span class="badge ${m.cls}"><span class="dot"></span>${m.label}</span>`;
}

function initials(name) {
  return name.split(" ").map((p) => p[0]).slice(0, 2).join("").toUpperCase();
}

function docIconClass(type) {
  return { pdf: "pdf", docx: "docx", txt: "txt", img: "img" }[type] || "txt";
}

function toast(message, type) {
  let stack = qs(".toast-stack");
  if (!stack) {
    stack = el("div", { class: "toast-stack" });
    document.body.appendChild(stack);
  }
  const t = el("div", { class: `toast fade-in ${type || ""}` }, [message]);
  stack.appendChild(t);
  setTimeout(() => { t.style.opacity = "0"; t.style.transition = "opacity .25s"; setTimeout(() => t.remove(), 250); }, 2600);
}

function openModal(id) { const m = qs("#" + id); if (m) m.classList.add("open"); }
function closeModal(id) { const m = qs("#" + id); if (m) m.classList.remove("open"); }

document.addEventListener("click", (e) => {
  if (e.target.matches("[data-close-modal]")) {
    const backdrop = e.target.closest(".modal-backdrop");
    if (backdrop) backdrop.classList.remove("open");
  }
  if (e.target.classList && e.target.classList.contains("modal-backdrop")) {
    e.target.classList.remove("open");
  }
  if (e.target.matches("[data-close-slideover]")) {
    const backdrop = e.target.closest(".slideover-backdrop");
    if (backdrop) backdrop.classList.remove("open");
  }
  if (e.target.classList && e.target.classList.contains("slideover-backdrop")) {
    e.target.classList.remove("open");
  }
});
