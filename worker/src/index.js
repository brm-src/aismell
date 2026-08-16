const MAX_CHARS = 3000;
const MODEL = "@cf/meta/llama-4-scout-17b-16e-instruct";
const VERSION = "2026-08-16-rewrite-v1";

function headers(origin = "") {
  return {
    "Content-Type": "application/json; charset=utf-8",
    "Cache-Control": "no-store",
    "Access-Control-Allow-Origin": origin || "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Vary": "Origin",
  };
}

function json(data, init = {}, origin = "") {
  return new Response(JSON.stringify(data), { ...init, headers: { ...headers(origin), ...(init.headers || {}) } });
}

function editorPrompt(language, findings) {
  const languageName = language === "es" ? "Spanish" : "English";
  const signalList = Array.isArray(findings) && findings.length ? findings.join(", ") : "none supplied";
  return [
    "You are a precise line editor, not a paraphraser.",
    `Rewrite the user text in ${languageName} to remove empty AI-sounding filler. Preserve every fact, claim, name, date, number, URL, citation, quote, code fragment, list item, and the writer's register.`,
    "Do not add information, praise, apologies, headings, bullets, or explanations. Do not translate. Keep wording unchanged when it is already direct.",
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

export async function handleRewrite(request, env) {
  let body;
  try {
    body = await request.json();
  } catch {
    return json({ error: "invalid-request" }, { status: 400 }, request.headers.get("Origin") || "");
  }

  const text = typeof body?.text === "string" ? body.text.trim() : "";
  const origin = request.headers.get("Origin") || "";
  if (!text) return json({ error: "empty" }, { status: 400 }, origin);
  if (text.length > MAX_CHARS) return json({ error: "too-long" }, { status: 400 }, origin);
  if (!env?.AI?.run) return json({ error: "rewrite-unavailable" }, { status: 503 }, origin);

  try {
    const response = await env.AI.run(MODEL, {
      messages: [
        { role: "system", content: editorPrompt(body.language, body.findings) },
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
