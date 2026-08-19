import { checkBibliography } from "./bibliography.js";
import { lookupBibliography } from "./lookup.js";
import { cleanText, inspectText } from "./unicode_strip.js";

const MAX_CHARS = 3000;
const MAX_BIBLIOGRAPHY_CHARS = 12000;
const MODEL = "@cf/meta/llama-4-scout-17b-16e-instruct";
const VERSION = "2026-08-19-strip-marks-v1";

// Layer B rewrite prompts, ported from guillaumemeyer/watermarks-remover
// (MIT) service/scripts/rewrite_text.py PROMPTS dict.
const WATERMARK_PROMPTS = {
  paraphrase:
    "Rewrite the following text so that it uses substantially different wording at the token level. Change clause order, connectors, and transition words; vary sentence boundaries and length; and replace both content words and function words where meaning allows. Preserve all facts, numbers, names, and technical identifiers. Do not add or remove claims. Output only the rewritten text.\n\n---\n{TEXT}",
  humanize:
    "Rewrite the following text so it reads as if a human wrote it from scratch. Vary sentence rhythm and length, replace formulaic AI-style transitions and filler with concrete natural phrasing, and use plain, varied wording. Preserve all facts, numbers, names, and technical identifiers. Do not add or remove claims. Output only the rewritten text.\n\n---\n{TEXT}",
};

// Bigram Jaccard lexical divergence, ported from rewrite_text.py.
function tokens(text) {
  const matches = text.toLowerCase().match(/[a-z0-9]+/g);
  return matches || [];
}
function bigrams(list) {
  const out = new Set();
  for (let i = 0; i + 1 < list.length; i++) out.add(list[i] + "\u0000" + list[i + 1]);
  return out;
}
function lexicalDivergence(original, candidate) {
  const a = tokens(original);
  const b = tokens(candidate);
  if (!a.length && !b.length) return 0;
  if (!a.length || !b.length) return 1;
  const ba = bigrams(a);
  const bb = bigrams(b);
  const union = new Set([...ba, ...bb]);
  if (!union.size) return 0;
  let intersection = 0;
  for (const item of ba) if (bb.has(item)) intersection++;
  return Number((1 - intersection / union.size).toFixed(4));
}


function headers(origin = "") {
  return {
    "Content-Type": "application/json; charset=utf-8",
    "Cache-Control": "no-store",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "interest-cohort=()",
    "Access-Control-Allow-Origin": origin || "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Vary": "Origin",
  };
}

function json(data, init = {}, origin = "") {
  return new Response(JSON.stringify(data), { ...init, headers: { ...headers(origin), ...(init.headers || {}) } });
}

function editorPrompt(language, findings, mode) {
  const languageName = language === "es" ? "Spanish" : "English";
  const signalList = Array.isArray(findings) && findings.length ? findings.join(", ") : "none supplied";
  const instruction = mode === "improve"
    ? [
        "Make the improvement noticeable but faithful.",
        "Cut ceremonial openings and closings, institutional boilerplate, generic motivational claims, redundant pairs, abstract nouns, passive constructions, and stacked adjectives.",
        "Prefer concrete verbs, shorter sentences, and direct natural phrasing for the reader.",
        "Keep the writer's register professional and human; do not make it slangy, casual, or sales-like.",
      ].join(" ")
    : "Remove only high-confidence empty filler: stock transition phrases and connectors that add no meaning (such as 'por esta razón', 'it is important to note'), ceremonial openings, redundant pairs, and empty adjectives. Leave already-direct wording alone. Do not paraphrase or restructure sentences that are fine.";
  return [
    "You are a precise line editor, not a paraphraser.",
    `Rewrite the user text in ${languageName}. ${instruction}`,
    "Preserve every fact, claim, name, date, number, URL, citation, quote, code fragment, list item, and the writer's register.",
    "Do not add information, praise, apologies, headings, bullets, or explanations. Do not translate.",
    "Keep existing markdown headings and titles exactly as they are.",
    "Strip leftover copy-paste formatting markers: remove literal markdown asterisks around bold text (like **word**), single asterisks, and backticks around code or filenames (like `file.xls`), keeping the words themselves. Remove other stray symbols only when they are clearly formatting residue, never when they are part of the meaning (URLs, citations, numbers, code).",
    "Start every new sentence after a period, exclamation, or question mark with a capital letter.",
    `aismell detected these possible signals: ${signalList}.`,
    "Return only valid JSON with exactly this shape: {\"text\":\"edited text\",\"changes\":[\"short factual description of each edit\"]}. If nothing needs changing, return the original text and an empty changes array.",
  ].join("\n");
}

