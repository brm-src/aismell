const MAX_CHARS = 3000;
const MODEL = "@cf/meta/llama-4-scout-17b-16e-instruct";
const VERSION = "2026-08-16-rewrite-v3";

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
    : "Remove only high-confidence empty AI-sounding filler and leave already-direct wording alone.";
  return [
    "You are a precise line editor, not a paraphraser.",
    `Rewrite the user text in ${languageName}. ${instruction}`,
    "Preserve every fact, claim, name, date, number, URL, citation, quote, code fragment, list item, and the writer's register.",
    "Do not add information, praise, apologies, headings, bullets, or explanations. Do not translate.",
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
  return { text: parsed.text, changes };
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

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const origin = request.headers.get("Origin") || "";
    if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: headers(origin) });
    if (url.pathname === "/health" && request.method === "GET") return json({ ok: true, version: VERSION }, {}, origin);
    if (url.pathname === "/rewrite" && request.method === "POST") return handleRewrite(request, env);
    return json({ error: "not-found" }, { status: 404 }, origin);
  },
};
