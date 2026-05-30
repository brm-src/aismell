// aismell web app — runs the real Python core via Pyodide in your browser.
// Your text never leaves the page.

const I18N = {
  es: {
    title: "aismell",
    tagline: "Olfatea si tu texto suena demasiado a IA. Y si trae bibliografía, revisa que no sea inventada.",
    examples_lbl: "probar con ejemplo:",
    example_ai: "texto IA",
    example_human: "texto humano",
    example_fakebib: "bibliografía falsa",
    about_toggle: "qué hace, qué no hace, cli",
    tagline_biblio: "Las citas viajan a CrossRef, OpenAlex, Google Books y otras fuentes públicas. El resto del texto se queda contigo.",
    how_title: "cómo funciona",
    how_layer1: "<strong>Patrones de frase.</strong> Muletillas, conectores forzados, calcos del inglés.<small>Regex auditable, sin caja negra.</small>",
    how_layer2: "<strong>Estructura.</strong> Encabezados decorativos, listas simétricas, fragmentos dramáticos.<small>Lo que delata un texto editorialmente \"armado\" por IA.</small>",
    how_layer3: "<strong>Ritmo y forma.</strong> Largo de oraciones demasiado uniforme, cadencia plana.<small>Los humanos varían más; los modelos tienden al promedio.</small>",
    how_score: "Tres capas combinadas dan un <strong>score de 0 a 100</strong> y un veredicto: limpio, mixto, o probable IA.",
    biblio_note_inline: "Al activar esto, solo las citas (DOI / título / autor / arXiv ID) se consultan en CrossRef, OpenAlex, Semantic Scholar, arXiv, Google Books y OpenLibrary. El resto del texto no sale de tu navegador.",
    boot: "afinando el olfato…",
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
      "cargando modelo semántico…",
      "midiendo cohesión entre párrafos…",
      "calculando smell…",
      "armando reporte…",
    ],
    scan_hits: "{n} señales detectadas",
    show_more: "ver los otros {n}",
    show_less: "colapsar",
    download_docx_btn: "descarga el archivo comentado",
    biblio_summary_label: "VERIFICANDO BIBLIOGRAFÍA",
    biblio_check_running: "cruzando cada cita con CrossRef, OpenAlex, Google Books y otras fuentes públicas para confirmar si existe.",
    biblio_progress_starting: "abriendo conexión con fuentes públicas…",
    biblio_progress_checking: "olfateando: {title}",
    biblio_progress_done: "listo. cruzando datos…",
    biblio_sum_total: "{n} referencias detectadas",
    biblio_sum_verified: "verificadas",
    biblio_sum_not_found: "sin coincidencia",
    biblio_sum_unverifiable: "sin DOI/ID",
    biblio_sum_error: "error de red",
    biblio_show_detail: "ver detalle por referencia",
    biblio_hide_detail: "colapsar",
    biblio_download_btn: "descargar reporte (.html)",
    biblio_view_btn: "ver reporte",
    biblio_rep_title: "reporte de bibliografía",
    biblio_rep_print: "imprimir / guardar PDF",
    biblio_rep_detail_title: "detalle por referencia",
    biblio_rep_footer: "todo corre en tu navegador",
    biblio_rep_verdict_high: "bibliografía sospechosa",
    biblio_rep_verdict_mid: "revisar a mano",
    biblio_rep_verdict_clean: "todas las citas verificadas",
    biblio_rep_reason_high: "{n} de {total} referencias no se encontraron en ninguna fuente. Revisa una por una antes de entregar el texto: la IA suele inventar citas con apariencia académica.",
    biblio_rep_reason_mid: "{n} de {total} sin coincidencia. No equivale a inventadas (libros, tesis y publicaciones locales pueden no estar indexadas), pero merecen revisión manual.",
    biblio_rep_reason_clean: "Todas las referencias detectadas se confirmaron en CrossRef, OpenAlex, Semantic Scholar, arXiv, Google Books u OpenLibrary.",
    biblio_disclaimer: "\"sin coincidencia\" significa que no se encontró en ninguna fuente (CrossRef, OpenAlex, Semantic Scholar, arXiv, Google Books, OpenLibrary). Igual pueden ser fuentes legítimas no indexadas (tesis, capítulos, ediciones locales). Revisa a mano antes de concluir nada. \"sin DOI/ID\" no es problema: muchas citas válidas no tienen identificador.",
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
    whyText: "aismell lee tu texto y marca línea por línea tres tipos de pista: muletillas y conectores forzados, estructura editorial (encabezados, listas simétricas, fragmentos dramáticos) y ritmo plano de oraciones. Las tres juntas dan un score de 0 a 100 y un veredicto: limpio, mixto o probable IA. Si detecta bibliografía, las citas se cruzan con fuentes públicas para confirmar si existen.",
    not: "qué NO hace",
    not1: "<strong>No reescribe tu texto.</strong> Tú decides qué cambiar.",
    not2: "<strong>No promete burlar detectores.</strong> Ese juego es scam.",
    not3: "<strong>No es forense.</strong> Falsos positivos pasan; humanos también usan estas frases.",
    cli: "también CLI",
    cliText: "¿Trabajas con PDFs? Hay una versión CLI que anota Word y PDF con highlights y comentarios al margen. <a href=\"https://github.com/brm-src/aismell#cli\" target=\"_blank\" rel=\"noopener\">Ver en GitHub</a>.",
    donate: "☕ donar",
    donateNote: "Si te sirvió, considera donarme. Lo mantengo solo, sin tracking, cobros ni APIs.",
    placeholder: "Pega tu texto, o suelta un archivo (.txt / .md / .docx / .pdf).",
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
    pdf_extracting: "extrayendo texto del PDF…",
    pdf_no_text: "El PDF no tiene capa de texto (probablemente escaneado). Sin OCR no puedo leerlo. Para PDFs escaneados usa el CLI con OCR.",
    biblio: "verificar bibliografía",
    biblioTip: "Busca las referencias del texto (DOIs, papers, libros, citas) y verifica si existen en CrossRef, OpenAlex, Google Books y otras fuentes. La IA suele inventar bibliografía.",
    strictTip: "Filtra los avisos dudosos. Solo te muestra lo que casi seguro es IA.",
    biblio_header: "BIBLIOGRAFÍA — {n} REFERENCIAS",
    biblio_privacy: "Solo se envían los identificadores (DOI / título / autor / arXiv ID) a CrossRef, OpenAlex, Semantic Scholar, arXiv, Google Books y OpenLibrary. Tu texto no sale.",
    biblio_none: "no se detectaron referencias parseables",
    biblio_warning: "⚠  {fakes}/{total} referencias no se encontraron — posible IA inventando",
    high_smell_note: "Este texto suena bastante a IA. Si lo escribiste tú y quieres que suene más humano, los hallazgos arriba te orientan.",
    high_smell_cta: "edición humana con Intelecta",
    biblio_cta_note: "Bibliografía falsa en una tesis o paper no es un detalle: puede echar abajo una entrega.",
    biblio_cta_btn: "revisión académica con Intelecta",
    footer_brand: "herramienta abierta de <a href=\"https://intelecta.cl\" target=\"_blank\" rel=\"noopener\"><strong>Intelecta</strong></a>",
    footer_disclaimer: "descargo",
    footer_about: "sobre",
    about_title: "sobre mí y sobre el sitio",
    about_body: `
      <p>Eterno estudiante. Lector que entiende el 50% de lo que lee y vuelve igual al mismo libro un par de años después como si fuera otro. Saco fotos cuando puedo, escribo cuando me sale. Asesoro a tesistas en redacción y corrección de estilo. Si necesitas ese tipo de apoyo, los servicios profesionales están en <a href="https://intelecta.cl" target="_blank" rel="noopener">intelecta.cl</a>.</p>

      <h3>creé esto porque la IA no sabe escribir</h3>
      <p><strong>Técnicamente:</strong> los modelos de lenguaje predicen, token a token, cuál es la palabra estadísticamente más probable dado un contexto. No razonan, no tienen criterio, no tienen voz. Es estadística aplicada a secuencias de texto, y el resultado suena fluido porque fluidez es exactamente lo que el modelo optimiza.</p>
      <p><strong>En la práctica:</strong> los patrones son reconocibles. Las frases que abren con "Es fundamental…", los listados de tres puntos, las conclusiones que no concluyen nada, el entusiasmo genérico sobre cualquier tema. Y eso sin contar la alucinación: la IA inventa citas, autores y datos con una confianza impecable.</p>

      <p>aismell no reescribe tu texto. Marca lo que no suena humano y te da algo concreto sobre lo que trabajar. La voz sigue siendo tuya.</p>

      <p class="about-foot">Si te sirvió, <a href="https://ko-fi.com/brmcl" target="_blank" rel="noopener">considera donarme</a> ☕<br>Escríbeme a <code>[tu@correo]</code></p>
    `,
    disc_title: "descargo de responsabilidad",
    disc_body: `
      <h3>qué hace aismell</h3>
      <p>aismell busca patrones de escritura que la IA usa más que los humanos. Es una herramienta de <strong>orientación</strong>, no un veredicto.</p>

      <h3>qué NO es</h3>
      <p>No es un detector forense ni una prueba en juicios académicos. Los falsos positivos existen: muchas frases que marca también las usan personas reales, especialmente en textos académicos formales.</p>

      <h3>privacidad</h3>
      <p>Tu texto no sale de tu navegador. Todo el análisis corre localmente con Python (Pyodide) en tu pestaña. Si activas <strong>verificar bibliografía</strong>, solo se envían los identificadores (DOIs, IDs de arXiv, títulos y autores) a CrossRef, OpenAlex, Semantic Scholar, arXiv, Google Books y OpenLibrary para confirmar si existen. El resto del texto se queda contigo.</p>

      <h3>uso responsable</h3>
      <p>No uses aismell para acusar a nadie de hacer trampa. Úsalo para revisar tu propia escritura, detectar muletillas, y decidir qué cambiar. Las instituciones que usen aismell para penalizar estudiantes lo hacen bajo su propia responsabilidad.</p>

      <h3>licencia</h3>
      <p>MIT. Código abierto. Sin garantía expresa o implícita. Úsalo bajo tu propio riesgo.</p>
    `,
    nudge_text: "Si te sirvió, considera donarme. Lo mantengo solo, sin tracking, cobros ni APIs.",
    nudge_btn: "☕ donar",
    nudge_dismiss: "no, gracias",
  },
  en: {
    title: "aismell",
    tagline: "Sniffs whether your text sounds too AI. And if it has a bibliography, checks that it isn't made up.",
    examples_lbl: "try with sample:",
    example_ai: "ai text",
    example_human: "human text",
    example_fakebib: "fake bibliography",
    about_toggle: "what it does, what it doesn't, cli",
    tagline_biblio: "Citations travel to CrossRef, OpenAlex, Google Books and other public sources. The rest of your text stays with you.",
    how_title: "how it works",
    how_layer1: "<strong>Phrase patterns.</strong> Filler phrases, forced connectors, English calques.<small>Auditable regex, no black box.</small>",
    how_layer2: "<strong>Structure.</strong> Decorative headings, symmetric lists, dramatic fragments.<small>What gives away an editorially AI-built text.</small>",
    how_layer3: "<strong>Rhythm & shape.</strong> Sentence length too uniform, flat cadence.<small>Humans vary more; models pull toward the mean.</small>",
    how_score: "The three layers combined produce a <strong>0–100 score</strong> and a verdict: clean, mixed, or likely AI.",
    biblio_note_inline: "When this is on, only the citations (DOI / title / author / arXiv ID) are queried against CrossRef, OpenAlex, Semantic Scholar, arXiv, Google Books and OpenLibrary. The rest of your text stays in your browser.",
    boot: "warming up the nose…",
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
      "loading semantic model…",
      "measuring paragraph cohesion…",
      "scoring smell…",
      "building report…",
    ],
    scan_hits: "{n} signals detected",
    show_more: "show the other {n}",
    show_less: "collapse",
    download_docx_btn: "download commented file",
    biblio_summary_label: "VERIFYING BIBLIOGRAPHY",
    biblio_check_running: "cross-checking every citation against CrossRef, OpenAlex, Google Books and other public sources to confirm it exists.",
    biblio_progress_starting: "opening connection to public sources…",
    biblio_progress_checking: "sniffing: {title}",
    biblio_progress_done: "done. crunching data…",
    biblio_sum_total: "{n} references detected",
    biblio_sum_verified: "verified",
    biblio_sum_not_found: "no match",
    biblio_sum_unverifiable: "no DOI/ID",
    biblio_sum_error: "network error",
    biblio_show_detail: "show per-reference detail",
    biblio_hide_detail: "collapse",
    biblio_download_btn: "download report (.html)",
    biblio_view_btn: "view report",
    biblio_rep_title: "bibliography report",
    biblio_rep_print: "print / save as PDF",
    biblio_rep_detail_title: "per-reference detail",
    biblio_rep_footer: "runs entirely in your browser",
    biblio_rep_verdict_high: "suspicious bibliography",
    biblio_rep_verdict_mid: "manual check needed",
    biblio_rep_verdict_clean: "all citations verified",
    biblio_rep_reason_high: "{n} of {total} references couldn't be matched in any source. Review them one by one before submitting: AI often invents citations that look academically plausible.",
    biblio_rep_reason_mid: "{n} of {total} with no match. This doesn't mean they're fake (books, theses, local publications may not be indexed), but they deserve a manual check.",
    biblio_rep_reason_clean: "All detected references were confirmed in CrossRef, OpenAlex, Semantic Scholar, arXiv, Google Books or OpenLibrary.",
    biblio_disclaimer: "\"no match\" means it wasn't found in any source (CrossRef, OpenAlex, Semantic Scholar, arXiv, Google Books, OpenLibrary). It may still be a legitimate non-indexed source (theses, chapters, regional editions). Check by hand before drawing conclusions. \"no DOI/ID\" is fine: lots of valid citations don't have one.",
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
    whyText: "aismell reads your text and flags three kinds of cues line by line: filler phrases and forced connectors, editorial structure (decorative headings, symmetric lists, dramatic fragments) and flat sentence rhythm. Together they yield a 0-to-100 score and a verdict: clean, mixed or likely AI. If a bibliography is detected, citations are cross-checked against public sources to confirm they exist.",
    not: "what it does NOT do",
    not1: "<strong>Does not rewrite your text.</strong> You decide what to change.",
    not2: "<strong>Does not promise to bypass detectors.</strong> That game is a scam.",
    not3: "<strong>Not forensic.</strong> False positives happen; humans use these phrases too.",
    cli: "also a CLI",
    cliText: "Working with PDFs? There's a CLI version that annotates Word and PDF with highlights and margin comments. <a href=\"https://github.com/brm-src/aismell#cli\" target=\"_blank\" rel=\"noopener\">See on GitHub</a>.",
    donate: "☕ donate",
    donateNote: "If it helped, consider donating. I maintain it solo — no tracking, no fees, no APIs.",
    placeholder: "Paste text, or drop a file (.txt / .md / .docx / .pdf).",
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
    pdf_extracting: "extracting text from PDF…",
    pdf_no_text: "This PDF has no text layer (probably scanned). Without OCR I can't read it. Use the CLI with OCR for scanned PDFs.",
    biblio: "verify bibliography",
    biblioTip: "Finds the references in the text (DOIs, papers, books, citations) and checks them against CrossRef, OpenAlex, Google Books and other sources. AI often invents bibliography.",
    strictTip: "Filters out the noisy hits. Only shows you what's almost certainly AI.",
    biblio_header: "BIBLIOGRAPHY — {n} REFERENCES",
    biblio_privacy: "Only the identifiers (DOI / title / author / arXiv ID) are sent to CrossRef, OpenAlex, Semantic Scholar, arXiv, Google Books and OpenLibrary. Your text stays local.",
    biblio_none: "no parseable references found",
    biblio_warning: "⚠  {fakes}/{total} references not found — possible AI hallucination",
    high_smell_note: "This text sounds strongly AI-written. If you wrote it and want it to sound more human, the findings above show where to edit.",
    high_smell_cta: "human editing by Intelecta",
    biblio_cta_note: "Fake bibliography in a thesis or paper is not a detail: it can sink a submission.",
    biblio_cta_btn: "academic review by Intelecta",
    footer_brand: "an open tool by <a href=\"https://intelecta.cl\" target=\"_blank\" rel=\"noopener\"><strong>Intelecta</strong></a>",
    footer_disclaimer: "disclaimer",
    footer_about: "about",
    about_title: "about me and this site",
    about_body: `
      <p>Eternal student. Reader who understands maybe 50% of what he reads and comes back to the same book a couple of years later as if it were a different one. I take photos when I can, I write when it comes. I help thesis writers with editing and style. If you need that kind of support, the professional services are at <a href="https://intelecta.cl" target="_blank" rel="noopener">intelecta.cl</a>.</p>

      <h3>I made this because AI can't write</h3>
      <p><strong>Technically:</strong> language models predict, token by token, the statistically most likely next word given a context. They don't reason, they don't have judgment, they don't have a voice. It's statistics applied to text sequences, and the result sounds fluent because fluency is exactly what the model optimizes for.</p>
      <p><strong>In practice:</strong> the patterns are recognizable. Sentences that open with "It's essential…", three-point lists, conclusions that don't conclude anything, the generic enthusiasm about any topic. And that's without counting hallucination: AI invents citations, authors and data with impeccable confidence.</p>

      <p>aismell doesn't rewrite your text. It flags what doesn't sound human and gives you something concrete to work on. The voice is still yours.</p>

      <p class="about-foot">If it helped, <a href="https://ko-fi.com/brmcl" target="_blank" rel="noopener">consider donating</a> ☕<br>Write to me at <code>[your@email]</code></p>
    `,
    disc_title: "disclaimer",
    disc_body: `
      <h3>what aismell does</h3>
      <p>aismell looks for writing patterns that AI uses more than humans. It's a <strong>guidance tool</strong>, not a verdict.</p>

      <h3>what it is NOT</h3>
      <p>It's not a forensic detector, and not evidence for academic misconduct cases. False positives happen: many phrases it flags are also used by real people, especially in formal academic writing.</p>

      <h3>privacy</h3>
      <p>Your text never leaves your browser. All analysis runs locally with Python (Pyodide) in your tab. If you enable <strong>verify bibliography</strong>, only the identifiers (DOIs, arXiv IDs, titles and authors) are sent to CrossRef, OpenAlex, Semantic Scholar, arXiv, Google Books and OpenLibrary to confirm they exist. The rest of your text stays with you.</p>

      <h3>responsible use</h3>
      <p>Don't use aismell to accuse anyone of cheating. Use it to review your own writing, spot fillers, and decide what to change. Institutions that use aismell to penalize students do so at their own responsibility.</p>

      <h3>license</h3>
      <p>MIT. Open source. No express or implied warranty. Use at your own risk.</p>
    `,
    nudge_text: "If it helped, consider donating. I maintain it solo — no tracking, no fees, no APIs.",
    nudge_btn: "☕ donate",
    nudge_dismiss: "not now",
  },
};

