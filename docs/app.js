// aismell web app — runs the real Python core via Pyodide in your browser.
// Your text never leaves the page.

const I18N = {
  es: {
    title: "aismell",
    tagline: "Pega tu texto. Te marcamos lo que huele a IA. Offline en tu navegador, sin trampa, sin promesas de \"burlar detectores\".",
    boot: "cargando python en tu navegador (~6 MB la primera vez)…",
    booting: "preparando aismell…",
    ready: "listo. pega tu texto y dale a analizar.",
    analyzing: "olfateando…",
    analyzing_steps: [
      "leyendo el texto…",
      "buscando muletillas…",
      "midiendo ritmo de oraciones…",
      "olfateando conectores…",
      "calculando smell…",
    ],
    error: "algo se rompió:",
    lang: "idioma",
    strict: "solo alta confianza",
    analyze: "analizar",
    clear: "limpiar",
    why: "qué hace",
    whyText: "aismell lee tu texto y marca línea por línea qué huele a modelo de lenguaje. Patrones reales, regex auditable, sin llamadas a APIs externas — el texto nunca sale de tu navegador.",
    not: "qué NO hace",
    not1: "<strong>No reescribe tu texto.</strong> Tú decides qué cambiar.",
    not2: "<strong>No promete burlar detectores.</strong> Ese juego es scam.",
    not3: "<strong>No es forense.</strong> Falsos positivos pasan; humanos también usan estas frases.",
    cli: "también CLI",
    cliText: "¿Necesitas anotar archivos Word o PDF con highlights y comentarios? Hay una versión de terminal que hace eso. <a href=\"https://github.com/brm-src/aismell\">github.com/brm-src/aismell</a>",
    donate: "☕ invitame un café",
    placeholder: "Pega tu texto acá. O suelta un archivo (.txt / .md / .docx).",
    sentences: "oraciones",
    smell: "smell",
    findings: "hallazgos",
    sev_high: "severidad alta",
    sev_mod: "media",
    sev_low: "baja",
    density: "densidad",
    density_text: "{n} de {total} oraciones con marca ({pct}%)",
    top_patterns: "más repetidos:",
    label_high: "alto",
    label_mod: "moderado",
    label_low: "bajo",
    label_clean: "limpio",
    clean: "limpio · nada que delatar",
    line: "L",
    empty: "pega texto y dale analizar",
    structural: "hallazgos estructurales",
    inline: "hallazgos línea por línea",
    global: "(global)",
    drop_hint: "suelta el archivo para analizarlo",
    upload: "subir archivo",
    annotating: "marcando word…",
    docx_done: "✓ {name} descargado. Ábrelo en Word o LibreOffice — los hallazgos están en amarillo con comentarios al costado.",
    pdf_browser_unsupported: "PDF en la web aún no se puede (la librería no carga en el navegador). Para PDF usa el CLI: aismell paper.pdf --out paper-marcado.pdf",
    biblio: "verificar bibliografía",
    biblioTip: "Detecta DOIs, IDs de arXiv y citas, y consulta CrossRef + arXiv para ver si existen. Solo se envían los identificadores, no tu texto. Útil porque la IA inventa referencias falsas.",
    biblio_header: "BIBLIOGRAFÍA — {n} REFERENCIAS",
    biblio_privacy: "Solo se envían los identificadores (DOI/arXiv/título) a CrossRef y arXiv. Tu texto no sale.",
    biblio_none: "no se detectaron referencias parseables",
    biblio_warning: "⚠  {fakes}/{total} referencias no se encontraron — posible IA inventando",
  },
  en: {
    title: "aismell",
    tagline: "Paste your text. We flag what smells like an LLM wrote it. Offline in your browser, no tricks, no \"bypass detectors\" lies.",
    boot: "loading python in your browser (~6 MB on first visit)…",
    booting: "warming up aismell…",
    ready: "ready. paste your text and hit analyze.",
    analyzing: "sniffing…",
    analyzing_steps: [
      "reading text…",
      "matching filler phrases…",
      "measuring sentence rhythm…",
      "sniffing connectors…",
      "scoring smell…",
    ],
    error: "something broke:",
    lang: "language",
    strict: "high confidence only",
    analyze: "analyze",
    clear: "clear",
    why: "what it does",
    whyText: "aismell reads your text and marks line by line what smells like a language model wrote it. Real patterns, auditable regex, no external API calls — your text never leaves your browser.",
    not: "what it does NOT do",
    not1: "<strong>Does not rewrite your text.</strong> You decide what to change.",
    not2: "<strong>Does not promise to bypass detectors.</strong> That game is a scam.",
    not3: "<strong>Not forensic.</strong> False positives happen; humans use these phrases too.",
    cli: "also a CLI",
    cliText: "Need to annotate Word or PDF files with highlights and comments? There's a terminal version that does that. <a href=\"https://github.com/brm-src/aismell\">github.com/brm-src/aismell</a>",
    donate: "☕ buy me a coffee",
    placeholder: "Paste your text here. Or drop a file (.txt / .md / .docx).",
    sentences: "sentences",
    smell: "smell",
    findings: "findings",
    sev_high: "high severity",
    sev_mod: "medium",
    sev_low: "low",
    density: "density",
    density_text: "{n} of {total} sentences flagged ({pct}%)",
    top_patterns: "most repeated:",
    label_high: "high",
    label_mod: "moderate",
    label_low: "low",
    label_clean: "clean",
    clean: "clean · nothing tells",
    line: "L",
    empty: "paste text and hit analyze",
    structural: "structural findings",
    inline: "line-by-line findings",
    global: "(global)",
    drop_hint: "drop the file to analyze",
    upload: "upload file",
    annotating: "annotating word…",
    docx_done: "✓ {name} downloaded. Open it in Word or LibreOffice — findings are highlighted in yellow with side comments.",
    pdf_browser_unsupported: "PDF in the browser isn't supported yet (the library doesn't run in WASM). For PDF use the CLI: aismell paper.pdf --out paper-marked.pdf",
    biblio: "verify bibliography",
    biblioTip: "Finds DOIs, arXiv IDs and citations, then queries CrossRef + arXiv to check they exist. Only the identifiers leave your browser, not your text. Useful because LLMs hallucinate references.",
    biblio_header: "BIBLIOGRAPHY — {n} REFERENCES",
    biblio_privacy: "Only identifiers (DOI/arXiv/title) are sent to CrossRef and arXiv. Your text stays local.",
    biblio_none: "no parseable references found",
    biblio_warning: "⚠  {fakes}/{total} references not found — possible AI hallucination",
  },
};

