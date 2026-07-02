// Carril 2 — semantic embedding analysis in browser.
// Uses @xenova/transformers (ONNX in WASM/WebGPU). Model cached in IndexedDB after first load.
// Runs entirely client-side. Text never leaves the device.

const MODEL_ID = "Xenova/multilingual-e5-small";
// transformers.js v3 is the official @huggingface/transformers package with
// proper browser ESM and WebGPU/WASM backends. Build URL piecewise to avoid
// email-encoding rewriting "@<version>".
const _TX_VERSION = "3.0.2";
const TRANSFORMERS_CDN =
  "https://cdn.jsdelivr.net/npm/@huggingface/transformers" + "@" + _TX_VERSION;

let _pipelinePromise = null;
let _progressListeners = new Set();

function emitProgress(evt) {
  for (const fn of _progressListeners) {
    try { fn(evt); } catch (e) { console.error(e); }
  }
}

export function onModelProgress(fn) {
  _progressListeners.add(fn);
  return () => _progressListeners.delete(fn);
}

// Trigger silent preload — model bytes arrive while user reads/types.
// No UI side-effects unless caller subscribes to progress.
export function preloadEmbeddings() {
  // Fire and forget; ignore errors here, analyze() will retry and surface them.
  getPipeline().catch((err) => {
    console.warn("embedding preload failed:", err);
  });
}

async function getPipeline() {
  if (_pipelinePromise) return _pipelinePromise;
  _pipelinePromise = (async () => {
    const transformers = await import(TRANSFORMERS_CDN);
    transformers.env.allowLocalModels = false;
    transformers.env.useBrowserCache = true;
    return await transformers.pipeline("feature-extraction", MODEL_ID, {
      progress_callback: (p) => emitProgress(p),
    });
  })();
  return _pipelinePromise;
}

// Cosine similarity between two vectors.
function cosine(a, b) {
  let dot = 0, na = 0, nb = 0;
  for (let i = 0; i < a.length; i++) {
    dot += a[i] * b[i];
    na += a[i] * a[i];
    nb += b[i] * b[i];
  }
  const denom = Math.sqrt(na) * Math.sqrt(nb);
  return denom === 0 ? 0 : dot / denom;
}

function mean(xs) {
  if (!xs.length) return 0;
  return xs.reduce((a, b) => a + b, 0) / xs.length;
}

function stdev(xs) {
  if (xs.length < 2) return 0;
  const m = mean(xs);
  const v = xs.reduce((acc, x) => acc + (x - m) ** 2, 0) / (xs.length - 1);
  return Math.sqrt(v);
}

function countMatches(text, rx) {
  return (text.match(rx) || []).length;
}

