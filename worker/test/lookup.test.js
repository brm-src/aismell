import test from "node:test";
import assert from "node:assert/strict";
import { lookupBibliography } from "../src/lookup.js";

function fetchFixture(url) {
  if (url.includes("api.crossref.org/works/10.1234%2Fdemo")) {
    return Promise.resolve(new Response(JSON.stringify({
      message: {
        DOI: "10.1234/demo",
        title: ["Manual de investigación"],
        author: [{ given: "M", family: "García" }],
        published: { "date-parts": [[2024]] },
        URL: "https://doi.org/10.1234/demo",
      },
    }), { status: 200 }));
  }
  if (url.includes("api.crossref.org")) {
    return Promise.resolve(new Response(JSON.stringify({ message: { items: [] } }), { status: 200 }));
  }
  return Promise.resolve(new Response(JSON.stringify({ results: [] }), { status: 200 }));
}

test("finds a DOI exactly through Crossref and reports its source", async () => {
  const report = await lookupBibliography([{
    number: 1,
    title: "Manual de investigación",
    authorPrefix: "García, M.",
    year: "2024",
    identifier: "doi:10.1234/demo",
  }], fetchFixture);

  assert.equal(report.status, "complete");
  assert.equal(report.checked, 1);
  assert.equal(report.results[0].status, "found");
  assert.equal(report.results[0].score, 1);
  assert.equal(report.results[0].match.source, "Crossref");
  assert.match(report.results[0].scholarUrl, /scholar\.google\.com\/scholar\?q=/);
});

test("does not claim a match when both catalogs return no records", async () => {
  const report = await lookupBibliography([{
    number: 2,
    title: "A source that should not exist in the fixture",
    authorPrefix: "Nobody, N.",
    year: "2024",
    identifier: null,
  }], fetchFixture);

  assert.equal(report.results[0].status, "not-found");
  assert.equal(report.results[0].match, null);
});

test("does not expose a weak candidate as a match", async () => {
  const weakFetch = async (url) => {
    if (url.includes("api.crossref.org")) {
      return new Response(JSON.stringify({ message: { items: [{
        title: ["Review of \"Array programming with NumPy\""],
        author: [{ given: "Ajit", family: "Singh" }],
        published: { "date-parts": [[2021]] },
      }] } }), { status: 200 });
    }
    return new Response(JSON.stringify({ results: [] }), { status: 200 });
  };
  const report = await lookupBibliography([{
    number: 3,
    title: "Array programming with NumPy",
    authorPrefix: "Harris, C.",
    year: "2020",
    identifier: null,
  }], weakFetch);

  assert.equal(report.results[0].status, "not-found");
  assert.equal(report.results[0].match, null);
});

test("limits external lookups and reports skipped entries", async () => {
  const entries = Array.from({ length: 13 }, (_, index) => ({
    number: index + 1,
    title: `Title ${index}`,
    authorPrefix: "Author, A.",
    year: "2024",
    identifier: null,
  }));
  const report = await lookupBibliography(entries, fetchFixture);

  assert.equal(report.results.length, 12);
  assert.equal(report.skipped, 1);
});