const els = {
  status: document.getElementById("status"),
  input: document.getElementById("input"),
  langSel: document.getElementById("langSel"),
  strictSel: document.getElementById("strictSel"),
  biblioSel: document.getElementById("biblioSel"),
  analyzeBtn: document.getElementById("analyzeBtn"),
  clearBtn: document.getElementById("clearBtn"),
  fileBtn: document.getElementById("fileBtn"),
  fileInput: document.getElementById("fileInput"),
  resultPanel: document.getElementById("resultPanel"),
  score: document.getElementById("score"),
  findings: document.getElementById("findings"),
  langSwitch: document.getElementById("langSwitch"),
};

// ---------- i18n ----------
let UILANG = (navigator.language || "es").startsWith("en") ? "en" : "es";
function applyI18n() {
  const t = I18N[UILANG];
  for (const el of document.querySelectorAll("[data-i18n]")) {
    const k = el.getAttribute("data-i18n");
    if (t[k] !== undefined) el.innerHTML = t[k];
  }
  for (const el of document.querySelectorAll("[data-i18n-tip]")) {
    const k = el.getAttribute("data-i18n-tip");
    if (t[k] !== undefined) el.setAttribute("data-tip", t[k]);
  }
  els.input.placeholder = t.placeholder;
  document.documentElement.lang = UILANG;
  for (const b of els.langSwitch.querySelectorAll("button")) {
    b.classList.toggle("on", b.dataset.lang === UILANG);
  }
}
els.langSwitch.addEventListener("click", (e) => {
  const t = e.target.closest("button");
  if (!t) return;
  UILANG = t.dataset.lang;
  applyI18n();
});
applyI18n();