function wordCount(text) {
  return (text.match(/[\p{L}\p{N}_'-]+/gu) || []).length;
}

function storyScopeSurfaceSignals(text, lang, paragraphs, metrics) {
  // StoryScope's useful product lesson: don't stop at style. Look for discourse
  // choices that LLM fiction tends to make — explicit moralizing, tidy single-
  // track arcs, and closures that explain the point instead of earning it.
  // These are lightweight, interpretable proxies; not a classifier.
  const findings = [];
  const words = Math.max(1, wordCount(text));
  const es = lang === "es";
  const themeRx = es
    ? /\b(tema|temas|moral|moraleja|lecci[oó]n|enseñanza|significado|sentido profundo|reflexi[oó]n|comprendi[oó]|comprender|aprendi[oó]|aprendizaje|verdad profunda|prop[oó]sito|humanidad|esperanza|redenci[oó]n)\b/gi
    : /\b(theme|themes|moral|lesson|meaning|deeper meaning|reflection|realized|understood|learned|truth|purpose|humanity|hope|redemption)\b/gi;
  const narratorMoralRx = es
    ? /\b(la historia (?:nos )?(?:enseña|recuerda|muestra)|esto (?:nos )?(?:enseña|recuerda|muestra)|al final,? (?:comprendi[oó]|aprendi[oó])|en (?:el )?fondo|m[aá]s all[aá] de)\b/gi
    : /\b(the story (?:teaches|reminds|shows)|this (?:teaches|reminds|shows) us|in the end,? (?:he|she|they|i) (?:realized|understood|learned)|deep down|beyond the)\b/gi;
  const themeHits = countMatches(text, themeRx) + countMatches(text, narratorMoralRx) * 2;
  const themeDensity = themeHits / (words / 1000);
  if (paragraphs.length >= 4 && themeHits >= 5 && themeDensity >= 8) {
    findings.push({
      kind: "discourse-overexplained-theme",
      severity: themeHits >= 9 ? 3 : 2,
      message: es
        ? `el texto explica su tema demasiadas veces (${themeHits} marcas) — StoryScope: la IA suele moralizar y cerrar el sentido`
        : `the text explains its theme too often (${themeHits} marks) — StoryScope: AI tends to moralize and close meaning down`,
      suggestion: es
        ? "borra una explicación del tema y reemplázala por una escena, un gesto, una contradicción o un detalle que deje inferir la idea"
        : "delete one explanation of the theme and replace it with a scene, gesture, contradiction, or detail that lets the idea be inferred",
    });
  }

  const closing = paragraphs[paragraphs.length - 1] || "";
  const tidyCloseRx = es
    ? /\b(al final|finalmente|en [uú]ltima instancia|en definitiva|desde ese momento|para siempre|comprendi[oó] que|aprendi[oó] que|lo que realmente importaba|un nuevo comienzo)\b/gi
    : /\b(in the end|ultimately|finally|from that day forward|forever changed|realized that|learned that|what truly mattered|new beginning)\b/gi;
  const tidyCloseHits = countMatches(closing, tidyCloseRx);
  if (paragraphs.length >= 4 && tidyCloseHits >= 2 && metrics.openClose >= 0.84) {
    findings.push({
      kind: "discourse-tidy-resolution",
      severity: 2,
      message: es
        ? `cierre demasiado ordenado (${tidyCloseHits} marcas y similitud apertura/cierre ${metrics.openClose.toFixed(2)}) — resolución de IA muy prolija`
        : `overly tidy ending (${tidyCloseHits} marks and opening/closing similarity ${metrics.openClose.toFixed(2)}) — AI-style neat resolution`,
      suggestion: es
        ? "quita la frase que explica la lección y termina con una consecuencia concreta o una duda que no quede totalmente resuelta"
        : "remove the sentence explaining the lesson and end with a concrete consequence or a question that stays partly unresolved",
    });
  }

  return findings;
}

// Split into paragraphs of meaningful length (>=15 words).
function splitParagraphs(text) {
  return text
    .split(/\n\s*\n/)
    .map((p) => p.trim())
    .filter((p) => p.split(/\s+/).length >= 15);
}

async function embed(extractor, texts) {
  // e5 family expects "passage: " prefix for documents.
  const inputs = texts.map((t) => "passage: " + t);
  const out = await extractor(inputs, { pooling: "mean", normalize: true });
  // out.dims = [batch, dim]
  const dim = out.dims[1];
  const data = out.data;
  const vectors = [];
  for (let i = 0; i < texts.length; i++) {
    vectors.push(Array.from(data.slice(i * dim, (i + 1) * dim)));
  }
  return vectors;
}

// Main entry point. Returns a list of structural findings to merge into the report.
// `lang` is "es" | "en", used to localize messages.
export async function analyzeEmbeddings(text, lang = "es") {
  const paragraphs = splitParagraphs(text);
  if (paragraphs.length < 4) {
    // Not enough material for a meaningful semantic shape.
    return { findings: [], metrics: null, skipped: "too-short" };
  }

  const extractor = await getPipeline();
  const vectors = await embed(extractor, paragraphs);

  // Pairwise consecutive similarity (paragraph N vs N+1).
  const consecSims = [];
  for (let i = 0; i < vectors.length - 1; i++) {
    consecSims.push(cosine(vectors[i], vectors[i + 1]));
  }
  // Open ↔ close similarity (first paragraph vs last).
  const openClose = cosine(vectors[0], vectors[vectors.length - 1]);
  // All-pairs mean similarity (overall topical concentration).
  const allSims = [];
  for (let i = 0; i < vectors.length; i++) {
    for (let j = i + 1; j < vectors.length; j++) {
      allSims.push(cosine(vectors[i], vectors[j]));
    }
  }

  const metrics = {
    paragraphs: paragraphs.length,
    consecMean: mean(consecSims),
    consecStdev: stdev(consecSims),
    openClose,
    allMean: mean(allSims),
    allStdev: stdev(allSims),
  };

  const findings = [];

  // 1. Excessive paragraph cohesion: LLMs rarely change topic abruptly.
  // Thresholds calibrated against multilingual-e5-small, which already produces
  // high baselines. Human prose typically lands consec_mean < 0.85.
  if (metrics.consecMean >= 0.92) {
    findings.push({
      kind: "semantic-cohesion-high",
      severity: 3,
      message:
        lang === "es"
          ? `cohesión semántica entre párrafos muy alta (${metrics.consecMean.toFixed(2)}) — patrón LLM`
          : `paragraph-to-paragraph semantic cohesion very high (${metrics.consecMean.toFixed(2)}) — LLM pattern`,
      suggestion:
        lang === "es"
          ? "permite que algún párrafo cambie de plano (ejemplo, anécdota, voz directa)"
          : "let one paragraph shift register (anecdote, direct voice, tangent)",
    });
  } else if (metrics.consecMean >= 0.88) {
    findings.push({
      kind: "semantic-cohesion-mid",
      severity: 2,
      message:
        lang === "es"
          ? `cohesión semántica alta entre párrafos (${metrics.consecMean.toFixed(2)})`
          : `high semantic cohesion between paragraphs (${metrics.consecMean.toFixed(2)})`,
      suggestion:
        lang === "es"
          ? "varía el ángulo entre párrafos para que respiren"
          : "vary angle between paragraphs",
    });
  }

  // 2. Low semantic variance: LLMs orbit around a single topic uniformly.
  if (metrics.allStdev < 0.04 && metrics.allMean > 0.85) {
    findings.push({
      kind: "semantic-uniformity",
      severity: 3,
      message:
        lang === "es"
          ? `varianza semántica plana (σ=${metrics.allStdev.toFixed(3)}) — texto orbita un solo tema sin desviarse`
          : `flat semantic variance (σ=${metrics.allStdev.toFixed(3)}) — single-topic orbit`,
      suggestion:
        lang === "es"
          ? "introduce digresiones, contraejemplos o un quiebre tonal"
          : "add a digression, counter-example, or tonal break",
    });
  }

  // 3. Open ↔ close very tight: LLMs return where they started.
  if (metrics.openClose >= 0.90) {
    findings.push({
      kind: "semantic-loop-closed",
      severity: 2,
      message:
        lang === "es"
          ? `apertura y cierre casi idénticos semánticamente (${metrics.openClose.toFixed(2)}) — el texto vuelve al punto de partida`
          : `opening and closing nearly identical (${metrics.openClose.toFixed(2)}) — text loops back`,
      suggestion:
        lang === "es"
          ? "deja que el cierre derive — un texto humano rara vez vuelve al punto exacto"
          : "let the closing drift — human texts rarely return to the exact start",
    });
  }

  findings.push(...storyScopeSurfaceSignals(text, lang, paragraphs, metrics));

  return { findings, metrics, skipped: null };
}
