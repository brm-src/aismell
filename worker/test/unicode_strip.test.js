import { test } from "node:test";
import assert from "node:assert/strict";
import { cleanText, inspectText } from "../src/unicode_strip.js";

// Cases mirror the Python reference (watermarks-remover text_unicode.py)
// and were verified against it: py output == js output for all inputs below.
const cases = [
  // zero width space
  ["hello\u200bworld", "helloworld", "zwj_family"],
  // homoglyph spaces
  ["a\u00a0b\u3000c", "a b c", "space"],
  // Cyrillic confusables (non-aggressive: kept)
  ["P\u0410R\u0418S", "P\u0410R\u0418S", null],
  // clean text
  ["normal text", "normal text", null],
  // bidi overrides (destructive: stripped by default)
  ["x\u202Ey\u202Cz", "xyz", "bidi"],
  // ZWJ between plain Latin letters: not load-bearing, stripped (verified vs Python)
  ["a\u200Db", "ab", "zwj_family"],
  // family emoji ZWJ chain (kept)
  ["\u{1F468}\u200D\u{1F469}\u200D\u{1F467}", "\u{1F468}\u200D\u{1F469}\u200D\u{1F467}", null],
  // heart + VS16 (kept)
  ["\u2764\uFE0F", "\u2764\uFE0F", null],
  // preservable bidi marks (kept in clean, reported in inspect)
  ["\u200E\u200F\u2066\u2067", "\u200E\u200F\u2066\u2067", "bidi"],
  // tag char (U+E0001, 5-digit escape) (stripped)
  ["t\u{E0001}x", "tx", "tag_chars"],
  // soft hyphen (stripped)
  ["a\u00ADb", "ab", "strip"],
  // normal é (kept)
  ["caf\u00E9", "caf\u00E9", null],
  // flag emoji (kept)
  ["\u{1F3F4}\u{E0067}\u{E0062}\u{E0073}\u{E0063}\u{E0074}\u{E007F}", "\u{1F3F4}\u{E0067}\u{E0062}\u{E0073}\u{E0063}\u{E0074}\u{E007F}", null],
  // orphan tag chars without flag base (stripped)
  ["\u{E0067}\u{E0062}\u{E0073}", "", "tag_chars"],
  // Persian ZWNJ orthographic (kept)
  ["\u0645\u06CC\u200C\u0631\u0648\u0645", "\u0645\u06CC\u200C\u0631\u0648\u0645", null],
  // Devanagari ZWJ (kept)
  ["\u0915\u094D\u200D\u0937", "\u0915\u094D\u200D\u0937", null],
  // Mongolian letter + FVS (kept)
  ["\u1820\u180B", "\u1820\u180B", null],
  // Khmer letter + inherent vowel (kept)
  ["\u1780\u17B4", "\u1780\u17B4", null],
  // Hangul jamo + filler (kept)
  ["\u1100\u115F", "\u1100\u115F", null],
  // valid bidi pair LRE...PDF (kept in clean)
  ["\u202Ahello\u202C", "\u202Ahello\u202C", "bidi"],
  // unpaired LRE (stripped)
  ["\u202Ahello", "hello", "bidi"],
  // emoji ZWJ chain ❤️‍🔥 (kept)
  ["\u2764\uFE0F\u200D\u{1F525}", "\u2764\uFE0F\u200D\u{1F525}", null],
  // vs16 after emoji base (kept)
  ["\u2696\uFE0F", "\u2696\uFE0F", null],
  // private use (stripped)
  ["\uE000x", "x", "private_use"],
];

test("cleanText matches the Python reference on verified cases", () => {
  for (const [input, expected, _kind] of cases) {
    assert.equal(cleanText(input).text, expected, `input ${JSON.stringify(input)}`);
  }
});

test("cleanText with nfkc normalizes fullwidth", () => {
  const result = cleanText("\uFF26\uFF49\uFF4C\uFF45", { nfkc: true });
  assert.equal(result.text, "File");
  assert.equal(result.stats.nfkc_changed, true);
});

test("inspectText reports the same kinds as the Python reference", () => {
  for (const [input, _expected, kind] of cases) {
    const report = inspectText(input);
    const kinds = report.hits.map((h) => h.kind);
    if (kind === null) {
      assert.equal(report.suspicious_total, 0, `input ${JSON.stringify(input)} should be clean`);
    } else {
      assert.ok(kinds.includes(kind), `input ${JSON.stringify(input)} should include ${kind}, got ${kinds}`);
    }
  }
});

test("aggressive homoglyph mode replaces Cyrillic lookalikes", () => {
  // И (U+0418) is NOT in the reference confusable map; use А (U+0410) and Р (U+0420).
  const result = cleanText("\u0410\u0420", { aggressiveHomoglyphs: true });
  assert.equal(result.text, "AP");
});