// ---------- Pyodide ----------
let pyodide = null;
let analyzeFn = null;
let annotateDocxFn = null;
let extractRefsFn = null;

function setStatus(msg, isError = false) {
  if (msg === null) {
    els.status.innerHTML = "";
    els.status.classList.remove("err");
    return;
  }
  els.status.innerHTML = msg;
  els.status.classList.toggle("err", isError);
}

async function bootPyodide() {
  try {
    pyodide = await loadPyodide({
      indexURL: "https://cdn.jsdelivr.net/pyodide/v0.27.2/full/",
    });
    await pyodide.loadPackage("pyyaml");

    // Fetch the patterns + core source from the same site (or from the
    // repo on GitHub Pages). Falls back to the GitHub raw URL if local
    // fetch fails so a copy-paste of index.html alone still works.
    const sources = await loadSources();

    pyodide.FS.mkdir("/aismell");
    pyodide.FS.mkdir("/aismell/patterns");
    pyodide.FS.writeFile("/aismell/__init__.py", "");
    pyodide.FS.writeFile("/aismell/core.py", sources.core);
    pyodide.FS.writeFile("/aismell/docx.py", sources.docx);
    pyodide.FS.writeFile("/aismell/biblio.py", sources.biblio);
    pyodide.FS.writeFile("/aismell/patterns/es.yaml", sources.es);
    pyodide.FS.writeFile("/aismell/patterns/en.yaml", sources.en);

    pyodide.runPython(`
import sys
sys.path.insert(0, "/")
from aismell.core import analyze
from aismell.docx import annotate_docx
from aismell.biblio import find_references
from pathlib import Path

def run(text, lang_code, strict):
    lang = None if lang_code == "auto" else lang_code
    report, used = analyze(text, lang=lang, strict=strict)
    out = {
        "score": report.score,
        "label": report.severity_label,
        "sentences": report.sentences,
        "lang": used,
        "hits": [],
        "structural": [],
    }
    for h in report.hits:
        out["hits"].append({
            "line": h.line,
            "col": h.col,
            "end": h.end,
            "text": h.text,
            "matched": h.matched,
            "id": h.pattern.id,
            "severity": h.pattern.severity,
            "message": h.pattern.message,
            "suggestion": h.pattern.suggestion,
        })
    for s in report.structural:
        out["structural"].append({
            "line": s.line,
            "kind": s.kind,
            "severity": s.severity,
            "message": s.message,
            "suggestion": s.suggestion,
        })
    return out

def annotate_docx_bytes(input_bytes, lang_code, strict):
    src = Path("/tmp/in.docx")
    dst = Path("/tmp/out.docx")
    src.write_bytes(bytes(input_bytes))
    lang = None if lang_code == "auto" else lang_code
    result = annotate_docx(src, dst, lang=lang, strict=strict)
    data = dst.read_bytes()
    return {
        "bytes": data,
        "findings": result.findings,
        "sentences": result.sentences,
        "score": result.score,
        "label": result.severity_label,
    }

def extract_refs(text):
    refs = find_references(text)
    out = []
    for r in refs:
        out.append({
            "kind": r.kind,
            "raw": r.raw,
            "line": r.line,
            "identifier": r.identifier,
            "title": r.title,
            "year": r.year,
            "author": r.author,
        })
    return out
`);
    analyzeFn = pyodide.globals.get("run");
    annotateDocxFn = pyodide.globals.get("annotate_docx_bytes");
    extractRefsFn = pyodide.globals.get("extract_refs");
    setStatus(I18N[UILANG].ready);
    els.analyzeBtn.disabled = false;
  } catch (err) {
    setStatus(`${I18N[UILANG].error} ${err.message}`, true);
    console.error(err);
  }
}

