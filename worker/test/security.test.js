import test from "node:test";
import assert from "node:assert/strict";
import worker from "../src/index.js";

const text = "The report is ready.";

function request(path, body) {
  return new Request(`https://api.example/${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

test("strip-marks sends text to AI only with literal boolean consent", async () => {
  let calls = 0;
  const env = { AI: { async run() { calls++; return { response: "Edited report." }; } } };
  for (const rewrite of [undefined, false, "false", "true", 1, {}, []]) {
    const response = await worker.fetch(request("strip-marks", { text, rewrite }), env);
    assert.equal(response.status, 200);
    assert.equal((await response.json()).text, text);
  }
  assert.equal(calls, 0);

  const response = await worker.fetch(request("strip-marks", { text, rewrite: true }), env);
  assert.equal(response.status, 200);
  assert.equal((await response.json()).text, "Edited report.");
  assert.equal(calls, 1);
});

for (const path of ["rewrite", "bibliography", "strip-marks"]) {
  test(`${path} never logs upstream exception messages containing private text`, async (t) => {
    const privateText = "PRIVATE-SENTINEL-REPORT";
    const logs = t.mock.method(console, "error", () => {});
    const fail = async () => { throw new Error(privateText); };
    const response = await worker.fetch(request(path, { text: privateText, rewrite: true }), {
      ANALYZER: { fetch: fail }, AI: { run: fail },
    });
    assert.equal(response.status, 503);
    assert.ok(logs.mock.calls.length > 0);
    assert.ok(!JSON.stringify(logs.mock.calls.map((call) => call.arguments)).includes(privateText));
    assert.ok(!(await response.text()).includes(privateText));
  });
}

test("rewrite never logs malformed model output embedded in JSON parse errors", async (t) => {
  const privateText = "PRIVATE-SENTINEL-REPORT";
  const logs = t.mock.method(console, "error", () => {});
  const response = await worker.fetch(request("rewrite", { text: privateText }), {
    ANALYZER: { async fetch() { return Response.json({ language: "en", findings: [] }); } },
    AI: { async run() { return { response: privateText }; } },
  });
  assert.equal(response.status, 503);
  assert.ok(!JSON.stringify(logs.mock.calls.map((call) => call.arguments)).includes("PRIVATE"));
});
