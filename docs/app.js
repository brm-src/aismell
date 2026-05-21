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
      "tokenizando oraciones…",
      "buscando muletillas…",
      "midiendo ritmo de oraciones…",
      "olfateando conectores forzados…",
      "revisando calcos del inglés…",
      "detectando estructura editorial IA…",
      "calculando smell…",
      "armando reporte…",
    ],
    scan_hits: "{n} señales detectadas",
    show_more: "ver los otros {n}",
    show_less: "colapsar",
    download_docx_btn: "descargar archivo anotado",
    biblio_summary_label: "BIBLIOGRAFÍA",
    biblio_sum_total: "{n} referencias detectadas",
    biblio_sum_verified: "verificadas",
    biblio_sum_not_found: "sin coincidencia",
    biblio_sum_unverifiable: "sin DOI/ID",
    biblio_sum_error: "error de red",
    biblio_show_detail: "ver detalle por referencia",
    biblio_hide_detail: "colapsar",
    biblio_download_btn: "descargar reporte de citas (.txt)",
    biblio_disclaimer: "\"sin coincidencia\" significa que no se encontró en CrossRef ni arXiv — pueden ser fuentes legítimas sin indexar (libros, tesis, capítulos). Revisa a mano antes de concluir nada. \"sin DOI/ID\" no es problema: muchas citas válidas no tienen identificador.",
    verdict_label: "veredicto",
    verdict_ai: "probable IA",
    verdict_mixed: "mixto / asistido",
    verdict_human: "huele a humano",
    verdict_clean: "limpio",
    verdict_confidence: "confianza",
    verdict_conf_high: "alta",
    verdict_conf_med: "media",
    verdict_conf_low: "baja",
    verdict_summary_label: "por qué",
    verdict_reasons: {
      density: "densidad de marcas IA: {pct}% de las oraciones",
      repeats: "patrón \"{id}\" repetido {n} veces",
      structural: "{n} señales estructurales (encabezados, listas, dramatización)",
      severe: "{n} marcas de alta severidad",
      uniform_rhythm: "ritmo demasiado uniforme entre oraciones",
      length: "texto muy corto · veredicto incierto",
      clean: "no se detectaron patrones IA fuertes",
    },
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
    cliText: "¿Necesitas anotar archivos Word o PDF con highlights y comentarios? Hay una versión de terminal que hace eso.",
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
    docx_done: "Listo: <strong>{name}</strong> está armado. Bájalo cuando quieras, ábrelo en Word o LibreOffice. Las palabras detectadas como IA aparecen resaltadas en amarillo, y al costado verás un comentario explicando qué huele mal.",
    pdf_browser_unsupported: "PDF en la web aún no se puede (la librería no carga en el navegador). Para PDF usa el CLI: aismell paper.pdf --out paper-marcado.pdf",
    biblio: "verificar bibliografía",
    biblioTip: "Busca las referencias del texto (DOIs, papers, citas) y verifica si existen. La IA suele inventar bibliografía.",
    strictTip: "Filtra los avisos dudosos. Solo te muestra lo que casi seguro es IA.",
    biblio_header: "BIBLIOGRAFÍA — {n} REFERENCIAS",
    biblio_privacy: "Solo se envían los identificadores (DOI/arXiv/título) a CrossRef y arXiv. Tu texto no sale.",
    biblio_none: "no se detectaron referencias parseables",
    biblio_warning: "⚠  {fakes}/{total} referencias no se encontraron — posible IA inventando",
    high_smell_note: "Este texto suena bastante a IA. Si lo escribiste tú y quieres que suene más humano, los hallazgos arriba te orientan.",
    high_smell_cta: "edición humana con Intelecta",
    biblio_cta_note: "Bibliografía falsa en una tesis o paper no es un detalle: puede echar abajo una entrega.",
    biblio_cta_btn: "revisión académica con Intelecta",
    footer_brand: "herramienta abierta de <a href=\"https://intelecta.cl\" target=\"_blank\" rel=\"noopener\"><strong>Intelecta</strong></a>",
    footer_disclaimer: "descargo",
    disc_title: "descargo de responsabilidad",
    disc_body: `
      <h3>qué hace aismell</h3>
      <p>aismell busca patrones de escritura que la IA usa más que los humanos. Es una herramienta de <strong>orientación</strong>, no un veredicto.</p>

      <h3>qué NO es</h3>
      <p>No es un detector forense ni una prueba en juicios académicos. Los falsos positivos existen: muchas frases que marca también las usan personas reales, especialmente en textos académicos formales.</p>

      <h3>privacidad</h3>
      <p>Tu texto no sale de tu navegador. Todo el análisis corre localmente con Python (Pyodide) en tu pestaña. Si activas <strong>verificar bibliografía</strong>, solo se envían los identificadores (DOIs, IDs de arXiv, títulos cortos) a CrossRef y arXiv para confirmar si existen. El resto del texto se queda contigo.</p>

      <h3>uso responsable</h3>
      <p>No uses aismell para acusar a nadie de hacer trampa. Úsalo para revisar tu propia escritura, detectar muletillas, y decidir qué cambiar. Las instituciones que usen aismell para penalizar estudiantes lo hacen bajo su propia responsabilidad.</p>

      <h3>licencia</h3>
      <p>MIT. Código abierto. Sin garantía expresa o implícita. Úsalo bajo tu propio riesgo.</p>
    `,
    nudge_text: "Si aismell te ha sido útil, considera apoyarlo con un café.",
    nudge_btn: "☕ donar",
    nudge_dismiss: "no, gracias",
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
      "tokenizing sentences…",
      "matching filler phrases…",
      "measuring sentence rhythm…",
      "sniffing forced connectors…",
      "checking English calques…",
      "detecting AI editorial structure…",
      "scoring smell…",
      "building report…",
    ],
    scan_hits: "{n} signals detected",
    show_more: "show the other {n}",
    show_less: "collapse",
    download_docx_btn: "download annotated file",
    biblio_summary_label: "BIBLIOGRAPHY",
    biblio_sum_total: "{n} references detected",
    biblio_sum_verified: "verified",
    biblio_sum_not_found: "no match",
    biblio_sum_unverifiable: "no DOI/ID",
    biblio_sum_error: "network error",
    biblio_show_detail: "show per-reference detail",
    biblio_hide_detail: "collapse",
    biblio_download_btn: "download citation report (.txt)",
    biblio_disclaimer: "\"no match\" means it wasn't found in CrossRef or arXiv — these might still be legitimate sources not indexed there (books, theses, chapters). Check by hand before drawing conclusions. \"no DOI/ID\" is fine: lots of valid citations don't have one.",
    verdict_label: "verdict",
    verdict_ai: "likely AI",
    verdict_mixed: "mixed / assisted",
    verdict_human: "smells human",
    verdict_clean: "clean",
    verdict_confidence: "confidence",
    verdict_conf_high: "high",
    verdict_conf_med: "medium",
    verdict_conf_low: "low",
    verdict_summary_label: "why",
    verdict_reasons: {
      density: "AI-marker density: {pct}% of sentences flagged",
      repeats: "pattern \"{id}\" repeats {n} times",
      structural: "{n} structural signals (headings, lists, dramatic fragments)",
      severe: "{n} high-severity marks",
      uniform_rhythm: "sentence rhythm suspiciously uniform",
      length: "text too short — verdict uncertain",
      clean: "no strong AI patterns detected",
    },
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
    cliText: "Need to annotate Word or PDF files with highlights and comments? There's a terminal version that does that.",
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
    docx_done: "Ready: <strong>{name}</strong> is built. Download it whenever, open it in Word or LibreOffice. AI-flagged words are highlighted in yellow, with a margin comment explaining what smells off.",
    pdf_browser_unsupported: "PDF in the browser isn't supported yet (the library doesn't run in WASM). For PDF use the CLI: aismell paper.pdf --out paper-marked.pdf",
    biblio: "verify bibliography",
    biblioTip: "Finds the references in the text (DOIs, papers, citations) and checks if they exist. AI often invents bibliography.",
    strictTip: "Filters out the noisy hits. Only shows you what's almost certainly AI.",
    biblio_header: "BIBLIOGRAPHY — {n} REFERENCES",
    biblio_privacy: "Only identifiers (DOI/arXiv/title) are sent to CrossRef and arXiv. Your text stays local.",
    biblio_none: "no parseable references found",
    biblio_warning: "⚠  {fakes}/{total} references not found — possible AI hallucination",
    high_smell_note: "This text sounds strongly AI-written. If you wrote it and want it to sound more human, the findings above show where to edit.",
    high_smell_cta: "human editing by Intelecta",
    biblio_cta_note: "Fake bibliography in a thesis or paper is not a detail: it can sink a submission.",
    biblio_cta_btn: "academic review by Intelecta",
    footer_brand: "an open tool by <a href=\"https://intelecta.cl\" target=\"_blank\" rel=\"noopener\"><strong>Intelecta</strong></a>",
    footer_disclaimer: "disclaimer",
    disc_title: "disclaimer",
    disc_body: `
      <h3>what aismell does</h3>
      <p>aismell looks for writing patterns that AI uses more than humans. It's a <strong>guidance tool</strong>, not a verdict.</p>

      <h3>what it is NOT</h3>
      <p>It's not a forensic detector, and not evidence for academic misconduct cases. False positives happen: many phrases it flags are also used by real people, especially in formal academic writing.</p>

      <h3>privacy</h3>
      <p>Your text never leaves your browser. All analysis runs locally with Python (Pyodide) in your tab. If you enable <strong>verify bibliography</strong>, only the identifiers (DOIs, arXiv IDs, short titles) are sent to CrossRef and arXiv to confirm they exist. The rest of your text stays with you.</p>

      <h3>responsible use</h3>
      <p>Don't use aismell to accuse anyone of cheating. Use it to review your own writing, spot fillers, and decide what to change. Institutions that use aismell to penalize students do so at their own responsibility.</p>

      <h3>license</h3>
      <p>MIT. Open source. No express or implied warranty. Use at your own risk.</p>
    `,
    nudge_text: "If aismell has been useful to you, consider supporting it with a coffee.",
    nudge_btn: "☕ donate",
    nudge_dismiss: "not now",
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
  scanning: document.getElementById("scanning"),
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
let extractDocxTextFn = null;

