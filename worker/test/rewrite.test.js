import test from "node:test";
import assert from "node:assert/strict";
import { handleRewrite } from "../src/index.js";

const text = "It is important to note that the report is ready.";

function analyzer(payload = {
  language: "en",
  findings: [{ id: "en.important_to_note", matched: "It is important to note", severity: 3 }],
}) {
  return {
    async fetch(url, init) {
      assert.equal(new URL(url).pathname, "/analyze");
      assert.deepEqual(JSON.parse(init.body), { text });
      return new Response(JSON.stringify(payload), { status: 200 });
    },
  };
}

test("runs the actual aismell analyzer before rewriting a short text", async () => {
  const calls = [];
  const ai = {
    async run(model, request) {
      calls.push({ model, request });
      return { response: JSON.stringify({ text: "The report is ready.", changes: ["Removed filler"] }) };
    },
  };
  const response = await handleRewrite(new Request("https://api.example/rewrite", {
    method: "POST", body: JSON.stringify({ text }),
  }), { AI: ai, ANALYZER: analyzer() });

  assert.equal(response.status, 200);
  assert.deepEqual(await response.json(), { text: "The report is ready.", changes: ["Removed filler"] });
  assert.equal(calls.length, 1);
  assert.equal(calls[0].model, "@cf/meta/llama-4-scout-17b-16e-instruct");
  assert.match(calls[0].request.messages[0].content, /en\.important_to_note/);
});

test("accepts the current Workers AI output message shape", async () => {
  const ai = { async run() {
    return { output: [{ type: "message", content: JSON.stringify({ text: "The report is ready.", changes: ["Removed filler"] }) }] };
  } };
  const response = await handleRewrite(new Request("https://api.example/rewrite", {
    method: "POST", body: JSON.stringify({ text }),
  }), { AI: ai, ANALYZER: analyzer() });

  assert.equal(response.status, 200);
  assert.deepEqual(await response.json(), { text: "The report is ready.", changes: ["Removed filler"] });
});

test("rejects text over the plugin limit before invoking any downstream service", async () => {
  let called = false;
  const response = await handleRewrite(new Request("https://api.example/rewrite", {
    method: "POST", body: JSON.stringify({ text: "x".repeat(3001) }),
  }), { AI: { async run() { called = true; } }, ANALYZER: { async fetch() { called = true; } } });

  assert.equal(response.status, 400);
  assert.deepEqual(await response.json(), { error: "too-long" });
  assert.equal(called, false);
});

test("does not rewrite when aismell analysis is unavailable", async () => {
  let called = false;
  const response = await handleRewrite(new Request("https://api.example/rewrite", {
    method: "POST", body: JSON.stringify({ text }),
  }), { AI: { async run() { called = true; } }, ANALYZER: { async fetch() { return new Response("", { status: 503 }); } } });

  assert.equal(response.status, 503);
  assert.deepEqual(await response.json(), { error: "rewrite-unavailable" });
  assert.equal(called, false);
});

test("returns a safe upstream error instead of pretending a rewrite happened", async () => {
  const response = await handleRewrite(new Request("https://api.example/rewrite", {
    method: "POST", body: JSON.stringify({ text }),
  }), { AI: { async run() { throw new Error("quota"); } }, ANALYZER: analyzer() });

  assert.equal(response.status, 503);
  assert.deepEqual(await response.json(), { error: "rewrite-unavailable" });
});
