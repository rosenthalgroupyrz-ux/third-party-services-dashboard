"use strict";

// Data comes only from /api/data, which the local server builds from the JSON
// files in dataExports/. Searching happens here in the browser.

const KNOWN_COLORS = {
  github: "#6e40c9",
  // Notion's near-black brand color disappears on a dark background.
  notion: matchMedia("(prefers-color-scheme: dark)").matches ? "#8c8a85" : "#37352f",
  linear: "#5e6ad2",
  todoist: "#db4035",
  asana: "#f06a6a",
};
const DISPLAY_NAMES = { github: "GitHub", notion: "Notion", linear: "Linear", todoist: "Todoist", asana: "Asana" };

const state = { data: null, service: "all", query: "", sort: "relevance" };
const $ = (id) => document.getElementById(id);

function displayName(service) {
  return DISPLAY_NAMES[service] || service.charAt(0).toUpperCase() + service.slice(1);
}

function serviceColor(service) {
  if (KNOWN_COLORS[service]) return KNOWN_COLORS[service];
  let h = 0;
  for (const c of service) h = (h * 31 + c.charCodeAt(0)) % 360;
  return `hsl(${h} 55% 45%)`;
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function escapeRegex(s) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

// Markdown/HTML to readable plain text, for excerpts.
function plainText(s) {
  return String(s || "")
    .replace(/<linear-image>[\s\S]*?<\/linear-image>/g, " ")
    .replace(/<[^>]+>/g, " ")
    .replace(/!\[[^\]]*\]\([^)]*\)/g, " ")
    .replace(/\[([^\]]*)\]\([^)]*\)/g, "$1")
    .replace(/^\s{0,3}(#{1,6}|>|[-*+]|\d+\.)\s+/gm, "")
    .replace(/[*_`|~]+/g, "")
    .replace(/\s+/g, " ")
    .trim();
}

// "Joe Smith" -> ["joe", "smith"]; quoted text stays one term: "\"route plan\"".
function parseQuery(q) {
  const terms = [];
  const re = /"([^"]+)"|(\S+)/g;
  let m;
  while ((m = re.exec(q))) terms.push((m[1] || m[2]).toLowerCase());
  return terms.filter(Boolean);
}

function countOf(hay, needle) {
  let n = 0, i = 0;
  while ((i = hay.indexOf(needle, i)) !== -1) { n++; i += needle.length; }
  return n;
}

function prepare(data) {
  for (const r of data.records) {
    r._bodyText = plainText(r.body);
    r._title = r.title.toLowerCase();
    r._body = r._bodyText.toLowerCase();
    r._meta = [r.id, r.display_id || "", r.meta.map((m) => m.value).join(" "), r.search_meta].join(" ").toLowerCase();
    const times = r.dates.filter((d) => d.label !== "Due").map((d) => Date.parse(d.value)).filter((t) => !isNaN(t));
    r._time = times.length ? Math.max(...times) : 0;
  }
}

function score(r, terms, phrase) {
  let s = 0;
  for (const t of terms) {
    const inTitle = r._title.includes(t), inBody = r._body.includes(t), inMeta = r._meta.includes(t);
    if (!inTitle && !inBody && !inMeta) return -1; // every term must match somewhere
    if (inTitle) s += 6;
    if (inBody) s += 1 + Math.min(countOf(r._body, t), 10) * 0.3;
    if (inMeta) s += 0.5;
  }
  if (terms.length > 1) {
    if (r._title.includes(phrase)) s += 10;
    if (r._body.includes(phrase)) s += 5;
    if (r._meta.includes(phrase)) s += 2;
  }
  return s;
}

// Pick a ~240 character window of the body around the first match, or fall
// back to the metadata when only the metadata matched.
function excerpt(r, terms, phrase) {
  const sources = [[r._bodyText, r._body, null], [r.search_meta, r.search_meta.toLowerCase(), "Matched in metadata"]];
  if (!terms.length) {
    return { text: r._bodyText.slice(0, 240) + (r._bodyText.length > 240 ? "…" : ""), note: null };
  }
  for (const [text, lower, note] of sources) {
    let idx = terms.length > 1 ? lower.indexOf(phrase) : -1;
    if (idx === -1) {
      for (const t of terms) { idx = lower.indexOf(t); if (idx !== -1) break; }
    }
    if (idx === -1) continue;
    let start = Math.max(0, idx - 90);
    if (start > 0) { const sp = text.indexOf(" ", start); if (sp !== -1 && sp < idx) start = sp + 1; }
    let end = Math.min(text.length, idx + 150);
    if (end < text.length) { const sp = text.lastIndexOf(" ", end); if (sp > idx) end = sp; }
    return { text: (start > 0 ? "…" : "") + text.slice(start, end) + (end < text.length ? "…" : ""), note };
  }
  // Matched only in the title: show the start of the body for context.
  return { text: r._bodyText.slice(0, 240) + (r._bodyText.length > 240 ? "…" : ""), note: null };
}

function highlight(text, terms) {
  if (!terms.length || !text) return escapeHtml(text);
  // The whole phrase goes first so "Joe Smith" is marked as one span.
  const parts = terms.length > 1 ? [terms.join(" "), ...terms] : terms;
  const re = new RegExp("(" + [...parts].sort((a, b) => b.length - a.length).map(escapeRegex).join("|") + ")", "gi");
  return text.split(re).map((part, i) => (i % 2 ? `<mark>${escapeHtml(part)}</mark>` : escapeHtml(part))).join("");
}

function formatDate(v) {
  if (/^\d{4}-\d{2}-\d{2}$/.test(v)) {
    const [y, m, d] = v.split("-").map(Number);
    return new Date(Date.UTC(y, m - 1, d)).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric", timeZone: "UTC" });
  }
  const t = new Date(v);
  if (isNaN(t)) return v;
  return t.toLocaleString(undefined, { year: "numeric", month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
}

function search() {
  const { data } = state;
  const terms = parseQuery(state.query);
  const phrase = terms.join(" ");
  const pool = data.records.filter((r) => state.service === "all" || r.service === state.service);
  const hits = [];
  for (const r of pool) {
    const s = terms.length ? score(r, terms, phrase) : 0;
    if (s >= 0) hits.push({ r, s });
  }
  const sorters = {
    relevance: (a, b) => (b.s - a.s) || (b.r._time - a.r._time),
    newest: (a, b) => b.r._time - a.r._time,
    oldest: (a, b) => a.r._time - b.r._time,
    title: (a, b) => a.r.title.localeCompare(b.r.title),
  };
  hits.sort(sorters[!terms.length && state.sort === "relevance" ? "newest" : state.sort]);
  return { hits, terms, phrase };
}

function countsByService(terms, phrase) {
  const counts = {};
  for (const r of state.data.records) {
    if (!terms.length || score(r, terms, phrase) >= 0) counts[r.service] = (counts[r.service] || 0) + 1;
  }
  return counts;
}

function renderServices(terms, phrase) {
  const counts = countsByService(terms, phrase);
  const total = Object.values(counts).reduce((a, b) => a + b, 0);
  const chip = (value, label, n, color, empty) => `
    <button type="button" class="chip${state.service === value ? " active" : ""}${empty ? " empty" : ""}"
      data-service="${escapeHtml(value)}" aria-pressed="${state.service === value}"
      style="--svc:${color}" title="${empty ? "No files in this folder yet" : ""}">
      ${value === "all" ? "" : '<span class="dot"></span>'}${escapeHtml(label)}
      <span class="count">${n}</span>
    </button>`;
  $("services").innerHTML =
    chip("all", "All services", total, "var(--accent)", false) +
    state.data.services.map((s) => chip(s.name, displayName(s.name), counts[s.name] || 0, serviceColor(s.name), s.count === 0)).join("");
}

function renderProblems() {
  const p = state.data.problems;
  const box = $("problems");
  if (!p.length) { box.hidden = true; return; }
  box.hidden = false;
  box.innerHTML = `<details><summary><strong>${p.length} file${p.length > 1 ? "s" : ""} skipped</strong> because they could not be read. Other results are unaffected.</summary>
    <ul>${p.map((x) => `<li><code>${escapeHtml(x.file)}</code> — ${escapeHtml(x.error)}</li>`).join("")}</ul></details>`;
}

function renderResult({ r }, terms, phrase) {
  const ex = excerpt(r, terms, phrase);
  const color = serviceColor(r.service);
  const meta = r.meta.map((m) => `<span class="tag${m.kind ? " tag-" + m.kind : ""}"><span class="tag-k">${escapeHtml(m.label)}</span> ${highlight(m.value, terms)}</span>`).join("");
  const dates = r.dates.slice(0, 3).map((d) => `<span><span class="tag-k">${escapeHtml(d.label)}</span> ${escapeHtml(formatDate(d.value))}</span>`).join("");
  const ids = [r.display_id, r.id].filter((v, i, a) => v && a.indexOf(v) === i);
  const title = highlight(r.title, terms);
  return `<li class="result" style="--svc:${color}">
    <div class="result-head">
      <span class="badge">${escapeHtml(displayName(r.service))}</span>
      <h2>${r.icon ? `<span class="icon">${escapeHtml(r.icon)}</span>` : ""}${r.url
        ? `<a href="${escapeHtml(r.url)}" target="_blank" rel="noopener noreferrer">${title}</a>`
        : title}</h2>
    </div>
    ${ex.text ? `<p class="excerpt">${ex.note ? `<span class="note">${ex.note}:</span> ` : ""}${highlight(ex.text, terms)}</p>` : ""}
    ${meta ? `<div class="tags">${meta}</div>` : ""}
    <div class="foot">
      <span class="ids">${ids.map((v) => `<code title="ID">${highlight(v, terms)}</code>`).join(" ")}</span>
      ${dates ? `<span class="dates">${dates}</span>` : ""}
      ${r.url ? `<a class="open" href="${escapeHtml(r.url)}" target="_blank" rel="noopener noreferrer">Open in ${escapeHtml(displayName(r.service))} ↗</a>` : ""}
    </div>
  </li>`;
}

function render() {
  if (!state.data) return;
  const { hits, terms, phrase } = search();
  renderServices(terms, phrase);
  const svc = state.data.services.find((s) => s.name === state.service);
  const where = state.service === "all" ? "all services" : displayName(state.service);
  const summary = $("summary"), list = $("results");

  if (!state.data.records.length && state.service === "all") {
    summary.textContent = "";
    list.innerHTML = `<li class="empty-state"><h2>No data yet</h2><p>No JSON files were found in <code>dataExports/</code>. Run the download skill, then click “Reload data”.</p></li>`;
    return;
  }
  if (svc && svc.count === 0) {
    summary.textContent = "";
    list.innerHTML = `<li class="empty-state"><h2>${escapeHtml(displayName(svc.name))} has no data yet</h2><p>The folder <code>dataExports/${escapeHtml(svc.name)}/</code> has no readable JSON files. Items will appear here once they are exported.</p></li>`;
    return;
  }
  if (!hits.length) {
    summary.textContent = "";
    list.innerHTML = `<li class="empty-state"><h2>No results for “${escapeHtml(state.query.trim())}”</h2>
      <p>Nothing in ${escapeHtml(where)} matches every search word. Try fewer or different words${state.service === "all" ? "" : ', or search <button type="button" class="linkish" data-service="all">all services</button>'}.</p></li>`;
    return;
  }
  summary.textContent = terms.length
    ? `${hits.length} result${hits.length === 1 ? "" : "s"} for “${state.query.trim()}” in ${where}`
    : `Showing all ${hits.length} item${hits.length === 1 ? "" : "s"} in ${where}`;
  list.innerHTML = hits.map((h) => renderResult(h, terms, phrase)).join("");
}

// Keep the search in the URL so a view can be bookmarked or shared.
function syncUrl() {
  const p = new URLSearchParams();
  if (state.query.trim()) p.set("q", state.query.trim());
  if (state.service !== "all") p.set("service", state.service);
  if (state.sort !== "relevance") p.set("sort", state.sort);
  const qs = p.toString();
  history.replaceState(null, "", qs ? "?" + qs : location.pathname);
}

function readUrl() {
  const p = new URLSearchParams(location.search);
  state.query = p.get("q") || "";
  state.service = p.get("service") || "all";
  state.sort = p.get("sort") || "relevance";
  $("q").value = state.query;
  $("sort").value = state.sort;
}

async function load() {
  $("summary").textContent = "Loading…";
  try {
    const res = await fetch("/api/data", { cache: "no-store" });
    if (!res.ok) throw new Error(`Server returned ${res.status}`);
    state.data = await res.json();
  } catch (e) {
    $("summary").textContent = "";
    $("results").innerHTML = `<li class="empty-state"><h2>Could not load data</h2><p>${escapeHtml(e.message)}. Is <code>python3 webapp/server.py</code> still running?</p></li>`;
    return;
  }
  prepare(state.data);
  if (state.service !== "all" && !state.data.services.some((s) => s.name === state.service)) state.service = "all";
  renderProblems();
  render();
}

let timer;
$("q").addEventListener("input", (e) => {
  clearTimeout(timer);
  timer = setTimeout(() => { state.query = e.target.value; syncUrl(); render(); }, 120);
});
$("search-form").addEventListener("submit", (e) => { e.preventDefault(); state.query = $("q").value; syncUrl(); render(); });
$("sort").addEventListener("change", (e) => { state.sort = e.target.value; syncUrl(); render(); });
document.addEventListener("click", (e) => {
  const b = e.target.closest("[data-service]");
  if (!b) return;
  state.service = b.dataset.service;
  syncUrl();
  render();
});
$("reload").addEventListener("click", load);

readUrl();
load();