async function loadSources() {
  // Try local relative paths first.
  const local = {
    core: "core.py",
    docx: "docx.py",
    biblio: "biblio.py",
    es: "patterns/es.yaml",
    en: "patterns/en.yaml",
  };
  const remote = {
    core: "https://raw.githubusercontent.com/brm-src/aismell/main/aismell/core.py",
    docx: "https://raw.githubusercontent.com/brm-src/aismell/main/aismell/docx.py",
    biblio: "https://raw.githubusercontent.com/brm-src/aismell/main/aismell/biblio.py",
    es:   "https://raw.githubusercontent.com/brm-src/aismell/main/aismell/patterns/es.yaml",
    en:   "https://raw.githubusercontent.com/brm-src/aismell/main/aismell/patterns/en.yaml",
  };
  const out = {};
  for (const k of Object.keys(local)) {
    let body = null;
    try {
      const r = await fetch(local[k]);
      if (r.ok) body = await r.text();
    } catch (_) { /* try remote */ }
    if (!body) {
      const r = await fetch(remote[k]);
      if (!r.ok) throw new Error(`could not fetch ${k}`);
      body = await r.text();
    }
    out[k] = body;
  }
  return out;
}

// ---------- analyze + render ----------
function severityClass(score) {
  if (score >= 0.6) return "s-high";
  if (score >= 0.3) return "s-mod";
  if (score > 0) return "s-low";
  return "s-clean";
}

function severityLabel(score) {
  const t = I18N[UILANG];
  if (score >= 0.6) return t.label_high;
  if (score >= 0.3) return t.label_mod;
  if (score > 0)    return t.label_low;
  return t.label_clean;
}