function modelText(result) {
  if (typeof result === "string" || typeof result?.response === "string") return typeof result === "string" ? result : result.response;
  if (typeof result?.output_text === "string") return result.output_text;
  if (typeof result?.choices?.[0]?.message?.content === "string") return result.choices[0].message.content;
  const content = result?.output?.find((item) => item?.type === "message")?.content;
  if (typeof content === "string") return content;
  if (Array.isArray(content)) return content.map((item) => item?.text || "").join("");
  return "";
}

function parseModelResponse(result, original) {
  const raw = modelText(result);
  if (typeof raw !== "string") throw new Error("model returned no text");
  const fenced = raw.trim().replace(/^```(?:json)?\s*/i, "").replace(/\s*```$/, "");
  const parsed = JSON.parse(fenced);
  if (typeof parsed?.text !== "string" || !parsed.text.trim() || parsed.text.length > MAX_CHARS) {
    throw new Error("model returned invalid edit");
  }
  const changes = Array.isArray(parsed.changes)
    ? parsed.changes.filter((item) => typeof item === "string" && item.trim()).slice(0, 12)
    : [];
  return { text: stripMarkdownResidue(parsed.text, changes), changes };
}

// Deterministic safety net: GPT/markdown copy-paste leaves literal **bold**,
// *emphasis* and `code` markers behind (the rich formatting does not survive
// the clipboard). The model is instructed to strip them too, but this ensures
// the output never ships with asterisk/backtick residue even if it does not.
export function stripMarkdownResidue(text, changes = []) {
  let stripped = text
    .replace(/\*\*([^*\n]+)\*\*/g, "$1")
    .replace(/`([^`\n]+)`/g, "$1")
    .split("\n")
    .map((line) => capitalizeAfterSentenceEnd(line.replace(/[ \t]{2,}/g, " ").trimEnd()))
    .join("\n");
  if (stripped !== text && !changes.some((item) => /marcadores|asteriscos|backticks|formato|markdown/i.test(item))) {
    changes.push("quitó marcadores de formato sobrantes (asteriscos y backticks)");
  }
  return stripped;
}

// Common abbreviations that end with a period but do NOT start a new sentence.
// The capitalizer must leave these alone: "etc. y más", "Sr. Pérez".
const SENTENCE_END_ABBREVIATIONS = new Set([
  "a", "c", "d", // a. m., c. (siglo), d. (don)
  "aprox", "art", "av", "cap", "co", "corp", "dept", "dto", "dr", "dra", "ed",
  "eds", "ej", "etc", "fig", "gral", "inc", "ltd", "m", "mr", "mrs", "ms",
  "no", "nro", "núm", "p", "pág", "págs", "prof", "pto", "sr", "sra", "st",
  "tel", "ud", "uds", "vol", "vs", "univ",
]);

function capitalizeAfterSentenceEnd(line) {
  return line.replace(/([.!?])\s+([a-záéíóúñ])/g, (match, punctuation, letter, offset) => {
    if (punctuation !== ".") return `${punctuation} ${letter.toUpperCase()}`;
    // Check the word right before the period: if it is a known abbreviation,
    // this period is not a sentence end.
    const before = line.slice(0, offset);
    const wordMatch = before.match(/(\S+)\s*$/);
    const word = wordMatch ? wordMatch[1].replace(/[.,;:)]+$/, "").toLowerCase() : "";
    if (word && SENTENCE_END_ABBREVIATIONS.has(word)) return match;
    return `${punctuation} ${letter.toUpperCase()}`;
  });
}

async function analyzeWithAismell(env, text) {
  if (!env?.ANALYZER?.fetch) throw new Error("aismell analyzer unavailable");
  const response = await env.ANALYZER.fetch("https://aismell-analyzer/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!response.ok) throw new Error("aismell analyzer unavailable");
  const result = await response.json();
  if (!result || (result.language !== "es" && result.language !== "en") || !Array.isArray(result.findings)) {
    throw new Error("aismell analyzer returned invalid data");
  }
  return {
    language: result.language,
    findings: result.findings
      .filter((finding) => typeof finding?.id === "string")
      .map((finding) => `${finding.id}${typeof finding.matched === "string" ? ` (${finding.matched})` : ""}`)
      .slice(0, 24),
  };
}

export async function handleBibliography(request, env) {
  let body;
  try {
    body = await request.json();
  } catch {
    return json({ error: "invalid-request" }, { status: 400 }, request.headers.get("Origin") || "");
  }

  const text = typeof body?.text === "string" ? body.text.trim() : "";
  const origin = request.headers.get("Origin") || "";
  if (!text) return json({ error: "empty" }, { status: 400 }, origin);
  if (text.length > MAX_BIBLIOGRAPHY_CHARS) return json({ error: "too-long" }, { status: 400 }, origin);

  try {
    const analysis = await analyzeWithAismell(env, text.slice(0, MAX_CHARS));
    const report = checkBibliography(text, analysis);
    report.lookup = await lookupBibliography(report.entries, env?.LOOKUP_FETCH || globalThis.fetch);
    return json(report, {}, origin);
  } catch (error) {
    if (error?.message === "empty" || error?.message === "too-long") {
      return json({ error: error.message }, { status: 400 }, origin);
    }
    console.error("bibliography check failed", error?.message || "unknown");
    return json({ error: "bibliography-unavailable" }, { status: 503 }, origin);
  }
}

export async function handleRewrite(request, env) {
  let body;
  try {
    body = await request.json();
  } catch {
    return json({ error: "invalid-request" }, { status: 400 }, request.headers.get("Origin") || "");
  }

  const text = typeof body?.text === "string" ? body.text.trim() : "";
  const mode = body?.mode === "improve" ? "improve" : "clean";
  const origin = request.headers.get("Origin") || "";
  if (!text) return json({ error: "empty" }, { status: 400 }, origin);
  if (text.length > MAX_CHARS) return json({ error: "too-long" }, { status: 400 }, origin);
  if (!env?.AI?.run) return json({ error: "rewrite-unavailable" }, { status: 503 }, origin);

  try {
    const analysis = await analyzeWithAismell(env, text);
    const response = await env.AI.run(MODEL, {
      messages: [
        { role: "system", content: editorPrompt(analysis.language, analysis.findings, mode) },
        { role: "user", content: text },
      ],
      response_format: { type: "json_object" },
      max_tokens: 1024,
      temperature: 0.15,
    });
    return json(parseModelResponse(response, text), {}, origin);
  } catch (error) {
    console.error("rewrite failed", error?.message || "unknown");
    return json({ error: "rewrite-unavailable" }, { status: 503 }, origin);
  }
}

export async function handleStripMarks(request, env) {
  let body;
  try {
    body = await request.json();
  } catch {
    return json({ error: "invalid-request" }, { status: 400 }, request.headers.get("Origin") || "");
  }

  const text = typeof body?.text === "string" ? body.text : "";
  const mode = body?.mode === "inspect" ? "inspect" : "clean";
  const strength = body?.strength === "humanize" ? "humanize" : "paraphrase";
  const options = {
    nfkc: !!body?.nfkc,
    aggressiveHomoglyphs: !!body?.aggressive_homoglyphs,
    stripBidi: !!body?.strip_bidi,
    stripEmojiGlue: !!body?.strip_emoji_glue,
  };
  const origin = request.headers.get("Origin") || "";
  if (!text.trim()) return json({ error: "empty" }, { status: 400 }, origin);
  if (text.length > MAX_CHARS) return json({ error: "too-long" }, { status: 400 }, origin);

  try {
    if (mode === "inspect") {
      return json({ ok: true, mode: "inspect", report: inspectText(text, { aggressive: options.aggressiveHomoglyphs, stripEmojiGlue: options.stripEmojiGlue }) }, {}, origin);
    }

    const layerA = cleanText(text, options);
    const result = { ok: true, mode: "clean", text: layerA.text, stats: layerA.stats };

    if (body?.rewrite && env?.AI?.run) {
      const prompt = WATERMARK_PROMPTS[strength].replace("{TEXT}", layerA.text);
      const response = await env.AI.run(MODEL, {
        messages: [{ role: "user", content: prompt }],
        max_tokens: 1024,
        temperature: 0.8,
      });
      const rewritten = modelText(response).trim();
      if (rewritten) {
        result.text = rewritten;
        result.rewrite = {
          strength,
          lexical_divergence: lexicalDivergence(layerA.text, rewritten),
          original_length: layerA.text.length,
          rewritten_length: rewritten.length,
        };
      }
    } else if (body?.rewrite) {
      result.rewrite = { error: "rewrite-unavailable" };
    }

    return json(result, {}, origin);
  } catch (error) {
    console.error("strip-marks failed", error?.message || "unknown");
    return json({ error: "strip-marks-unavailable" }, { status: 503 }, origin);
  }
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const origin = request.headers.get("Origin") || "";
    if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: headers(origin) });
    if (url.pathname === "/health" && request.method === "GET") return json({ ok: true, version: VERSION }, {}, origin);
    if (url.pathname === "/rewrite" && request.method === "POST") return handleRewrite(request, env);
    if (url.pathname === "/bibliography" && request.method === "POST") return handleBibliography(request, env);
    if (url.pathname === "/strip-marks" && request.method === "POST") return handleStripMarks(request, env);
    return json({ error: "not-found" }, { status: 404 }, origin);
  },
};