function setStatus(msg, isError = false) {
  if (msg === null) {
    els.status.innerHTML = "";
    els.status.classList.remove("err");
    return;
  }
  els.status.innerHTML = msg;
  els.status.classList.toggle("err", isError);
}

// Big in-panel scanner with rotating step labels + live hit counter.
// Returns { advance(stepIndex), setHits(n,sentences), finish(), cancel() }.
function startScanning(steps, opts = {}) {
  const t = I18N[UILANG];
  const expectedMs = opts.expectedMs ?? 9000;
  const stepMs = Math.max(900, Math.floor(expectedMs / steps.length));

  // Hide previous results, show scanner inside the result panel
  els.score.innerHTML = "";
  els.findings.innerHTML = "";
  clearBiblio();
  els.resultPanel.hidden = false;
  els.scanning.hidden = false;
  els.scanning.innerHTML = `
    <div class="nose" aria-hidden="true">👃</div>
    <div class="label" role="status" aria-live="polite"></div>
    <div class="track"><div class="fill"></div></div>
    <div class="stats">
      <span class="pct">0%</span>
      <span class="hits">${(t.scan_hits || "señales").replace("{n}", "0")}</span>
    </div>`;
  const labelEl = els.scanning.querySelector(".label");
  const fillEl = els.scanning.querySelector(".fill");
  const pctEl = els.scanning.querySelector(".pct");
  const hitsEl = els.scanning.querySelector(".hits");

  let cancelled = false;
  let i = -1;

  function setStep(idx) {
    if (cancelled) return;
    if (idx === i || idx >= steps.length) return;
    i = idx;
    labelEl.style.opacity = "0";
    setTimeout(() => {
      if (cancelled) return;
      labelEl.textContent = steps[idx];
      labelEl.style.opacity = "1";
    }, 90);
    const pct = Math.min(92, Math.round(((idx + 1) / steps.length) * 92));
    fillEl.style.width = pct + "%";
    pctEl.textContent = pct + "%";
  }

  setStep(0);
  let next = 1;
  const ticker = setInterval(() => {
    if (cancelled) return;
    if (next >= steps.length - 1) return;
    setStep(next++);
  }, stepMs);

  return {
    advance(idx) { setStep(Math.min(idx, steps.length - 1)); },
    setHits(n) {
      if (cancelled || !hitsEl) return;
      hitsEl.textContent = (t.scan_hits || "señales").replace("{n}", String(n));
      hitsEl.classList.toggle("alert", n > 0);
    },
    async finish() {
      cancelled = true;
      clearInterval(ticker);
      if (!fillEl) return;
      labelEl.textContent = steps[steps.length - 1];
      fillEl.classList.add("done");
      fillEl.style.width = "100%";
      pctEl.textContent = "100%";
      await new Promise((r) => setTimeout(r, 320));
      els.scanning.hidden = true;
      els.scanning.innerHTML = "";
    },
    cancel() {
      cancelled = true;
      clearInterval(ticker);
      els.scanning.hidden = true;
      els.scanning.innerHTML = "";
    },
  };
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

def extract_docx_text(input_bytes):
    import io, zipfile
    from xml.etree import ElementTree as ET
    W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    with zipfile.ZipFile(io.BytesIO(bytes(input_bytes))) as z:
        xml = z.read("word/document.xml")
    root = ET.fromstring(xml)
    paras = []
    for p in root.iter(W + "p"):
        paras.append("".join(t.text or "" for t in p.iter(W + "t")))
    return "\\n".join(paras)
`);
    analyzeFn = pyodide.globals.get("run");
    annotateDocxFn = pyodide.globals.get("annotate_docx_bytes");
    extractRefsFn = pyodide.globals.get("extract_refs");
    extractDocxTextFn = pyodide.globals.get("extract_docx_text");
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

function renderIntelectaNudge(kind) {
  const t = I18N[UILANG];
  const note = kind === "biblio" ? t.biblio_cta_note : t.high_smell_note;
  const cta = kind === "biblio" ? t.biblio_cta_btn : t.high_smell_cta;
  const href = "https://intelecta.cl/cotizador";
  return `
    <div class="nudge intelecta-nudge" data-intelecta-nudge="${kind}">
      <span class="mark">${kind === "biblio" ? "🚨" : "⚠"}</span>
      <span class="text">${escapeHtml(note)}</span>
      <a href="${href}" target="_blank" rel="noopener">${escapeHtml(cta)}</a>
      <button type="button" class="dismiss" aria-label="cerrar">×</button>
    </div>`;
}

function dismissIntelectaNudge(btn) {
  const note = btn.closest(".intelecta-nudge");
  if (note) note.remove();
}

function escapeHtml(s) {
  return s
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function renderHit(hit, t) {
  // Compact context: ±60 chars around the match (was: whole paragraph).
  const CTX = 60;
  const start = Math.max(0, hit.col - CTX);
  const end = Math.min(hit.text.length, hit.end + CTX);
  const lead = start > 0 ? "… " : "";
  const tail = end < hit.text.length ? " …" : "";
  const before = escapeHtml(hit.text.slice(start, hit.col));
  const matched = escapeHtml(hit.text.slice(hit.col, hit.end));
  const after = escapeHtml(hit.text.slice(hit.end, end));
  let glyph = "·";
  if (hit.severity === 3) glyph = "🔴";
  else if (hit.severity === 2) glyph = "⚠";
  return `
    <div class="finding">
      <div class="glyph s-${hit.severity}">${glyph}</div>
      <div class="body">
        <div class="ctx">${lead}${before}<span class="match">${matched}</span>${after}${tail}</div>
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

function computeVerdict(report) {
  const t = I18N[UILANG];
  const reasons = [];
  const sentences = report.sentences || 0;
  const hits = report.hits || [];
  const structural = report.structural || [];

  // Density by sentence count (more reliable than by line — pasted text may be single-line).
  // hits-per-sentence ratio, capped at 100%.
  const denPct = sentences ? Math.min(100, (hits.length / sentences) * 100) : 0;

  // Severe count
  let severe = 0;
  for (const h of hits) if (h.severity === 3) severe++;
  for (const s of structural) if (s.severity === 3) severe++;

  // Repeated patterns (any id seen 3+ times = a tic)
  const counts = {};
  for (const h of hits) counts[h.id] = (counts[h.id] || 0) + 1;
  const repeats = Object.entries(counts)
    .filter(([, n]) => n >= 3)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 2);

  // Heuristic score (0..1)
  let h = 0;
  // Density: 0% -> 0, 30% -> 0.45, 60%+ -> 0.85
  h += Math.min(0.85, denPct / 70);
  // Repeats (each tic adds up to 0.15)
  h += Math.min(0.30, repeats.length * 0.15);
  // Severe marks
  h += Math.min(0.25, severe * 0.05);
  // Structural signals
  h += Math.min(0.20, structural.length * 0.05);
  // Blend with rule-based score
  h = h * 0.7 + report.score * 0.3;
  h = Math.max(0, Math.min(1, h));

  // Build reasons
  if (denPct >= 15 && hits.length >= 3) {
    reasons.push(t.verdict_reasons.density.replace("{pct}", Math.round(denPct)));
  }
  for (const [id, n] of repeats) {
    reasons.push(t.verdict_reasons.repeats.replace("{id}", id).replace("{n}", n));
  }
  if (structural.length >= 2) {
    reasons.push(t.verdict_reasons.structural.replace("{n}", structural.length));
  }
  if (severe >= 2 && reasons.length < 3) {
    reasons.push(t.verdict_reasons.severe.replace("{n}", severe));
  }

  // Verdict label + confidence
  let label, klass, conf, confKey;
  if (sentences < 3) {
    label = t.verdict_human;
    klass = "v-low";
    conf = t.verdict_conf_low;
    confKey = "low";
    reasons.length = 0;
    reasons.push(t.verdict_reasons.length);
  } else if (h >= 0.55) {
    label = t.verdict_ai;
    klass = "v-high";
    if (h >= 0.72 && reasons.length >= 2) { conf = t.verdict_conf_high; confKey = "high"; }
    else if (h >= 0.65) { conf = t.verdict_conf_med; confKey = "med"; }
    else { conf = t.verdict_conf_low; confKey = "low"; }
  } else if (h >= 0.28) {
    label = t.verdict_mixed;
    klass = "v-mid";
    conf = reasons.length >= 2 ? t.verdict_conf_med : t.verdict_conf_low;
    confKey = reasons.length >= 2 ? "med" : "low";
  } else if (hits.length === 0 && structural.length === 0) {
    label = t.verdict_clean;
    klass = "v-clean";
    conf = t.verdict_conf_med;
    confKey = "med";
    reasons.length = 0;
    reasons.push(t.verdict_reasons.clean);
  } else {
    label = t.verdict_human;
    klass = "v-low";
    conf = t.verdict_conf_med;
    confKey = "med";
    if (reasons.length === 0) reasons.push(t.verdict_reasons.clean);
  }

  return { label, klass, conf, confKey, reasons: reasons.slice(0, 3), heur: h };
}