function escapeHtml(s) {
  return s
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function renderHit(hit, t) {
  const before = escapeHtml(hit.text.slice(0, hit.col));
  const matched = escapeHtml(hit.text.slice(hit.col, hit.end));
  const after = escapeHtml(hit.text.slice(hit.end));
  let glyph = "·";
  if (hit.severity === 3) glyph = "🔴";
  else if (hit.severity === 2) glyph = "⚠";
  return `
    <div class="finding">
      <div class="glyph s-${hit.severity}">${glyph}</div>
      <div class="body">
        <div class="ctx">${before}<span class="match">${matched}</span>${after}</div>
        <div class="meta">${escapeHtml(hit.message)} <span class="id">${escapeHtml(hit.id)}</span> · ${t.line}${hit.line}</div>
        ${hit.suggestion ? `<div class="sug">${escapeHtml(hit.suggestion)}</div>` : ""}
      </div>
    </div>`;
}

function renderStructural(s, t) {
  let glyph = "·";
  if (s.severity === 3) glyph = "🔴";
  else if (s.severity === 2) glyph = "⚠";
  const where = s.line ? `${t.line}${s.line}` : t.global;
  return `
    <div class="finding">
      <div class="glyph s-${s.severity}">${glyph}</div>
      <div class="body">
        <div class="ctx" style="color: var(--fg);">${escapeHtml(s.message)}</div>
        <div class="meta"><span class="id">${escapeHtml(s.kind)}</span> · ${where}</div>
        ${s.suggestion ? `<div class="sug">${escapeHtml(s.suggestion)}</div>` : ""}
      </div>
    </div>`;
}

function render(report) {
  const t = I18N[UILANG];
  const pct = Math.round(report.score * 100);
  const sev = severityClass(report.score);

  // Severity breakdown
  let sevHigh = 0, sevMod = 0, sevLow = 0;
  for (const h of report.hits) {
    if (h.severity === 3) sevHigh++;
    else if (h.severity === 2) sevMod++;
    else sevLow++;
  }
  for (const s of report.structural) {
    if (s.severity === 3) sevHigh++;
    else if (s.severity === 2) sevMod++;
    else sevLow++;
  }

  // Density: % of distinct lines with at least one inline hit
  const flaggedLines = new Set();
  for (const h of report.hits) flaggedLines.add(h.line);
  const flagged = flaggedLines.size;
  const denPct = report.sentences ? Math.round((flagged / report.sentences) * 100) : 0;

  // Top repeated patterns (by id)
  const counts = {};
  for (const h of report.hits) {
    counts[h.id] = (counts[h.id] || 0) + 1;
  }
  const top = Object.entries(counts)
    .sort((a, b) => b[1] - a[1])
    .filter(([, n]) => n >= 2)
    .slice(0, 3);

  const totalFindings = report.hits.length + report.structural.length;

  let scoreHtml = `
    <div class="score-top">
      <div class="pct ${sev}">${pct}%</div>
      <div class="meta">
        <strong>${severityLabel(report.score)}</strong> · ${report.sentences} ${t.sentences} ·
        ${totalFindings} ${t.findings} · ${report.lang}
      </div>
    </div>`;

  if (totalFindings > 0) {
    scoreHtml += `
    <div class="score-bars">
      <div class="score-bar s-high">
        <div class="num">${sevHigh}</div>
        <div class="lbl">${t.sev_high}</div>
      </div>
      <div class="score-bar s-mod">
        <div class="num">${sevMod}</div>
        <div class="lbl">${t.sev_mod}</div>
      </div>
      <div class="score-bar s-low">
        <div class="num">${sevLow}</div>
        <div class="lbl">${t.sev_low}</div>
      </div>
    </div>`;

    if (flagged > 0 && report.sentences > 0) {
      scoreHtml += `
    <div class="score-density">
      <span>${t.density_text.replace("{n}", flagged).replace("{total}", report.sentences).replace("{pct}", denPct)}</span>
      <div class="track"><div class="fill" style="width: ${Math.min(100, denPct)}%"></div></div>
    </div>`;
    }

    if (top.length > 0) {
      const chips = top.map(([id, n]) => `<span class="chip"><span class="cnt">×${n}</span>${escapeHtml(id)}</span>`).join("");
      scoreHtml += `
    <div class="score-top-patterns">
      <span>${t.top_patterns}</span>
      ${chips}
    </div>`;
    }
  }

  els.score.innerHTML = scoreHtml;

  if (report.hits.length === 0 && report.structural.length === 0) {
    els.findings.innerHTML = `<div class="clean">${t.clean}</div>`;
    els.resultPanel.hidden = false;
    return;
  }

  let html = "";
  if (report.hits.length) {
    const sorted = [...report.hits].sort((a, b) => a.line - b.line || a.col - b.col);
    html += sorted.map((h) => renderHit(h, t)).join("");
  }
  if (report.structural.length) {
    html += `<div class="finding" style="border-bottom: 1px dashed var(--line); color: var(--dim); font-size: 12px; text-transform: uppercase; letter-spacing: 1px;"><div></div><div>${t.structural}</div></div>`;
    html += report.structural.map((s) => renderStructural(s, t)).join("");
  }
  els.findings.innerHTML = html;
  els.resultPanel.hidden = false;
}

async function analyze() {
  if (!analyzeFn) return;
  const text = els.input.value;
  if (!text.trim()) {
    setStatus(I18N[UILANG].empty);
    return;
  }
  els.analyzeBtn.disabled = true;

  // Rotating animation messages — at least one cycle so it feels real
  const steps = I18N[UILANG].analyzing_steps || [I18N[UILANG].analyzing];
  let i = 0;
  setStatus(`<span class="spin">●</span> ${steps[0]}`);
  const ticker = setInterval(() => {
    i = (i + 1) % steps.length;
    setStatus(`<span class="spin">●</span> ${steps[i]}`);
  }, 350);

  // Run sync code in a microtask so the spinner renders first
  await new Promise((r) => setTimeout(r, 50));
  const startedAt = performance.now();

  try {
    const res = analyzeFn(text, els.langSel.value, els.strictSel.checked);
    const obj = res.toJs({ dict_converter: Object.fromEntries });
    res.destroy();

    // Floor at ~1.2s so very short texts don't feel instant/fake
    const elapsed = performance.now() - startedAt;
    if (elapsed < 1200) await new Promise((r) => setTimeout(r, 1200 - elapsed));
    clearInterval(ticker);

    render(obj);
    setStatus(null);

    // Optional: verify bibliography (network call to CrossRef/arXiv).
    if (els.biblioSel && els.biblioSel.checked && extractRefsFn) {
      await verifyBibliography(text);
    }
  } catch (err) {
    clearInterval(ticker);
    setStatus(`${I18N[UILANG].error} ${err.message}`, true);
    console.error(err);
  } finally {
    els.analyzeBtn.disabled = false;
  }
}

els.analyzeBtn.addEventListener("click", () => { clearBiblio(); analyze(); });
els.clearBtn.addEventListener("click", () => {
  els.input.value = "";
  els.resultPanel.hidden = true;
  clearBiblio();
  els.input.focus();
});

// Cmd/Ctrl+Enter to analyze
els.input.addEventListener("keydown", (e) => {
  if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
    e.preventDefault();
    clearBiblio();
    analyze();
  }
});