const els = {
  status: document.getElementById("status"),
  input: document.getElementById("input"),
  langSel: document.getElementById("langSel"),
  strictSel: document.getElementById("strictSel"),
  biblioSel: null,
  biblioInlineNote: null,
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
  const prev = UILANG;
  UILANG = t.dataset.lang;
  applyI18n();
  // Re-translate the status line if it's currently the "ready" message
  if (els.status && els.status.textContent.trim() === I18N[prev].ready) {
    setStatus(I18N[UILANG].ready);
  }
});
applyI18n();

// Biblio checkbox removed (now always-on); leave dead handler block as no-op
if (els.biblioSel && els.biblioInlineNote) {
  // intentionally empty — checkbox no longer exists
}

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
    setModelProgress(ratio, fileName) {
      if (cancelled || !labelEl || !fillEl) return;
      const pct = Math.round(ratio * 100);
      const file = fileName ? ` (${fileName})` : "";
      labelEl.textContent = (UILANG === "es"
        ? `descargando modelo semántico${file}: ${pct}%`
        : `downloading semantic model${file}: ${pct}%`);
      // Visually wire model download to the bar between 70% and 92%.
      const bar = 70 + Math.round(ratio * 22);
      fillEl.style.width = bar + "%";
      pctEl.textContent = bar + "%";
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
from aismell.biblio import find_references, score_apa_reference
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
        "sections": [],
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
    for sec in report.sections:
        out["sections"].append({
            "name": sec.name,
            "score": sec.score,
            "sentences": sec.sentences,
            "reasons": sec.reasons,
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
        apa = score_apa_reference(r) if r.kind == "citation" else None
        out.append({
            "kind": r.kind,
            "raw": r.raw,
            "line": r.line,
            "identifier": r.identifier,
            "title": r.title,
            "year": r.year,
            "author": r.author,
            "apa_score": apa.score if apa else None,
            "apa_status": apa.status if apa else "",
            "apa_issues": apa.issues if apa else [],
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
    // Silently start downloading the embedding model in the background
    // so the first analysis doesn't block waiting for ~120 MB.
    // No UI side-effects: errors are swallowed; analyze() will retry.
    import("./embedding-analysis.js")
      .then((m) => m.preloadEmbeddings())
      .catch(() => {});
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
        <div class="meta">${escapeHtml(hit.message)}</div>
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

  // Sections (apertura/cuerpo/cierre) intentionally removed —
  // their per-section scorer was inconsistent with the global one
  // (could read 0% per section while the global verdict was 100%).

  if (report.score >= 0.6) {
    scoreHtml += renderIntelectaNudge("smell");
  }

  els.score.innerHTML = scoreHtml;

  if (report.hits.length === 0 && report.structural.length === 0) {
    els.findings.innerHTML = `<div class="clean">${t.clean}</div>`;
    els.resultPanel.hidden = false;
    return;
  }

  // Findings — collapsed by default, expandable to full list.
  const sorted = [...report.hits].sort((a, b) => (b.severity - a.severity) || (a.line - b.line));

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

  const detailLbl = (UILANG === "es") ? "ver detalle de hallazgos" : "show finding details";
  const detailHide = (UILANG === "es") ? "colapsar" : "collapse";

  let html = `
    <div class="findings-summary">
      <span class="fs-count"><strong>${totalFindings}</strong> ${t.findings}</span>
      <span class="fs-sep">·</span>
      <span class="fs-sev s-high">${sevHigh} ${t.sev_high}</span>
      <span class="fs-sev s-mod">${sevMod} ${t.sev_mod}</span>
      <span class="fs-sev s-low">${sevLow} ${t.sev_low}</span>
    </div>
    <details class="findings-more">
      <summary>
        <span class="more-show">${detailLbl}</span>
        <span class="more-hide">${detailHide}</span>
      </summary>
      ${sorted.map((h) => renderHit(h, t)).join("")}
      ${report.structural.length ? `<div class="finding" style="border-bottom: 1px dashed var(--line); color: var(--dim); font-size: 12px; text-transform: uppercase; letter-spacing: 1px; margin-top: 14px;"><div></div><div>${t.structural}</div></div>` : ""}
      ${report.structural.map((s) => renderStructural(s, t)).join("")}
    </details>`;

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

    // Carril 2 — semantic embedding analysis (browser-side, after Python core).
    // Augments findings; never sends text out. First run downloads ~120 MB model
    // and caches it in IndexedDB.
    try {
      progress.advance(7);
      const { analyzeEmbeddings, onModelProgress } = await import("./embedding-analysis.js");
      const offProgress = onModelProgress((evt) => {
        if (evt && evt.status === "progress" && typeof evt.progress === "number") {
          progress.setModelProgress(evt.progress, evt.file || "");
        }
      });
      try {
        const semantic = await analyzeEmbeddings(text, obj.lang || "es");
        if (semantic && semantic.findings && semantic.findings.length) {
          obj.structural = (obj.structural || []).concat(
            semantic.findings.map((f) => ({
              line: 0,
              kind: f.kind,
              severity: f.severity,
              message: f.message,
              suggestion: f.suggestion,
            })),
          );
          // Bump score if a strong semantic signal lands.
          const strongSemantic = semantic.findings.some((f) => f.severity >= 3);
          if (strongSemantic && obj.score < 0.55) {
            obj.score = Math.max(obj.score, 0.55);
            if (obj.score >= 0.6) obj.label = obj.lang === "es" ? "alto" : "high";
            else if (obj.score >= 0.3) obj.label = obj.lang === "es" ? "moderado" : "moderate";
          }
        }
      } finally {
        offProgress();
      }
    } catch (err) {
      // Embedding layer is best-effort. Never block on it.
      console.warn("embedding analysis failed:", err);
    }

    // Live hit count once analysis is back
    const totalHits = (obj.hits ? obj.hits.length : 0) + (obj.structural ? obj.structural.length : 0);
    progress.setHits(totalHits);

    // Floor at minMs so the user can read the steps even on tiny text
    const elapsed = performance.now() - startedAt;
    if (elapsed < minMs) await new Promise((r) => setTimeout(r, minMs - elapsed));
    await progress.finish();

    render(obj);

    // Auto-run bibliography verification on every analysis (no opt-in needed).
    // verifyBibliography skips itself if no references are detected.
    if (extractRefsFn) {
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
  document.body.classList.remove("has-text");
});

// Toggle "has-text" class for mobile sticky button
els.input.addEventListener("input", () => {
  document.body.classList.toggle("has-text", els.input.value.trim().length > 0);
});

// Example chips — pools of variants. Each click cycles to the next one.
const EXAMPLES = {
  ai: [
    `El presente ensayo aborda la cuestión de la migración digital desde tres ejes principales. En primer lugar, examinaremos la transformación cultural que esta implica. En segundo lugar, analizaremos el impacto económico que ha tenido en las últimas décadas. En tercer lugar, exploraremos las consecuencias políticas que se derivan de este proceso.

Es importante destacar que la migración digital no es solo un fenómeno tecnológico, sino que constituye un cambio estructural profundo en la forma en que las sociedades contemporáneas se organizan, se comunican y se relacionan entre sí. Lo que enseña la historia es que estos procesos rara vez son neutros: se imponen, se resisten, se traducen, se renegocian.

En definitiva, comprender la migración digital requiere adoptar una mirada interdisciplinar que combine perspectivas de la sociología, la economía y la ciencia política. Solo así podremos abordar de manera integral los desafíos que este fenómeno plantea para el siglo XXI.`,

    `En el mundo actual, la inteligencia artificial se ha convertido en una herramienta fundamental para abordar los desafíos del siglo XXI. Desde la salud hasta la educación, sus aplicaciones son prácticamente ilimitadas y prometen transformar profundamente la forma en que vivimos y trabajamos.

Es fundamental comprender que la IA no es solo una tecnología, sino un cambio de paradigma que requiere una reflexión ética profunda. Diversos expertos coinciden en que su desarrollo debe guiarse por principios sólidos de transparencia, equidad y responsabilidad.

En conclusión, el futuro de la inteligencia artificial dependerá de nuestra capacidad colectiva para equilibrar innovación y regulación. Solo a través de un diálogo abierto y multidisciplinar podremos garantizar que esta tecnología beneficie a toda la humanidad.`,

    `La sostenibilidad ambiental constituye uno de los desafíos más apremiantes de nuestra era. Cabe destacar que las decisiones que tomemos hoy tendrán un impacto duradero en las generaciones futuras, lo cual exige un compromiso firme y articulado por parte de todos los actores sociales.

En primer lugar, resulta imperativo reconocer que el cambio climático no es solo un problema ambiental, sino que constituye un desafío multidimensional que afecta a la economía, la salud pública y la estabilidad social. En segundo lugar, debemos considerar que las soluciones requieren un enfoque integral. En tercer lugar, la cooperación internacional resulta esencial.

En síntesis, abordar la crisis climática requiere voluntad política, innovación tecnológica y cambios profundos en nuestros patrones de consumo. Estamos ante una oportunidad histórica para construir un mundo más justo y sostenible para todos.`,

    `La educación en el siglo XXI atraviesa una transformación sin precedentes. Las metodologías tradicionales, basadas en la transmisión unidireccional del conocimiento, están dando paso a modelos más dinámicos, colaborativos y centrados en el estudiante.

Es importante señalar que esta transformación no se limita a la incorporación de tecnología en el aula. Más bien, supone repensar profundamente los objetivos educativos, los roles de docentes y estudiantes, así como los criterios de evaluación. En este contexto, conceptos como el aprendizaje significativo, las competencias del siglo XXI y la educación inclusiva adquieren una relevancia fundamental.

Para concluir, el futuro de la educación dependerá de nuestra capacidad para integrar lo mejor de la tradición pedagógica con las posibilidades que ofrecen las nuevas tecnologías. Sin duda, estamos ante un momento apasionante.`,

    `El liderazgo efectivo en las organizaciones modernas requiere una combinación única de habilidades técnicas, emocionales y estratégicas. Los líderes contemporáneos deben navegar entornos cada vez más complejos, volátiles e inciertos, lo que demanda capacidades adaptativas excepcionales.

En primer lugar, la inteligencia emocional emerge como un factor crítico de éxito. En segundo lugar, la visión estratégica permite anticipar tendencias y oportunidades. En tercer lugar, la capacidad de comunicación inspira y moviliza a los equipos. Estos tres pilares constituyen la base del liderazgo transformacional.

Cabe mencionar que el liderazgo no es solo una posición jerárquica, sino una influencia que se ejerce a través del ejemplo, la coherencia y el compromiso genuino con el desarrollo de las personas. En última instancia, los grandes líderes son aquellos que dejan un legado de transformación positiva.`,
  ],

  human: [
    `Mi abuela tenía una caja de costura de hojalata con un dibujo descolorido de Cibeles. Adentro había botones de nácar de tres tamaños, un dedal con un golpe en el borde, agujas clavadas en un trozo de fieltro rojo. Cuando murió en 1997 nadie quiso la caja y terminó en mi pieza, encima del armario, juntando polvo unos quince años.

La abrí el otro día buscando un botón para una camisa. El dedal tenía las iniciales MR grabadas con una aguja: María Reyes, mi bisabuela, que la abuela apenas conoció porque murió de tifus cuando ella tenía cuatro. Eso me lo había contado mi mamá hace mucho, en una sobremesa, sin darle importancia, mientras pelaba una manzana.

Las cosas que heredamos no son las cosas. Son una conversación interrumpida que uno trata de seguir leyendo años después, sin todos los personajes, con la mitad de las páginas perdidas. El dedal funciona perfecto. Lo usé para coser el botón. Pesaba tres gramos. La caja sigue arriba del armario.`,

    `Compré la bici en marzo del 2018, una Trek de segunda con la pintura amarilla rayada en el cuadro y un timbre que sonaba a juguete. El tipo que me la vendió me dijo que la había usado tres veranos para ir al trabajo, dejó de andar en bici cuando se compró auto. Le faltaba una pastilla de freno.

La armé en el patio con mi vieja mirando desde la cocina, tomando té. Me prestó un destornillador philips que tenía guardado de cuando mi papá vivía. Yo no sabía nada de bicis. Aprendí mirando videos en YouTube, con la pantalla del teléfono apoyada en una maceta porque no tenía donde dejarla. Tardé cuatro horas en algo que un mecánico hace en quince minutos.

Esa bici me llevó al trabajo dos años. Se la regalé a un primo cuando me mudé. Capaz un día le pregunto si todavía la usa. Capaz no.`,

    `Mi mamá cocina pollo al horno los domingos. Siempre demás, porque calcula para diez aunque seamos cuatro. Después la mitad va al freezer en tuppers que ella reutiliza desde antes que yo naciera, con el plástico amarillento por dentro y la fecha escrita en la tapa con marcador.

El olor de su cocina es lo que más extraño cuando estoy fuera. No el pollo en sí, que tampoco está tan rico. Es la mezcla. Cebolla, ajo, orégano, una vela de citronella que tiene en la ventana desde hace años para los mosquitos, el detergente de loza marca Ariel que compra en el almacén de la esquina porque dice que el del super no espuma igual.

La última vez que fui me dio un tupper para llevar. Lo dejé en la heladera de mi pieza dos semanas hasta que se echó a perder. No lo quise tirar al tacho del depto. Lo llevé al tacho de la calle, una cuadra abajo. No sé bien por qué.`,

    `Mi vecino del 4B muere los lunes a las 6 de la mañana cuando le suena el despertador y no lo apaga. Vive solo desde que su mujer se fue a vivir con la hija a Mendoza, hace como cinco años. Nos saludamos en el ascensor. Nunca hablamos.

Una vez le golpeé la puerta a las 6:30 porque el despertador llevaba media hora sonando y yo trabajo en casa y no podía pensar. Tardó en abrir. Estaba en pijama, con cara de no haber dormido. Me pidió disculpas tres veces. Le dije que no pasaba nada, que solo quería avisarle. Volví a mi depto y me sentí pésimo el resto del día.

Después pasaron meses sin que sonara el despertador. Pensé que se había mudado. La semana pasada lo vi en el ascensor. Me dijo "buen día" antes que yo. Me pareció que estaba más flaco.`,

    `El gato de la casa es viejo. Se llama Mateo, tiene catorce años, y duerme arriba de mi notebook cuando trabajo. Cuando lo saco se enoja, se va a la otra punta del living, me mira con cara de odio, y vuelve diez minutos después como si no hubiera pasado nada.

La veterinaria dice que está bien para su edad, pero le falta un diente y le bajó la función renal. Tomamos la decisión de no operarlo. Le damos pastillas dos veces al día, escondidas en paté. Él las pesca igual: come el paté, escupe la pastilla, y nos mira como diciendo "soy más vivo que ustedes". Eventualmente se la da. Eventualmente.

Pienso a veces en el día que se muera. No quiero pensarlo, pero pienso. Cuando vuelva a casa y no esté arriba del notebook va a ser raro. La casa va a quedar más vacía. Y todavía nos van a quedar las pastillas en el cajón, sin gato a quien dárselas.`,
  ],

  fakebib: [
    `La transformación digital de las prácticas pedagógicas constituye uno de los desafíos centrales del siglo XXI. Diversos estudios han mostrado el impacto sustancial de las tecnologías inmersivas en el aprendizaje significativo (Mendoza & Ruiz, 2021).

Referencias

Mendoza, P., & Ruiz, A. (2021). Pedagogías inmersivas y aprendizaje situado. Revista Iberoamericana de Educación, 87(2), 145-168. https://doi.org/10.35362/rie8723421

Halberstam, J. K. (2019). Embodied cognition in virtual learning environments. Journal of Educational Technology Research, 67(4), 891-915.

Calderón-Vivas, M. (2020). Digital natives reconsidered: a Latin American perspective. Educación y Sociedad, 41(3), 412-438. https://doi.org/10.1590/s1517-9702202044123456

Pinker, S. (2014). The language instinct: How the mind creates language. Harper Perennial.

García Canclini, N. (2018). Culturas híbridas: estrategias para entrar y salir de la modernidad. Grijalbo.`,

    `La economía conductual ha transformado nuestra comprensión de la toma de decisiones financieras. Como sostiene Kahneman (2011), los seres humanos no operan como agentes perfectamente racionales, sino que están sujetos a sesgos sistemáticos que afectan sus elecciones cotidianas.

Bibliografía

Kahneman, D. (2011). Thinking, fast and slow. Farrar, Straus and Giroux.

Velasco-Ramírez, J. (2020). Sesgos cognitivos en mercados emergentes: una perspectiva latinoamericana. Revista de Economía Conductual, 14(3), 287-312. https://doi.org/10.1108/recb.2020.0331

Thaler, R. H., & Sunstein, C. R. (2008). Nudge: Improving decisions about health, wealth, and happiness. Yale University Press.

Achterhof, M. (2019). Decision-making under uncertainty in post-pandemic economies. Journal of Behavioral Finance, 20(4), 521-549.

Castiglione-Pérez, A., & Wong, T. (2022). Heurísticas de inversión en milenials: estudio comparado Chile-Singapur. Estudios Económicos del Cono Sur, 56(2), 89-117. https://doi.org/10.4067/eecs.2022.5621`,

    `La filosofía contemporánea de la mente se ha visto profundamente influenciada por los avances en neurociencia cognitiva. La cuestión de la conciencia, el problema duro al que alude Chalmers (1995), sigue siendo objeto de intenso debate.

Referencias

Chalmers, D. J. (1995). Facing up to the problem of consciousness. Journal of Consciousness Studies, 2(3), 200-219.

Dennett, D. C. (1991). Consciousness explained. Little, Brown and Company.

Vargas-Llosa, F. (2018). Mente extendida y cognición situada: una crítica fenomenológica. Análisis Filosófico, 38(1), 67-94. https://doi.org/10.36446/af.2018.3814

Tononi, G., & Koch, C. (2015). Consciousness: here, there and everywhere? Philosophical Transactions of the Royal Society B, 370(1668), 20140167.

Bressan-Quintana, P. (2021). Qualia y representacionalismo: una propuesta integradora. Cuadernos de Filosofía de la Mente, 9(2), 145-178. https://doi.org/10.5377/cfm.v9i2.11824`,

    `Los estudios de género han redefinido las categorías analíticas con que abordamos las relaciones sociales. La obra fundacional de Butler (1990) abrió un campo de investigación que sigue produciendo debate y desarrollo teórico.

Bibliografía

Butler, J. (1990). Gender trouble: Feminism and the subversion of identity. Routledge.

Lugones, M. (2008). Colonialidad y género. Tabula Rasa, 9, 73-101.

Sandoval-Hernández, K. (2019). Performatividad y resistencia en cuerpos disidentes del sur global. Revista Latinoamericana de Estudios de Género, 12(1), 33-58. https://doi.org/10.32870/rleg.v12i1.7842

hooks, b. (2000). Feminism is for everybody: Passionate politics. South End Press.

Echeverría-Quispe, R. (2022). Decolonialidad y feminismos comunitarios andinos: tensiones y diálogos. Andina: Revista de Estudios Decoloniales, 7(3), 211-244. https://doi.org/10.18800/are.20223.7301`,

    `La crisis climática plantea desafíos urgentes a la gobernanza global. El Acuerdo de París marcó un hito, pero las trayectorias actuales de emisiones siguen siendo incompatibles con sus metas (IPCC, 2021).

Referencias

IPCC. (2021). Climate change 2021: The physical science basis. Working Group I contribution to the Sixth Assessment Report.

Naomi Klein. (2014). This changes everything: Capitalism vs. the climate. Simon & Schuster.

Mansilla-Aravena, D. (2020). Justicia climática y deuda ecológica en América Latina: un análisis crítico. Ecología Política Latinoamericana, 18(2), 99-128. https://doi.org/10.4324/eplat.2020.1822

Steffen, W., et al. (2018). Trajectories of the Earth System in the Anthropocene. Proceedings of the National Academy of Sciences, 115(33), 8252-8259.

Quispe-Achacollo, M. (2021). Saberes ancestrales andinos frente al cambio climático: el caso del altiplano boliviano. Pacha: Revista de Estudios Contemporáneos del Sur, 4(11), 178-205. https://doi.org/10.46652/pacha.v4i11.222`,
  ],
};

// Round-robin counter per chip so each click rotates to the next variant.
const _exampleCursor = { ai: 0, human: 0, fakebib: 0 };

document.querySelectorAll(".ex-chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    const key = chip.dataset.example;
    const pool = EXAMPLES[key];
    if (!pool || !pool.length) return;
    const idx = _exampleCursor[key] % pool.length;
    _exampleCursor[key] = idx + 1;
    els.input.value = pool[idx];
    document.body.classList.add("has-text");
    els.input.focus();
    els.input.scrollTop = 0;
    // Tiny visual hint: flash the chip so user sees it changed
    chip.classList.add("ex-chip-flash");
    setTimeout(() => chip.classList.remove("ex-chip-flash"), 250);
  });
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

function buildSearchUrl(title, author, kind) {
  // Builds a search URL for manual lookup.
  const q = [title, author].filter(Boolean).join(" ");
  const enc = encodeURIComponent(q);
  if (kind === "scholar") return `https://scholar.google.com/scholar?q=${enc}`;
  if (kind === "crossref") return `https://api.crossref.org/works?rows=5&query.bibliographic=${enc}`;
  if (kind === "openalex") return `https://api.openalex.org/works?search=${enc}`;
  // generic web search
  return `https://www.google.com/search?q=${enc}`;
}

function renderBiblioRow(ref, res) {
  const t = I18N[UILANG];
  const icon = { exists: "✓", not_found: "✗", error: "?", unverifiable: "·" }[res.status] || "·";
  const cls = `biblio-${res.status}`;
  const ident = ref.identifier || (ref.title ? ref.title.slice(0, 80) : ref.raw.slice(0, 80));
  const identSafe = escapeHtml(ident);
  // If verified and has URL, make the title clickable.
  const identHtml = (res.status === "exists" && res.url)
    ? `<a href="${escapeHtml(res.url)}" target="_blank" rel="noopener" class="biblio-link">${identSafe} ↗</a>`
    : identSafe;
  const detail = res.detail ? `<div class="biblio-detail">${escapeHtml(res.detail)}</div>` : "";

  const title = ref.title || "";
  const author = ref.author || "";

  // Action buttons + advice per status
  let actions = "";
  if (res.status === "not_found") {
    const advice = (UILANG === "es")
      ? "No se encontró en ninguna fuente. Puede ser una cita inventada por IA, o una fuente legítima no indexada (tesis, capítulo, edición regional)."
      : "Not found in any source. Could be AI-invented, or a legitimate non-indexed source (thesis, chapter, regional edition).";
    actions = `
      <div class="biblio-advice">${advice}</div>
      <div class="biblio-actions">
        <a class="biblio-action" href="${buildSearchUrl(title, author, "scholar")}" target="_blank" rel="noopener">🔍 Google Scholar</a>
        <a class="biblio-action" href="${buildSearchUrl(title, author, "crossref")}" target="_blank" rel="noopener">📖 CrossRef</a>
        <a class="biblio-action" href="${buildSearchUrl(title, author, "openalex")}" target="_blank" rel="noopener">📚 OpenAlex</a>
        <a class="biblio-action" href="${buildSearchUrl(title, author, "web")}" target="_blank" rel="noopener">🌐 web</a>
      </div>`;
  } else if (res.status === "unverifiable") {
    const advice = (UILANG === "es")
      ? "Sin DOI ni identificador parseable. Muchas citas válidas (libros, tesis, informes) no tienen DOI. No es señal de falsedad."
      : "No DOI or parseable ID. Many valid citations (books, theses, reports) don't have DOIs. Not a sign of fakery.";
    const searchQ = title || ident;
    const encoded = encodeURIComponent(searchQ);
    actions = `
      <div class="biblio-advice">${advice}</div>
      <div class="biblio-actions">
        <a class="biblio-action" href="https://scholar.google.com/scholar?q=${encoded}" target="_blank" rel="noopener">🔍 Google Scholar</a>
        <a class="biblio-action" href="https://www.google.com/search?q=${encoded}" target="_blank" rel="noopener">🌐 web</a>
      </div>`;
  } else if (res.status === "error") {
    const advice = (UILANG === "es")
      ? "Error de red al consultar las fuentes. No significa que la cita sea falsa — solo que las APIs no respondieron a tiempo. Reintenta o busca manualmente."
      : "Network error while checking sources. Doesn't mean the citation is fake — just that the APIs didn't respond in time. Retry or search manually.";
    const searchQ = title || ident;
    const encoded = encodeURIComponent(searchQ);
    actions = `
      <div class="biblio-advice">${advice}</div>
      <div class="biblio-actions">
        <button class="biblio-action biblio-retry" data-ref-index="${ref.line}" data-ref-kind="${ref.kind}" data-ref-id="${escapeHtml(ref.identifier || "")}" data-ref-title="${escapeHtml(title)}" data-ref-author="${escapeHtml(author)}" data-ref-year="${escapeHtml(ref.year || "")}">🔄 reintentar</button>
        <a class="biblio-action" href="https://scholar.google.com/scholar?q=${encoded}" target="_blank" rel="noopener">🔍 Google Scholar</a>
        <a class="biblio-action" href="https://www.google.com/search?q=${encoded}" target="_blank" rel="noopener">🌐 web</a>
      </div>`;
  }

  return `
    <div class="biblio-row ${cls}" data-sort-id="${identSafe.toLowerCase()}" data-sort-status="${res.status}">
      <div class="biblio-icon">${icon}</div>
      <div class="biblio-body">
        <div class="biblio-ident">[${ref.kind}] ${identHtml}</div>
        ${detail}
        ${actions}
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
    // No references in the text — silently skip. No need to show "biblio: none".
    return;
  }

  // Header + privacy note (always shown when refs are detected)
  appendBiblio(`<div class="biblio-header"><span class="biblio-emoji">📚</span> ${t.biblio_summary_label} — ${t.biblio_sum_total.replace("{n}", refs.length)}</div>`);
  appendBiblio(`<div class="biblio-note">${t.biblio_check_running}</div>`);

  // Animated progress strip with per-source dots
  const progressId = "biblio-progress-" + Math.random().toString(36).slice(2, 8);
  appendBiblio(`
    <div id="${progressId}" class="biblio-progress-box">
      <div class="biblio-progress-bar"><div class="biblio-progress-fill" style="width:0%"></div></div>
      <div class="biblio-progress-meta">
        <span class="biblio-progress-count">0 / ${refs.length}</span>
        <span class="biblio-progress-current">${t.biblio_progress_starting}</span>
      </div>
    </div>`);
  const box = document.getElementById(progressId);
  const fill = box && box.querySelector(".biblio-progress-fill");
  const countEl = box && box.querySelector(".biblio-progress-count");
  const currentEl = box && box.querySelector(".biblio-progress-current");

  const updateProgress = (done, label) => {
    if (!box) return;
    const pct = Math.round((done / refs.length) * 100);
    if (fill) fill.style.width = pct + "%";
    if (countEl) countEl.textContent = `${done} / ${refs.length}`;
    if (currentEl && label) currentEl.textContent = label;
  };

  const results = [];
  const verifyOne = async (r) => {
    try {
      if (r.kind === "doi")        return { ref: r, res: await verifyDoiJs(r.identifier) };
      if (r.kind === "arxiv")      return { ref: r, res: await verifyArxivJs(r.identifier) };
      if (r.kind === "isbn")       return { ref: r, res: await verifyIsbnJs(r.identifier) };
      if (r.kind === "citation")   return { ref: r, res: await verifyCitationJs(r) };
      return { ref: r, res: { status: "unverifiable", detail: "" } };
    } catch (e) {
      return { ref: r, res: { status: "error", detail: e.message } };
    }
  };
  const CONCURRENCY = 4;
  for (let i = 0; i < refs.length; i += CONCURRENCY) {
    const batch = refs.slice(i, i + CONCURRENCY);
    // Show the title of the first ref of the current batch as preview
    const preview = (batch[0].title || batch[0].identifier || batch[0].raw || "").slice(0, 60);
    updateProgress(i, t.biblio_progress_checking.replace("{title}", preview || "…"));
    const done = await Promise.all(batch.map(verifyOne));
    results.push(...done);
    updateProgress(Math.min(i + batch.length, refs.length), preview ? t.biblio_progress_checking.replace("{title}", preview) : "");
    await sleep(60);
  }
  updateProgress(refs.length, t.biblio_progress_done);
  // Brief pause so the user sees the bar fill, then collapse
  await sleep(400);
  if (box) box.remove();

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

  // Detail (collapsed) with sort controls
  let detailHtml = "";
  for (const { ref, res } of results) detailHtml += renderBiblioRow(ref, res);

  const sortLabels = {
    az: UILANG === "es" ? "A–Z" : "A–Z",
    verified: UILANG === "es" ? "✓ verificadas" : "✓ verified",
    notfound: UILANG === "es" ? "✗ sin match" : "✗ no match",
    unverifiable: UILANG === "es" ? "· sin ID" : "· no ID",
    error: UILANG === "es" ? "? error red" : "? net err",
  };

  appendBiblio(`
    <details class="biblio-detail-box" id="biblio-detail-box">
      <summary>
        <span class="more-show">${t.biblio_show_detail}</span>
        <span class="more-hide">${t.biblio_hide_detail}</span>
      </summary>
      <div class="biblio-sortbar">
        <span class="biblio-sortbar-label">${UILANG === "es" ? "ordenar:" : "sort:"}</span>
        <button class="biblio-sortbtn active" data-sort="az">${sortLabels.az}</button>
        <button class="biblio-sortbtn" data-sort="exists">${sortLabels.verified}</button>
        <button class="biblio-sortbtn" data-sort="not_found">${sortLabels.notfound}</button>
        ${counts.unverifiable ? `<button class="biblio-sortbtn" data-sort="unverifiable">${sortLabels.unverifiable}</button>` : ""}
        ${counts.error ? `<button class="biblio-sortbtn" data-sort="error">${sortLabels.error}</button>` : ""}
      </div>
      <div class="biblio-detail-rows">${detailHtml}</div>
    </details>`);

  // Sort controls — live sorting
  const sortBar = document.querySelector("#biblio-detail-box .biblio-sortbar");
  if (sortBar) {
    sortBar.addEventListener("click", (e) => {
      const btn = e.target.closest(".biblio-sortbtn");
      if (!btn) return;
      // Mark active
      sortBar.querySelectorAll(".biblio-sortbtn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      const mode = btn.dataset.sort;
      const rowsEl = document.querySelector("#biblio-detail-box .biblio-detail-rows");
      if (!rowsEl) return;
      const rows = [...rowsEl.children];
      rows.sort((a, b) => {
        if (mode === "az") {
          return (a.dataset.sortId || "").localeCompare(b.dataset.sortId || "");
        }
        // Status-based: requested status first, then by A-Z
        const aMatch = a.dataset.sortStatus === mode ? 0 : 1;
        const bMatch = b.dataset.sortStatus === mode ? 0 : 1;
        if (aMatch !== bMatch) return aMatch - bMatch;
        return (a.dataset.sortId || "").localeCompare(b.dataset.sortId || "");
      });
      rowsEl.innerHTML = "";
      for (const r of rows) rowsEl.appendChild(r);
    });
  }

  // Retry buttons for errored entries
  document.querySelectorAll("#biblio-detail-box .biblio-retry").forEach(btn => {
    btn.addEventListener("click", async function() {
      const origText = this.textContent;
      this.textContent = "...";
      this.disabled = true;
      const ref = {
        kind: this.dataset.refKind,
        identifier: this.dataset.refId,
        title: this.dataset.refTitle,
        author: this.dataset.refAuthor,
        year: this.dataset.refYear,
        line: this.dataset.refIndex,
        raw: this.dataset.refTitle || this.dataset.refId || "",
      };
      let newRes;
      try {
        if (ref.kind === "doi")          newRes = await verifyDoiJs(ref.identifier);
        else if (ref.kind === "arxiv")    newRes = await verifyArxivJs(ref.identifier);
        else if (ref.kind === "isbn")     newRes = await verifyIsbnJs(ref.identifier);
        else if (ref.kind === "citation") newRes = await verifyCitationJs(ref);
        else newRes = { status: "unverifiable", detail: "" };
      } catch (e) {
        newRes = { status: "error", detail: e.message };
      }
      // Replace this row in-place
      const row = this.closest(".biblio-row");
      if (row && ref.kind) {
        const newRowHtml = renderBiblioRow(ref, newRes);
        const temp = document.createElement("div");
        temp.innerHTML = newRowHtml;
        const newRow = temp.firstElementChild;
        row.replaceWith(newRow);
      } else {
        this.textContent = origText;
        this.disabled = false;
      }
    });
  });

  // Download report...
  const reportHtml = buildBiblioReportHtml(results, t);
  const reportBlob = new Blob([reportHtml], { type: "text/html;charset=utf-8" });
  const reportUrl = URL.createObjectURL(reportBlob);
  appendBiblio(`
    <div class="biblio-download">
      <a class="btn ghost" href="${reportUrl}" target="_blank" rel="noopener">📄 ${t.biblio_view_btn}</a>
      <a class="btn ghost" href="${reportUrl}" download="aismell-bibliografia.html">⬇ ${t.biblio_download_btn}</a>
    </div>`);

  // Only nudge Intelecta when there's enough signal: 2+ "no match" AND ratio > 25%
  const ratio = counts.not_found / refs.length;
  if (counts.not_found >= 2 && ratio >= 0.25) {
    appendBiblio(renderIntelectaNudge("biblio"));
  }
}

function buildBiblioReportHtml(results, t) {
  const stats = { exists: 0, not_found: 0, unverifiable: 0, error: 0 };
  for (const { res } of results) stats[res.status] = (stats[res.status] || 0) + 1;
  const total = results.length;
  const ratioFake = total ? (stats.not_found / total) : 0;
  let verdictLabel, verdictClass, verdictReason;
  if (ratioFake >= 0.25 && stats.not_found >= 2) {
    verdictLabel = t.biblio_rep_verdict_high;
    verdictClass = "v-high";
    verdictReason = t.biblio_rep_reason_high.replace("{n}", stats.not_found).replace("{total}", total);
  } else if (stats.not_found > 0) {
    verdictLabel = t.biblio_rep_verdict_mid;
    verdictClass = "v-mid";
    verdictReason = t.biblio_rep_reason_mid.replace("{n}", stats.not_found).replace("{total}", total);
  } else {
    verdictLabel = t.biblio_rep_verdict_clean;
    verdictClass = "v-clean";
    verdictReason = t.biblio_rep_reason_clean;
  }

  const escape = (s) => String(s == null ? "" : s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;").replace(/'/g, "&#39;");

  const statusLabels = {
    exists: { label: t.biblio_sum_verified, glyph: "✓", cls: "ok" },
    not_found: { label: t.biblio_sum_not_found, glyph: "✗", cls: "err" },
    unverifiable: { label: t.biblio_sum_unverifiable, glyph: "?", cls: "warn" },
    error: { label: t.biblio_sum_error, glyph: "·", cls: "warn" },
  };

  const rows = results.map(({ ref, res }) => {
    const sl = statusLabels[res.status] || statusLabels.error;
    const idLabel = ref.identifier || ref.title || ref.raw || "";
    const detail = res.detail || "";
    return `
      <li class="ref ref-${sl.cls}">
        <div class="ref-line">
          <span class="ref-glyph">${sl.glyph}</span>
          <span class="ref-loc">L${escape(ref.line)}</span>
          <span class="ref-kind">[${escape(ref.kind || "citation")}]</span>
          <span class="ref-status ${sl.cls}">${escape(sl.label)}</span>
        </div>
        <div class="ref-id">${escape(idLabel)}</div>
        ${detail ? `<div class="ref-detail">${escape(detail)}</div>` : ""}
      </li>`;
  }).join("");

  const date = new Date().toISOString().slice(0, 10);
  const title = t.biblio_rep_title;

  return `<!DOCTYPE html>
<html lang="${t === I18N.es ? "es" : "en"}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${escape(title)} · aismell</title>
<style>
  :root {
    --bg: #0d0d0e; --bg2: #161618; --fg: #e8e6e0; --dim: #6b6864;
    --line: #2a2826; --hl: #e8c547; --red: #d65a4a; --grn: #6fb86a;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  html, body { background: var(--bg); color: var(--fg); }
  body {
    font-family: "JetBrains Mono", "Fira Code", "SF Mono", "Menlo", ui-monospace, monospace;
    font-size: 14px; line-height: 1.55;
    padding: 28px 24px 60px;
    max-width: 920px; margin: 0 auto;
  }
  header {
    border-bottom: 1px dashed var(--line);
    padding-bottom: 18px; margin-bottom: 24px;
    display: flex; align-items: baseline; gap: 14px; flex-wrap: wrap;
  }
  header h1 { font-size: 22px; font-weight: 700; letter-spacing: -0.3px; }
  header h1 .nose { margin-right: 4px; }
  header .meta { color: var(--dim); font-size: 12px; margin-left: auto; }

  .toolbar {
    display: flex; gap: 10px; flex-wrap: wrap;
    margin-bottom: 22px;
  }
  .btn {
    background: var(--hl); color: #1a1a1a; border: none;
    padding: 8px 16px; font: inherit; font-weight: 700; font-size: 13px;
    cursor: pointer; text-transform: lowercase; text-decoration: none;
    display: inline-block;
  }
  .btn:hover { background: #f0d160; }
  .btn.ghost {
    background: transparent; color: var(--dim); border: 1px solid var(--line);
    font-weight: 400;
  }
  .btn.ghost:hover { color: var(--fg); border-color: var(--fg); }

  .verdict {
    padding: 22px 24px;
    border: 1px solid var(--line); background: var(--bg2);
    margin-bottom: 22px;
  }
  .verdict-label {
    font-size: 11px; text-transform: uppercase; letter-spacing: 1.4px;
    color: var(--dim); margin-bottom: 10px;
  }
  .verdict-value { font-size: 26px; font-weight: 600; letter-spacing: -0.3px; }
  .verdict.v-high .verdict-value { color: var(--red); }
  .verdict.v-mid .verdict-value  { color: var(--hl); }
  .verdict.v-clean .verdict-value { color: var(--grn); }
  .verdict-reason { color: var(--fg); font-size: 13.5px; margin-top: 10px; }

  .stats {
    display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px;
    margin-bottom: 24px;
  }
  .stat {
    border-left: 3px solid var(--line);
    padding: 6px 0 6px 12px;
  }
  .stat.ok   { border-color: var(--grn); }
  .stat.err  { border-color: var(--red); }
  .stat.warn { border-color: var(--hl); }
  .stat.zero { opacity: 0.55; }
  .stat .num {
    font-size: 24px; font-weight: 700; color: var(--fg); line-height: 1;
    font-variant-numeric: tabular-nums;
  }
  .stat .lbl {
    font-size: 11px; text-transform: uppercase; letter-spacing: 1px;
    color: var(--dim); margin-top: 6px;
  }

  .disclaimer {
    padding: 12px 16px; border: 1px dashed var(--line);
    color: var(--dim); font-size: 12px; line-height: 1.6;
    font-style: italic; margin-bottom: 22px;
  }

  h2 {
    font-size: 11px; text-transform: uppercase; letter-spacing: 1.4px;
    color: var(--dim); margin-bottom: 12px; font-weight: 600;
  }

  ul.refs { list-style: none; }
  .ref {
    border-bottom: 1px solid var(--line);
    padding: 14px 0;
  }
  .ref:last-child { border-bottom: none; }
  .ref-line {
    display: flex; gap: 10px; align-items: baseline;
    font-size: 12px; color: var(--dim); margin-bottom: 6px;
  }
  .ref-glyph { font-size: 16px; line-height: 1; }
  .ref-ok   .ref-glyph { color: var(--grn); }
  .ref-err  .ref-glyph { color: var(--red); }
  .ref-warn .ref-glyph { color: var(--hl); }
  .ref-loc { color: var(--dim); font-size: 11px; }
  .ref-kind { color: var(--dim); font-size: 11px; }
  .ref-status {
    margin-left: auto; text-transform: uppercase; letter-spacing: 0.6px;
    font-size: 10.5px;
  }
  .ref-status.ok   { color: var(--grn); }
  .ref-status.err  { color: var(--red); }
  .ref-status.warn { color: var(--hl); }
  .ref-id { color: var(--fg); font-size: 13px; line-height: 1.5; }
  .ref-detail { color: var(--dim); font-size: 12px; margin-top: 4px; line-height: 1.5; }

  footer {
    margin-top: 36px; padding-top: 16px;
    border-top: 1px dashed var(--line);
    color: var(--dim); font-size: 11px; text-align: center;
  }
  footer a { color: var(--dim); text-decoration: underline; text-underline-offset: 3px; }
  footer a:hover { color: var(--fg); }

  /* Print → PDF: forces white background, black text, sane page breaks */
  @media print {
    html, body {
      background: #fff; color: #111;
    }
    body { padding: 14mm 12mm; max-width: none; }
    .toolbar { display: none; }
    .verdict, .stat, .disclaimer, .ref {
      border-color: #ccc !important;
      background: transparent !important;
    }
    h1, h2, .ref-id { color: #111 !important; }
    .verdict-label, .verdict-reason, .stat .lbl, .ref-detail,
    .ref-line, .ref-loc, .ref-kind, .disclaimer, footer, header .meta {
      color: #555 !important;
    }
    .verdict.v-high .verdict-value, .ref-err .ref-glyph, .ref-status.err { color: #b03020 !important; }
    .verdict.v-mid .verdict-value,  .ref-warn .ref-glyph, .ref-status.warn { color: #a07820 !important; }
    .verdict.v-clean .verdict-value, .ref-ok .ref-glyph,  .ref-status.ok   { color: #2a7030 !important; }
    .ref { page-break-inside: avoid; }
  }
</style>
</head>
<body>
<header>
  <h1><span class="nose">👃</span> ${escape(title)}</h1>
  <div class="meta">${escape(date)}</div>
</header>

<div class="toolbar">
  <button class="btn" onclick="window.print()">🖨 ${escape(t.biblio_rep_print)}</button>
  <a class="btn ghost" href="https://brm-src.github.io/aismell/" target="_blank" rel="noopener">↗ aismell</a>
</div>

<div class="verdict ${verdictClass}">
  <div class="verdict-label">${escape(t.verdict_label)}</div>
  <div class="verdict-value">${escape(verdictLabel)}</div>
  <div class="verdict-reason">${escape(verdictReason)}</div>
</div>

<div class="stats">
  <div class="stat ok ${stats.exists === 0 ? "zero" : ""}"><div class="num">${stats.exists}</div><div class="lbl">${escape(t.biblio_sum_verified)}</div></div>
  <div class="stat err ${stats.not_found === 0 ? "zero" : ""}"><div class="num">${stats.not_found}</div><div class="lbl">${escape(t.biblio_sum_not_found)}</div></div>
  <div class="stat warn ${stats.unverifiable === 0 ? "zero" : ""}"><div class="num">${stats.unverifiable}</div><div class="lbl">${escape(t.biblio_sum_unverifiable)}</div></div>
  <div class="stat warn ${stats.error === 0 ? "zero" : ""}"><div class="num">${stats.error}</div><div class="lbl">${escape(t.biblio_sum_error)}</div></div>
</div>

<div class="disclaimer">${escape(t.biblio_disclaimer)}</div>

<h2>${escape(t.biblio_rep_detail_title)} — ${total}</h2>
<ul class="refs">${rows}</ul>

<footer>
  ${escape(t.biblio_rep_footer)} · <a href="https://brm-src.github.io/aismell/">aismell</a> · <a href="https://intelecta.cl">Intelecta</a>
</footer>
</body>
</html>`;
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
    const url = m.URL || `https://doi.org/${doi}`;
    return { status: "exists", detail, url };
  } catch (e) {
    return { status: "error", detail: e.message };
  }
}

async function verifyArxivJs(id) {
  const url = `https://export.arxiv.org/api/query?id_list=${encodeURIComponent(id)}`;
  const publicUrl = `https://arxiv.org/abs/${encodeURIComponent(id)}`;
  try {
    const r = await fetch(url);
    if (!r.ok) return { status: "error", detail: `HTTP ${r.status}` };
    const text = await r.text();
    if (!text.includes("<entry>")) return { status: "not_found", detail: "arXiv: not found" };
    const m = text.match(/<entry>[\s\S]*?<title>([\s\S]*?)<\/title>/);
    const title = m ? m[1].replace(/\s+/g, " ").trim() : "";
    return { status: "exists", detail: title, url: publicUrl };
  } catch (e) {
    return { status: "error", detail: e.message };
  }
}

// Bulletproof citation verification: try every source, classify by best signal.
// - 8s timeout per source (AbortController) → no hangs
// - parallel-ish fallback chain, returns first "exists"
// - if no source confirms but ≥1 errored, mark as "error" (not "not_found")
async function fetchWithTimeout(url, opts = {}, ms = 8000) {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), ms);
  try {
    return await fetch(url, { ...opts, signal: ctrl.signal });
  } finally {
    clearTimeout(t);
  }
}

async function verifyCrossrefJs(ref) {
  const q = ref.author ? `${ref.title} ${ref.author}` : ref.title;
  const url = `https://api.crossref.org/works?rows=3&query.bibliographic=${encodeURIComponent(q)}`;
  try {
    const r = await fetchWithTimeout(url, { headers: { Accept: "application/json" } });
    if (!r.ok) return { status: "error", detail: `CrossRef HTTP ${r.status}` };
    const d = await r.json();
    const items = (d.message && d.message.items) || [];
    for (const item of items) {
      const found = (item.title && item.title[0]) || "";
      const score = item.score || 0;
      if (score >= 45 && titleSimilar(ref.title, found)) {
        const url = item.DOI ? `https://doi.org/${item.DOI}` : (item.URL || null);
        return { status: "exists", detail: `CrossRef: ${found}`, url };
      }
    }
    return { status: "not_found", detail: "sin match en CrossRef" };
  } catch (e) {
    return { status: "error", detail: `CrossRef: ${e.name === "AbortError" ? "timeout" : e.message}` };
  }
}

async function verifyOpenLibrarySearchJs(ref) {
  const params = new URLSearchParams({ q: ref.title, limit: "3" });
  if (ref.author) params.set("author", ref.author);
  const url = `https://openlibrary.org/search.json?${params.toString()}`;
  try {
    const r = await fetchWithTimeout(url, { headers: { Accept: "application/json" } });
    if (!r.ok) return { status: "error", detail: `OpenLibrary HTTP ${r.status}` };
    const d = await r.json();
    for (const item of (d.docs || []).slice(0, 5)) {
      const found = item.title || "";
      const year = item.first_publish_year ? String(item.first_publish_year) : "";
      if (titleSimilar(ref.title, found) && (!ref.year || !year || Math.abs(parseInt(year) - parseInt(ref.year)) <= 1)) {
        const authors = (item.author_name || []).slice(0, 2).join(", ");
        const olKey = item.key || (item.cover_edition_key ? `/books/${item.cover_edition_key}` : null);
        const url = olKey ? `https://openlibrary.org${olKey}` : null;
        return { status: "exists", detail: `OpenLibrary${year ? ` (${year})` : ""}: ${authors ? authors + " — " : ""}${found}`, url };
      }
    }
    return { status: "not_found", detail: "sin match en OpenLibrary" };
  } catch (e) {
    return { status: "error", detail: `OpenLibrary: ${e.name === "AbortError" ? "timeout" : e.message}` };
  }
}

async function verifyArxivSearchJs(ref) {
  // arXiv has a query API, returns Atom XML. We only need a yes/no.
  const q = `ti:"${(ref.title || "").replace(/"/g, "")}"`;
  const url = `https://export.arxiv.org/api/query?search_query=${encodeURIComponent(q)}&max_results=3`;
  try {
    const r = await fetchWithTimeout(url);
    if (!r.ok) return { status: "error", detail: `arXiv HTTP ${r.status}` };
    const xml = await r.text();
    // Parse <entry><title>...</title>...</entry> blocks
    const entries = xml.match(/<entry>[\s\S]*?<\/entry>/g) || [];
    for (const entry of entries) {
      const m = entry.match(/<title>([\s\S]*?)<\/title>/);
      const found = m ? m[1].replace(/\s+/g, " ").trim() : "";
      if (titleSimilar(ref.title, found)) {
        const idMatch = entry.match(/<id>([\s\S]*?)<\/id>/);
        const url = idMatch ? idMatch[1].trim() : null;
        return { status: "exists", detail: `arXiv: ${found}`, url };
      }
    }
    return { status: "not_found", detail: "sin match en arXiv" };
  } catch (e) {
    return { status: "error", detail: `arXiv: ${e.name === "AbortError" ? "timeout" : e.message}` };
  }
}

async function verifyCitationJs(ref) {
  if (!ref.title) return { status: "unverifiable", detail: "" };

  // Run all 6 sources sequentially. Stop at first "exists".
  // Track errors separately so we can distinguish "all sources errored" (network down)
  // from "every source said no match" (probably fake).
  const sources = [
    verifyCrossrefJs,
    verifyOpenAlexJs,
    verifySemanticScholarJs,
    verifyGoogleBooksJs,
    verifyOpenLibrarySearchJs,
    verifyArxivSearchJs,
  ];

  let errors = 0;
  let notFound = 0;
  const errorDetails = [];

  for (const src of sources) {
    let res;
    try {
      res = await src(ref);
    } catch (e) {
      // Defensive — every src already has try/catch, but belt + suspenders
      res = { status: "error", detail: `unexpected: ${e.message}` };
    }
    if (res.status === "exists") return res;
    if (res.status === "error") { errors++; if (res.detail) errorDetails.push(res.detail); }
    else if (res.status === "not_found") notFound++;
  }

  const apa = ref.apa_status === "suspicious" && ref.apa_issues && ref.apa_issues.length
    ? ` · APA débil: ${ref.apa_issues.slice(0, 2).join(", ")}` : "";

  // If every source errored, this isn't "no match" — it's a network problem.
  if (errors === sources.length) {
    return { status: "error", detail: `red caída o APIs no disponibles: ${errorDetails.slice(0, 2).join("; ")}` };
  }
  // If most errored and only 1-2 actually checked → still flag as error to be honest.
  if (errors >= sources.length - 1 && notFound <= 1) {
    return { status: "error", detail: `${errors}/${sources.length} fuentes con error de red: ${errorDetails.slice(0, 2).join("; ")}` };
  }
  // Otherwise enough sources said "no" — call it not_found.
  return { status: "not_found", detail: `sin match en CrossRef/OpenAlex/Semantic Scholar/Google Books/OpenLibrary/arXiv${apa}` };
}

function titleSimilar(a, b) {
  const norm = (s) => (s || "").toLowerCase().replace(/\W+/g, "");
  const na = norm(a), nb = norm(b);
  if (!na || !nb) return false;
  if (na.includes(nb) || nb.includes(na)) return true;
  const toksA = new Set((a || "").toLowerCase().match(/\w+/g)?.filter((x) => x.length > 3) || []);
  const toksB = new Set((b || "").toLowerCase().match(/\w+/g)?.filter((x) => x.length > 3) || []);
  if (!toksA.size) return false;
  let overlap = 0;
  for (const x of toksA) if (toksB.has(x)) overlap++;
  return overlap / toksA.size >= 0.75;
}

async function verifyOpenAlexJs(ref) {
  const params = new URLSearchParams({ search: ref.title, "per-page": "3" });
  if (ref.year) params.set("filter", `from_publication_date:${ref.year}-01-01,to_publication_date:${ref.year}-12-31`);
  const url = `https://api.openalex.org/works?${params.toString()}`;
  try {
    const r = await fetchWithTimeout(url, { headers: { Accept: "application/json" } });
    if (!r.ok) return { status: "error", detail: `OpenAlex HTTP ${r.status}` };
    const d = await r.json();
    for (const item of (d.results || [])) {
      const found = item.display_name || item.title || "";
      const year = item.publication_year ? String(item.publication_year) : "";
      if (titleSimilar(ref.title, found) && (!ref.year || !year || year === ref.year)) {
        const url = item.doi ? `https://doi.org/${item.doi.replace(/^https?:\/\/doi\.org\//i, "")}` : (item.id || null);
        return { status: "exists", detail: `OpenAlex${year ? ` (${year})` : ""}: ${found}`, url };
      }
    }
    return { status: "not_found", detail: "sin match en OpenAlex" };
  } catch (e) {
    return { status: "error", detail: `OpenAlex: ${e.name === "AbortError" ? "timeout" : e.message}` };
  }
}

async function verifySemanticScholarJs(ref) {
  const params = new URLSearchParams({ query: ref.title, limit: "3", fields: "title,year" });
  const url = `https://api.semanticscholar.org/graph/v1/paper/search?${params.toString()}`;
  try {
    const r = await fetchWithTimeout(url, { headers: { Accept: "application/json" } });
    if (!r.ok) return { status: "error", detail: `Semantic Scholar HTTP ${r.status}` };
    const d = await r.json();
    for (const item of (d.data || [])) {
      const found = item.title || "";
      const year = item.year ? String(item.year) : "";
      if (titleSimilar(ref.title, found) && (!ref.year || !year || year === ref.year)) {
        const url = item.paperId ? `https://www.semanticscholar.org/paper/${item.paperId}` : null;
        return { status: "exists", detail: `Semantic Scholar${year ? ` (${year})` : ""}: ${found}`, url };
      }
    }
    return { status: "not_found", detail: "sin match en Semantic Scholar" };
  } catch (e) {
    return { status: "error", detail: `Semantic Scholar: ${e.name === "AbortError" ? "timeout" : e.message}` };
  }
}

async function verifyGoogleBooksJs(ref) {
  // Build query: prefer "intitle: + inauthor:" for precision; fallback to plain title
  const parts = [];
  if (ref.title) parts.push(`intitle:${ref.title}`);
  if (ref.author) parts.push(`inauthor:${ref.author}`);
  const q = parts.length ? parts.join("+") : (ref.title || "");
  if (!q) return { status: "unverifiable", detail: "Google Books: sin título" };
  const url = `https://www.googleapis.com/books/v1/volumes?q=${encodeURIComponent(q)}&maxResults=3&printType=books`;
  try {
    const r = await fetchWithTimeout(url);
    if (!r.ok) return { status: "error", detail: `Google Books HTTP ${r.status}` };
    const d = await r.json();
    const items = d.items || [];
    for (const item of items) {
      const v = item.volumeInfo || {};
      const found = v.title || "";
      const subtitle = v.subtitle ? `: ${v.subtitle}` : "";
      const fullTitle = `${found}${subtitle}`;
      const year = v.publishedDate ? String(v.publishedDate).slice(0, 4) : "";
      const authors = (v.authors || []).join(", ");
      if (titleSimilar(ref.title, fullTitle) && (!ref.year || !year || year === ref.year)) {
        const detail = authors
          ? `Google Books${year ? ` (${year})` : ""}: ${authors} — ${fullTitle}`
          : `Google Books${year ? ` (${year})` : ""}: ${fullTitle}`;
        const url = v.canonicalVolumeLink || v.previewLink || (v.industryIdentifiers && v.industryIdentifiers[0]
          ? `https://books.google.com/books?vid=ISBN${v.industryIdentifiers[0].identifier}` : null);
        return { status: "exists", detail, url };
      }
    }
    return { status: "not_found", detail: "sin match en Google Books" };
  } catch (e) {
    return { status: "error", detail: e.message };
  }
}

async function verifyIsbnJs(isbn) {
  const clean = String(isbn || "").replace(/[^0-9Xx]/g, "");
  if (!clean) return { status: "unverifiable", detail: "ISBN vacío" };
  try {
    const r = await fetch(`https://openlibrary.org/isbn/${encodeURIComponent(clean)}.json`, { headers: { Accept: "application/json" } });
    if (r.status === 404) return { status: "not_found", detail: "OpenLibrary: not found" };
    if (!r.ok) return { status: "error", detail: `OpenLibrary HTTP ${r.status}` };
    const d = await r.json();
    return d.title ? { status: "exists", detail: `OpenLibrary: ${d.title}`, url: `https://openlibrary.org/isbn/${encodeURIComponent(clean)}` } : { status: "not_found", detail: "OpenLibrary sin título" };
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
  if (name.endsWith(".pdf")) {
    return await handlePdf(file);
  }
  const isText = ["text/plain", "text/markdown", ""].includes(file.type) ||
                 /\.(txt|md|markdown)$/i.test(file.name);
  if (!isText) {
    setStatus(`${t.error} ${file.name}`, true);
    return;
  }
  const text = await file.text();
  els.input.value = text;
  await analyze();
}

// PDF text extraction via pdf.js (Mozilla). No OCR — only embedded text layers.
let _pdfjsLib = null;
async function loadPdfJs() {
  if (_pdfjsLib) return _pdfjsLib;
  const PDFJS_VER = "4.7.76";
  const base = `https://cdn.jsdelivr.net/npm/pdfjs-dist@${PDFJS_VER}/build`;
  const mod = await import(`${base}/pdf.min.mjs`);
  mod.GlobalWorkerOptions.workerSrc = `${base}/pdf.worker.min.mjs`;
  _pdfjsLib = mod;
  return mod;
}

async function extractPdfText(file) {
  const pdfjs = await loadPdfJs();
  const buf = await file.arrayBuffer();
  const doc = await pdfjs.getDocument({ data: buf }).promise;
  const out = [];
  for (let i = 1; i <= doc.numPages; i++) {
    const page = await doc.getPage(i);
    const content = await page.getTextContent();
    // Reconstruct lines: pdf.js gives us items with positions. Group by Y.
    const lines = new Map();
    for (const item of content.items) {
      if (!item.str) continue;
      const y = Math.round(item.transform[5]);
      if (!lines.has(y)) lines.set(y, []);
      lines.get(y).push(item);
    }
    const ys = [...lines.keys()].sort((a, b) => b - a);
    for (const y of ys) {
      const items = lines.get(y).sort((a, b) => a.transform[4] - b.transform[4]);
      out.push(items.map((x) => x.str).join(" ").replace(/\s+/g, " ").trim());
    }
    out.push(""); // page break
  }
  return out.join("\n").replace(/\n{3,}/g, "\n\n").trim();
}

async function handlePdf(file) {
  const t = I18N[UILANG];
  setStatus(t.pdf_extracting || "extrayendo texto del PDF…");
  try {
    const text = await extractPdfText(file);
    if (!text || text.length < 20) {
      setStatus(t.pdf_no_text || "El PDF no tiene capa de texto (probablemente escaneado). Sin OCR no puedo leerlo.", true);
      return;
    }
    els.input.value = text;
    document.body.classList.add("has-text");
    setStatus(null);
    await analyze();
  } catch (err) {
    console.error("pdf extract failed", err);
    setStatus(`${t.error} PDF: ${err.message}`, true);
  }
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
    //    If smell is high, fuse the Intelecta nudge into the same card so it
    //    doesn't repeat the same message twice.
    const isHighSmell = report && report.score >= 0.6;
    const intelectaInline = isHighSmell ? `
      <div class="docx-intelecta">
        <span class="mark">⚠</span>
        <span class="text">${escapeHtml(t.high_smell_note)}</span>
        <a href="https://intelecta.cl/cotizador" target="_blank" rel="noopener">${escapeHtml(t.high_smell_cta)}</a>
      </div>` : "";
    const downloadHtml = `
      <div class="docx-download${isHighSmell ? " docx-download-fused" : ""}">
        <div class="docx-download-row">
          <div class="docx-download-text">
            ${t.docx_done.replace("{name}", `<strong>${escapeHtml(outName)}</strong>`)}
          </div>
          <a class="btn" id="docxDownloadBtn" href="${url}" download="${escapeHtml(outName)}">⬇ ${escapeHtml(t.download_docx_btn || outName)}</a>
        </div>
        ${intelectaInline}
      </div>`;
    els.findings.insertAdjacentHTML("afterbegin", downloadHtml);

    // If we already inlined the smell nudge, remove any duplicate one
    // that render() might have placed in the score panel.
    if (isHighSmell) {
      const dup = els.score.querySelector(".intelecta-nudge[data-intelecta-nudge='smell']");
      if (dup) dup.remove();
    }

    // Keep the blob alive for a couple of minutes so the user can click when ready.
    setTimeout(() => URL.revokeObjectURL(url), 120000);

    setStatus(null);

    // Optional: bibliography verification on the extracted text
    if (extractedText.trim() && extractRefsFn) {
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

// ---------- About modal ----------
const aboutModal = document.getElementById("aboutModal");
const aboutBtn = document.getElementById("aboutBtn");
function openAbout() { aboutModal.hidden = false; document.body.style.overflow = "hidden"; }
function closeAbout() { aboutModal.hidden = true; document.body.style.overflow = ""; }
if (aboutBtn) aboutBtn.addEventListener("click", openAbout);
if (aboutModal) {
  aboutModal.querySelector(".close").addEventListener("click", closeAbout);
  aboutModal.addEventListener("click", (e) => {
    if (e.target === aboutModal) closeAbout();
  });
}

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && !disclaimerModal.hidden) closeDisclaimer();
  if (e.key === "Escape" && aboutModal && !aboutModal.hidden) closeAbout();
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