function renderVerdict(report) {
  const t = I18N[UILANG];
  const v = computeVerdict(report);
  const reasonsHtml = v.reasons.map((r) => `<li>${escapeHtml(r)}</li>`).join("");
  return `
    <div class="verdict ${v.klass}">
      <div class="verdict-head">
        <div class="verdict-label">${t.verdict_label}</div>
        <div class="verdict-value">${escapeHtml(v.label)}</div>
        <div class="verdict-conf">${t.verdict_confidence}: <strong>${escapeHtml(v.conf)}</strong></div>
      </div>
      <div class="verdict-why">
        <div class="verdict-why-label">${t.verdict_summary_label}</div>
        <ul>${reasonsHtml}</ul>
      </div>
    </div>`;
}

function render(report) {
  const t = I18N[UILANG];
  const pct = Math.round(report.score * 100);
  const sev = severityClass(report.score);

  const totalFindings = report.hits.length + report.structural.length;

  let scoreHtml = renderVerdict(report) + `
    <div class="score-top">
      <div class="pct ${sev}">${pct}%</div>
      <div class="meta">
        <strong>${severityLabel(report.score)}</strong> · ${report.sentences} ${t.sentences} ·
        ${totalFindings} ${t.findings} · ${report.lang}
      </div>
    </div>`;

  if (report.score >= 0.6) {
    scoreHtml += renderIntelectaNudge("smell");
  }

  els.score.innerHTML = scoreHtml;

  if (report.hits.length === 0 && report.structural.length === 0) {
    els.findings.innerHTML = `<div class="clean">${t.clean}</div>`;
    els.resultPanel.hidden = false;
    return;
  }

  // Findings — collapsed summary by default, expandable to full list.
  const sorted = [...report.hits].sort((a, b) => (b.severity - a.severity) || (a.line - b.line));
  const TOP_N = 5;
  const top = sorted.slice(0, TOP_N);
  const rest = sorted.slice(TOP_N);

  // Severity counts (for the compact summary line)
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

  let html = `
    <div class="findings-summary">
      <span class="fs-count"><strong>${totalFindings}</strong> ${t.findings}</span>
      <span class="fs-sep">·</span>
      <span class="fs-sev s-high">${sevHigh} ${t.sev_high}</span>
      <span class="fs-sev s-mod">${sevMod} ${t.sev_mod}</span>
      <span class="fs-sev s-low">${sevLow} ${t.sev_low}</span>
    </div>`;

  if (top.length) {
    html += top.map((h) => renderHit(h, t)).join("");
  }
  if (rest.length) {
    const moreLbl = (t.show_more || "ver los otros {n}").replace("{n}", rest.length);
    const lessLbl = t.show_less || "colapsar";
    html += `
      <details class="findings-more">
        <summary>
          <span class="more-show">${moreLbl}</span>
          <span class="more-hide">${lessLbl}</span>
        </summary>
        ${rest.map((h) => renderHit(h, t)).join("")}
      </details>`;
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

  // Big in-panel scanner — visible budget ~9s, even on short text
  const steps = I18N[UILANG].analyzing_steps || [I18N[UILANG].analyzing];
  const minMs = 4500;
  const targetMs = 9000;
  const progress = startScanning(steps, { expectedMs: targetMs });
  setStatus(null);

  // Run sync code in a microtask so the spinner renders first
  await new Promise((r) => setTimeout(r, 50));
  const startedAt = performance.now();

  try {
    const res = analyzeFn(text, els.langSel.value, els.strictSel.checked);
    const obj = res.toJs({ dict_converter: Object.fromEntries });
    res.destroy();

    // Live hit count once analysis is back
    const totalHits = (obj.hits ? obj.hits.length : 0) + (obj.structural ? obj.structural.length : 0);
    progress.setHits(totalHits);

    // Floor at minMs so the user can read the steps even on tiny text
    const elapsed = performance.now() - startedAt;
    if (elapsed < minMs) await new Promise((r) => setTimeout(r, minMs - elapsed));
    await progress.finish();

    render(obj);

    // Optional: verify bibliography (network call to CrossRef/arXiv).
    if (els.biblioSel && els.biblioSel.checked && extractRefsFn) {
      await verifyBibliography(text);
    }

    bumpRunCount();
    maybeShowNudge();
  } catch (err) {
    progress.cancel();
    setStatus(`${I18N[UILANG].error} ${err.message}`, true);
    console.error(err);
  } finally {
    els.analyzeBtn.disabled = false;
  }
}

els.analyzeBtn.addEventListener("click", () => { clearBiblio(); analyze(); });
els.resultPanel.addEventListener("click", (e) => {
  if (e.target && e.target.matches(".intelecta-nudge .dismiss")) {
    dismissIntelectaNudge(e.target);
  }
});
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

  // Header + privacy note
  appendBiblio(`<div class="biblio-header">${t.biblio_summary_label} — ${t.biblio_sum_total.replace("{n}", refs.length)}</div>`);
  appendBiblio(`<div class="biblio-note">${t.biblio_privacy}</div>`);

  // Live progress placeholder
  appendBiblio(`<div id="biblio-progress" class="biblio-progress">verificando 0 / ${refs.length}…</div>`);
  const progEl = () => document.getElementById("biblio-progress");

  const results = [];
  for (let i = 0; i < refs.length; i++) {
    const r = refs[i];
    let res;
    try {
      if (r.kind === "doi")        res = await verifyDoiJs(r.identifier);
      else if (r.kind === "arxiv") res = await verifyArxivJs(r.identifier);
      else if (r.kind === "citation") res = await verifyCitationJs(r);
      else                         res = { status: "unverifiable", detail: "" };
    } catch (e) {
      res = { status: "error", detail: e.message };
    }
    results.push({ ref: r, res });
    if (progEl()) progEl().textContent = `verificando ${i + 1} / ${refs.length}…`;
    await sleep(180);
  }
  if (progEl()) progEl().remove();

  // Summary stats
  const counts = { exists: 0, not_found: 0, unverifiable: 0, error: 0 };
  for (const { res } of results) counts[res.status] = (counts[res.status] || 0) + 1;

  const summary = `
    <div class="biblio-summary">
      <span class="bs-cell ok"><strong>${counts.exists}</strong> ${t.biblio_sum_verified}</span>
      <span class="bs-cell warn"><strong>${counts.not_found}</strong> ${t.biblio_sum_not_found}</span>
      <span class="bs-cell dim"><strong>${counts.unverifiable}</strong> ${t.biblio_sum_unverifiable}</span>
      ${counts.error ? `<span class="bs-cell err"><strong>${counts.error}</strong> ${t.biblio_sum_error}</span>` : ""}
    </div>
    <div class="biblio-disclaimer">${t.biblio_disclaimer}</div>`;
  appendBiblio(summary);

  // Detail (collapsed)
  let detailHtml = "";
  for (const { ref, res } of results) detailHtml += renderBiblioRow(ref, res);
  appendBiblio(`
    <details class="biblio-detail-box">
      <summary>
        <span class="more-show">${t.biblio_show_detail}</span>
        <span class="more-hide">${t.biblio_hide_detail}</span>
      </summary>
      ${detailHtml}
    </details>`);

  // Download report
  const reportText = buildBiblioReport(results, t);
  const reportBlob = new Blob([reportText], { type: "text/plain;charset=utf-8" });
  const reportUrl = URL.createObjectURL(reportBlob);
  appendBiblio(`
    <div class="biblio-download">
      <a class="btn ghost" href="${reportUrl}" download="aismell-bibliografia.txt">⬇ ${t.biblio_download_btn}</a>
    </div>`);

  // Only nudge Intelecta when there's enough signal: 2+ "no match" AND ratio > 25%
  const ratio = counts.not_found / refs.length;
  if (counts.not_found >= 2 && ratio >= 0.25) {
    appendBiblio(renderIntelectaNudge("biblio"));
  }
}