// ---------- bibliography verification ----------
function appendBiblio(html) {
  let panel = document.getElementById("biblioPanel");
  if (!panel) {
    panel = document.createElement("div");
    panel.id = "biblioPanel";
    panel.className = "biblio";
    els.resultPanel.appendChild(panel);
  }
  panel.insertAdjacentHTML("beforeend", html);
}

function clearBiblio() {
  const panel = document.getElementById("biblioPanel");
  if (panel) panel.remove();
}

function renderBiblioRow(ref, res) {
  const icon = { exists: "✓", not_found: "✗", error: "?", unverifiable: "·" }[res.status] || "·";
  const cls = `biblio-${res.status}`;
  const ident = ref.identifier || (ref.title ? ref.title.slice(0, 70) : ref.raw.slice(0, 70));
  const detail = res.detail ? `<div class="biblio-detail">${escapeHtml(res.detail)}</div>` : "";
  return `
    <div class="biblio-row ${cls}">
      <div class="biblio-icon">${icon}</div>
      <div class="biblio-body">
        <div class="biblio-ident">[${ref.kind}] ${escapeHtml(ident)} <span class="biblio-line">L${ref.line}</span></div>
        ${detail}
      </div>
    </div>`;
}

function sleep(ms) { return new Promise((r) => setTimeout(r, ms)); }

async function verifyBibliography(text) {
  const t = I18N[UILANG];
  const refsPy = extractRefsFn(text);
  const refs = refsPy.toJs({ dict_converter: Object.fromEntries });
  refsPy.destroy();
  if (!refs || refs.length === 0) {
    appendBiblio(`<div class="biblio-empty">${t.biblio_none}</div>`);
    return;
  }
  appendBiblio(`<div class="biblio-header">${t.biblio_header.replace("{n}", refs.length)}</div>`);
  appendBiblio(`<div class="biblio-note">${t.biblio_privacy}</div>`);

  let fakes = 0;
  for (const r of refs) {
    let res;
    try {
      if (r.kind === "doi")        res = await verifyDoiJs(r.identifier);
      else if (r.kind === "arxiv") res = await verifyArxivJs(r.identifier);
      else if (r.kind === "citation") res = await verifyCitationJs(r);
      else                         res = { status: "unverifiable", detail: "" };
    } catch (e) {
      res = { status: "error", detail: e.message };
    }
    if (res.status === "not_found") fakes++;
    appendBiblio(renderBiblioRow(r, res));
    await sleep(300);
  }
  if (fakes > 0) {
    appendBiblio(
      `<div class="biblio-warning">${t.biblio_warning.replace("{fakes}", fakes).replace("{total}", refs.length)}</div>`
    );
  }
}

