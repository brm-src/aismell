import test from "node:test";
import assert from "node:assert/strict";
import { handleRewrite, handleBibliography } from "../src/index.js";

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

test("uses a stronger humanizing prompt only in improve mode", async () => {
  let systemPrompt = "";
  const ai = {
    async run(model, request) {
      systemPrompt = request.messages[0].content;
      return { response: JSON.stringify({ text, changes: ["Shortened boilerplate"] }) };
    },
  };
  const response = await handleRewrite(new Request("https://api.example/rewrite", {
    method: "POST", body: JSON.stringify({ text, mode: "improve" }),
  }), { AI: ai, ANALYZER: analyzer() });

  assert.equal(response.status, 200);
  assert.match(systemPrompt, /Make the improvement noticeable but faithful/);
  assert.match(systemPrompt, /ceremonial openings and closings/);
});

test("clean mode targets stock transition phrases, not just AI-sounding filler", async () => {
  let systemPrompt = "";
  const ai = {
    async run(model, request) {
      systemPrompt = request.messages[0].content;
      return { response: JSON.stringify({ text, changes: [] }) };
    },
  };
  const response = await handleRewrite(new Request("https://api.example/rewrite", {
    method: "POST", body: JSON.stringify({ text }),
  }), { AI: ai, ANALYZER: analyzer() });

  assert.equal(response.status, 200);
  assert.match(systemPrompt, /stock transition phrases/);
  assert.match(systemPrompt, /por esta razón/);
  assert.match(systemPrompt, /Do not paraphrase or restructure sentences that are fine/);
});

test("clean mode preserves existing markdown headings in the rewrite instruction", async () => {
  let systemPrompt = "";
  const ai = {
    async run(model, request) {
      systemPrompt = request.messages[0].content;
      return { response: JSON.stringify({ text, changes: [] }) };
    },
  };
  const response = await handleRewrite(new Request("https://api.example/rewrite", {
    method: "POST", body: JSON.stringify({ text }),
  }), { AI: ai, ANALYZER: analyzer() });

  assert.equal(response.status, 200);
  assert.match(systemPrompt, /Keep existing markdown headings and titles exactly as they are/);
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

test("returns aismell-backed bibliography findings without pretending to verify sources", async () => {
  const bibliography = [
    "[1] García, M. (2024). Manual de investigación. https://doi.org/10.1234/demo",
    "[2] García, M. 2024. Manual de investigación. https://doi.org/10.1234/demo",
    "[3] Smith, J. (2021). A clear paper.",
  ].join("\n\n");
  const response = await handleBibliography(new Request("https://api.example/bibliography", {
    method: "POST", body: JSON.stringify({ text: bibliography }),
  }), {
    ANALYZER: {
      async fetch(url, init) {
        assert.equal(new URL(url).pathname, "/analyze");
        assert.deepEqual(JSON.parse(init.body), { text: bibliography });
        return new Response(JSON.stringify({
          language: "es",
          findings: [{ id: "es.vale_pena_destacar", matched: "vale la pena destacar" }],
        }), { status: 200 });
      },
    },
    LOOKUP_FETCH: async () => new Response("", { status: 404 }),
  });

  assert.equal(response.status, 200);
  const payload = await response.json();
  assert.equal(payload.entryCount, 3);
  assert.equal(payload.analysis.findingCount, 1);
  assert.equal(payload.method.source, "pasted-text");
  assert.equal(payload.method.separator, "blank-line boundaries");
  assert.ok(payload.method.fields.includes("title span"));
  assert.equal(payload.method.aismell.characters, bibliography.length);
  assert.equal(payload.entries[0].author, true);
  assert.equal(payload.entries[0].title, "Manual de investigación");
  assert.ok(payload.findings.some((finding) => finding.code === "duplicate-source"));
  assert.ok(payload.findings.some((finding) => finding.code === "mixed-year-style"));
  assert.ok(payload.findings.some((finding) => finding.code === "aismell-signal"));
});

test("indexes corporate authors, titles, identifiers, and publication locators", async () => {
  const bibliography = "World Health Organization. (2023). Global health report. Journal of Health, 10(2), 12-30. https://example.org/report";
  const response = await handleBibliography(new Request("https://api.example/bibliography", {
    method: "POST", body: JSON.stringify({ text: bibliography }),
  }), {
    ANALYZER: {
      async fetch() {
        return new Response(JSON.stringify({ language: "en", findings: [] }), { status: 200 });
      },
    },
    LOOKUP_FETCH: async () => new Response("", { status: 404 }),
  });

  assert.equal(response.status, 200);
  const payload = await response.json();
  assert.equal(payload.entries[0].author, true);
  assert.equal(payload.entries[0].year, "2023");
  assert.equal(payload.entries[0].title, "Global health report");
  assert.equal(payload.entries[0].pages, true);
  assert.equal(payload.entries[0].volumeIssue, true);
  assert.equal(payload.method.covered.identifiers, 1);
});

test("rejects an oversized bibliography before calling aismell", async () => {
  let called = false;
  const response = await handleBibliography(new Request("https://api.example/bibliography", {
    method: "POST", body: JSON.stringify({ text: "x".repeat(12001) }),
  }), { ANALYZER: { async fetch() { called = true; } } });

  assert.equal(response.status, 400);
  assert.deepEqual(await response.json(), { error: "too-long" });
  assert.equal(called, false);
});