function buildBiblioReport(results, t) {
  const lines = [];
  lines.push("aismell · reporte de bibliografía");
  lines.push("=".repeat(50));
  lines.push(`total: ${results.length}`);
  const stats = { exists: 0, not_found: 0, unverifiable: 0, error: 0 };
  for (const { res } of results) stats[res.status] = (stats[res.status] || 0) + 1;
  lines.push(`verificadas: ${stats.exists}`);
  lines.push(`sin coincidencia (CrossRef/arXiv): ${stats.not_found}`);
  lines.push(`sin DOI/ID: ${stats.unverifiable}`);
  if (stats.error) lines.push(`error de red: ${stats.error}`);
  lines.push("");
  lines.push("nota: \"sin coincidencia\" no equivale a falsa. Libros, tesis,");
  lines.push("capítulos y publicaciones locales muchas veces no están indexados");
  lines.push("en CrossRef o arXiv. Verifica a mano antes de concluir nada.");
  lines.push("");
  lines.push("-".repeat(50));
  for (const { ref, res } of results) {
    lines.push(`L${ref.line} [${ref.kind}] ${ref.identifier || ref.title || ref.raw}`);
    lines.push(`  estado: ${res.status}${res.detail ? " · " + res.detail : ""}`);
    lines.push("");
  }
  return lines.join("\n");
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
  if (!annotateDocxFn || !analyzeFn) {
    setStatus(t.booting, true);
    return;
  }
  els.analyzeBtn.disabled = true;

  // Big in-panel scanner — same animation as paste-text flow
  const steps = t.analyzing_steps || [t.analyzing];
  const minMs = 4500;
  const targetMs = 9000;
  const progress = startScanning(steps, { expectedMs: targetMs });
  setStatus(null);

  await new Promise((r) => setTimeout(r, 50));
  const startedAt = performance.now();

  try {
    const buf = new Uint8Array(await file.arrayBuffer());

    // 1) Extract plain text from the .docx so we can run the same analysis
    //    as paste-text and show a real verdict.
    let extractedText = "";
    if (extractDocxTextFn) {
      try {
        extractedText = extractDocxTextFn(buf) || "";
      } catch (e) {
        console.warn("extract_docx_text failed", e);
      }
    }

    // 2) Run analysis on the extracted text (drives the verdict + summary)
    let report = null;
    if (extractedText.trim()) {
      const res = analyzeFn(extractedText, els.langSel.value, els.strictSel.checked);
      report = res.toJs({ dict_converter: Object.fromEntries });
      res.destroy();
      const totalHits = (report.hits ? report.hits.length : 0) + (report.structural ? report.structural.length : 0);
      progress.setHits(totalHits);
    }

    // 3) Annotate the .docx (highlights + comments)
    const py = annotateDocxFn(buf, els.langSel.value, els.strictSel.checked);
    const result = py.toJs({ dict_converter: Object.fromEntries });
    py.destroy();

    // Floor at minMs so the scanner animation breathes
    const elapsed = performance.now() - startedAt;
    if (elapsed < minMs) await new Promise((r) => setTimeout(r, minMs - elapsed));
    await progress.finish();

    // 4) Render the same verdict/score panel as paste-text flow,
    //    then add a docx-specific footer with the download link.
    const outBytes = new Uint8Array(result.bytes);
    const blob = new Blob([outBytes], {
      type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    });
    const url = URL.createObjectURL(blob);
    const outName = file.name.replace(/(\.docx)$/i, "-aismell$1");

    if (report) {
      // Stash the input text so the bibliography toggle works on .docx too.
      els.input.value = extractedText;
      render(report);
    } else {
      // Fallback: no extracted text — show minimal score panel
      const pct = Math.round(result.score * 100);
      const sev = severityClass(result.score);
      els.score.innerHTML = `
        <div class="score-top">
          <div class="pct ${sev}">${pct}%</div>
          <div class="meta">
            <strong>${severityLabel(result.score)}</strong> · ${result.sentences} ${t.sentences} ·
            ${result.findings} ${t.findings}
          </div>
        </div>`;
      els.findings.innerHTML = "";
      els.resultPanel.hidden = false;
    }

    // 5) Append a download bar at the top of findings — manual click, no auto-download.
    const downloadHtml = `
      <div class="docx-download">
        <div class="docx-download-text">
          ${t.docx_done.replace("{name}", `<strong>${escapeHtml(outName)}</strong>`)}
        </div>
        <a class="btn" id="docxDownloadBtn" href="${url}" download="${escapeHtml(outName)}">⬇ ${escapeHtml(t.download_docx_btn || outName)}</a>
      </div>`;
    els.findings.insertAdjacentHTML("afterbegin", downloadHtml);

    // Keep the blob alive for a couple of minutes so the user can click when ready.
    setTimeout(() => URL.revokeObjectURL(url), 120000);

    setStatus(null);

    // Optional: bibliography verification on the extracted text
    if (extractedText.trim() && els.biblioSel && els.biblioSel.checked && extractRefsFn) {
      await verifyBibliography(extractedText);
    }

    bumpRunCount();
    maybeShowNudge();
  } catch (err) {
    progress.cancel();
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

// ---------- Disclaimer modal ----------
const disclaimerModal = document.getElementById("disclaimerModal");
const disclaimerBtn = document.getElementById("disclaimerBtn");
function openDisclaimer() { disclaimerModal.hidden = false; document.body.style.overflow = "hidden"; }
function closeDisclaimer() { disclaimerModal.hidden = true; document.body.style.overflow = ""; }
if (disclaimerBtn) disclaimerBtn.addEventListener("click", openDisclaimer);
disclaimerModal.querySelector(".close").addEventListener("click", closeDisclaimer);
disclaimerModal.addEventListener("click", (e) => {
  if (e.target === disclaimerModal) closeDisclaimer();
});
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && !disclaimerModal.hidden) closeDisclaimer();
});