async function verifyDoiJs(doi) {
  const url = `https://api.crossref.org/works/${encodeURIComponent(doi)}`;
  try {
    const r = await fetch(url, { headers: { Accept: "application/json" } });
    if (r.status === 404) return { status: "not_found", detail: "CrossRef: not found" };
    if (!r.ok) return { status: "error", detail: `HTTP ${r.status}` };
    const d = await r.json();
    if (d.status !== "ok") return { status: "not_found", detail: "" };
    const m = d.message;
    const title = (m.title && m.title[0]) || "";
    const authors = m.author || [];
    const author = authors[0] ? (authors[0].family || authors[0].name || "") : "";
    let year = "";
    for (const k of ["published-print", "published-online", "issued"]) {
      const dp = m[k] && m[k]["date-parts"] && m[k]["date-parts"][0];
      if (dp && dp[0]) { year = String(dp[0]); break; }
    }
    let detail = title;
    if (author) detail = year ? `${author} (${year}) ${title}` : `${author}: ${title}`;
    return { status: "exists", detail };
  } catch (e) {
    return { status: "error", detail: e.message };
  }
}

async function verifyArxivJs(id) {
  const url = `https://export.arxiv.org/api/query?id_list=${encodeURIComponent(id)}`;
  try {
    const r = await fetch(url);
    if (!r.ok) return { status: "error", detail: `HTTP ${r.status}` };
    const text = await r.text();
    if (!text.includes("<entry>")) return { status: "not_found", detail: "arXiv: not found" };
    const m = text.match(/<entry>[\s\S]*?<title>([\s\S]*?)<\/title>/);
    const title = m ? m[1].replace(/\s+/g, " ").trim() : "";
    return { status: "exists", detail: title };
  } catch (e) {
    return { status: "error", detail: e.message };
  }
}

async function verifyCitationJs(ref) {
  if (!ref.title) return { status: "unverifiable", detail: "" };
  const q = ref.author ? `${ref.title} ${ref.author}` : ref.title;
  const url = `https://api.crossref.org/works?rows=1&query.bibliographic=${encodeURIComponent(q)}`;
  try {
    const r = await fetch(url, { headers: { Accept: "application/json" } });
    if (!r.ok) return { status: "error", detail: `HTTP ${r.status}` };
    const d = await r.json();
    const items = (d.message && d.message.items) || [];
    if (!items.length) return { status: "not_found", detail: "no match" };
    const item = items[0];
    const found = (item.title && item.title[0]) || "";
    const score = item.score || 0;
    const a = ref.title.toLowerCase().replace(/\W+/g, "");
    const b = found.toLowerCase().replace(/\W+/g, "");
    const sim = a && b && (a.includes(b) || b.includes(a));
    if (score >= 60 && sim) return { status: "exists", detail: `CrossRef: ${found}` };
    if (score >= 60) return { status: "not_found", detail: `título distinto: ${found}` };
    return { status: "not_found", detail: "sin match" };
  } catch (e) {
    return { status: "error", detail: e.message };
  }
}

// Drag & drop for .txt / .md / .docx files
function setupDnd() {
  const ta = els.input;
  ["dragenter", "dragover"].forEach((ev) =>
    ta.addEventListener(ev, (e) => {
      e.preventDefault();
      ta.classList.add("drag-over");
    })
  );
  ["dragleave", "drop"].forEach((ev) =>
    ta.addEventListener(ev, (e) => {
      e.preventDefault();
      ta.classList.remove("drag-over");
    })
  );
  ta.addEventListener("drop", async (e) => {
    const file = e.dataTransfer?.files?.[0];
    if (file) await handleFile(file);
  });
}