// ---------- Donation nudge (non-invasive) ----------
// Shows after the user has run analyze 3+ times, only once, and never again
// after dismiss/donate. Uses localStorage; clears nothing else.
const NUDGE_THRESHOLD = 3;
const NUDGE_KEY = "aismell.nudge";   // "shown" | "dismissed"
const COUNT_KEY = "aismell.runs";

function bumpRunCount() {
  try {
    const n = parseInt(localStorage.getItem(COUNT_KEY) || "0", 10) + 1;
    localStorage.setItem(COUNT_KEY, String(n));
    return n;
  } catch (_) { return 0; }
}

function maybeShowNudge() {
  let state, count;
  try {
    state = localStorage.getItem(NUDGE_KEY);
    count = parseInt(localStorage.getItem(COUNT_KEY) || "0", 10);
  } catch (_) { return; }
  if (state) return;                 // already shown or dismissed
  if (count < NUDGE_THRESHOLD) return;
  if (document.getElementById("nudge")) return;

  const t = I18N[UILANG];
  const div = document.createElement("div");
  div.className = "nudge";
  div.id = "nudge";
  div.innerHTML = `
    <span class="heart">♥</span>
    <span>${t.nudge_text}</span>
    <a href="https://ko-fi.com/brmcl" target="_blank" rel="noopener">${t.nudge_btn}</a>
    <button type="button" class="dismiss" aria-label="dismiss">${t.nudge_dismiss}</button>
  `;
  document.querySelector("main").appendChild(div);
  div.querySelector(".dismiss").addEventListener("click", () => {
    try { localStorage.setItem(NUDGE_KEY, "dismissed"); } catch (_) {}
    div.remove();
  });
  div.querySelector("a").addEventListener("click", () => {
    try { localStorage.setItem(NUDGE_KEY, "donated"); } catch (_) {}
  });
  try { localStorage.setItem(NUDGE_KEY, "shown"); } catch (_) {}
}

bootPyodide();