async function handleFile(file) {
  const t = I18N[UILANG];
  const name = file.name.toLowerCase();
  if (name.endsWith(".docx")) {
    return await annotateDocx(file);
  }
  const isText = ["text/plain", "text/markdown", ""].includes(file.type) ||
                 /\.(txt|md|markdown)$/i.test(file.name);
  if (!isText) {
    if (name.endsWith(".pdf")) {
      setStatus(t.pdf_browser_unsupported, true);
    } else {
      setStatus(`${t.error} ${file.name}`, true);
    }
    return;
  }
  const text = await file.text();
  els.input.value = text;
  await analyze();
}

async function annotateDocx(file) {
  const t = I18N[UILANG];
  if (!annotateDocxFn) {
    setStatus(t.booting, true);
    return;
  }
  els.analyzeBtn.disabled = true;

  // Same rotating animation as analyze() — feels alive while parsing the docx
  const baseSteps = t.analyzing_steps || [t.analyzing];
  const steps = [`${t.annotating} ${file.name}`, ...baseSteps];
  let i = 0;
  setStatus(`<span class="spin">●</span> ${steps[0]}`);
  const ticker = setInterval(() => {
    i = (i + 1) % steps.length;
    setStatus(`<span class="spin">●</span> ${steps[i]}`);
  }, 350);

  await new Promise((r) => setTimeout(r, 50));
  const startedAt = performance.now();

  try {
    const buf = new Uint8Array(await file.arrayBuffer());
    const py = annotateDocxFn(buf, els.langSel.value, els.strictSel.checked);
    const result = py.toJs({ dict_converter: Object.fromEntries });
    py.destroy();

    // Floor at ~1.5s — docx parsing is usually fast, so we let the animation breathe
    const elapsed = performance.now() - startedAt;
    if (elapsed < 1500) await new Promise((r) => setTimeout(r, 1500 - elapsed));
    clearInterval(ticker);

    const outBytes = new Uint8Array(result.bytes);
    const blob = new Blob([outBytes], {
      type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    });
    const url = URL.createObjectURL(blob);
    const outName = file.name.replace(/(\.docx)$/i, "-aismell$1");

    // Auto-trigger the download.
    const a = document.createElement("a");
    a.href = url;
    a.download = outName;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1500);

    // Render a summary in the result panel.
    const pct = Math.round(result.score * 100);
    const sev = severityClass(result.score);
    els.score.innerHTML = `
      <div class="score-top">
        <div class="pct ${sev}">${pct}%</div>
        <div class="meta">
          <strong>${severityLabel(result.score)}</strong> · ${result.sentences} ${t.sentences} ·
          ${result.findings} ${t.findings} · <span style="color: var(--hl);">${outName}</span>
        </div>
      </div>
    `;
    els.findings.innerHTML = `
      <div class="empty" style="color: var(--grn);">
        ${t.docx_done.replace("{name}", outName)}
      </div>
    `;
    els.resultPanel.hidden = false;
    setStatus(null);

    // Optional bibliography verification on docx text — needs source text.
    if (els.biblioSel && els.biblioSel.checked && extractRefsFn) {
      // We don't have raw text here; extract again via Pyodide from the bytes.
      // For now: pop a note. We add proper docx-text-extract later if needed.
    }
  } catch (err) {
    clearInterval(ticker);
    console.error(err);
    setStatus(`${t.error} ${err.message}`, true);
  } finally {
    els.analyzeBtn.disabled = false;
  }
}

setupDnd();

// File-input button
els.fileBtn.addEventListener("click", () => els.fileInput.click());
els.fileInput.addEventListener("change", async (e) => {
  const file = e.target.files?.[0];
  if (file) await handleFile(file);
  e.target.value = ""; // allow re-picking the same file
});

bootPyodide();
