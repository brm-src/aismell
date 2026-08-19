// Layer A: invisible Unicode / homoglyph space detection and cleaning.
// Faithful port of guillaumemeyer/watermarks-remover service/scripts/text_unicode.py
// (MIT). Iterates by code point; JS property escapes stand in for unicodedata.

const STRIP_CODEPOINTS = new Set([
  0x00ad, 0x034f, 0x061c, 0x115f, 0x1160, 0x17b4, 0x17b5,
  0x180b, 0x180c, 0x180d, 0x180e,
  0x200b, 0x200c, 0x200d, 0x200e, 0x200f,
  0x202a, 0x202b, 0x202c, 0x202d, 0x202e,
  0x2060, 0x2061, 0x2062, 0x2063, 0x2064,
  0x2066, 0x2067, 0x2068, 0x2069,
  0x206a, 0x206b, 0x206c, 0x206d, 0x206e, 0x206f,
  0xfeff,
  0xfe00, 0xfe01, 0xfe02, 0xfe03, 0xfe04, 0xfe05, 0xfe06, 0xfe07,
  0xfe08, 0xfe09, 0xfe0a, 0xfe0b, 0xfe0c, 0xfe0d, 0xfe0e, 0xfe0f,
  0xfff9, 0xfffa, 0xfffb,
]);

const SPACE_HOMOGLYPHS = new Map([
  [0x00a0, " "], [0x1680, " "], [0x2000, " "], [0x2001, " "], [0x2002, " "],
  [0x2003, " "], [0x2004, " "], [0x2005, " "], [0x2006, " "], [0x2007, " "],
  [0x2008, " "], [0x2009, " "], [0x200a, " "], [0x202f, " "], [0x205f, " "],
  [0x3000, " "],
]);

const LATIN_CONFUSABLES = new Map([
  [0x0410, "A"], [0x0412, "B"], [0x0415, "E"], [0x041a, "K"], [0x041c, "M"],
  [0x041d, "H"], [0x041e, "O"], [0x0420, "P"], [0x0421, "C"], [0x0422, "T"],
  [0x0425, "X"], [0x0430, "a"], [0x0435, "e"], [0x043e, "o"], [0x0440, "p"],
  [0x0441, "c"], [0x0443, "y"], [0x0445, "x"], [0x0456, "i"],
  [0xff21, "A"], [0xff22, "B"], [0xff23, "C"], [0xff24, "D"], [0xff25, "E"],
  [0xff26, "F"], [0xff27, "G"], [0xff28, "H"], [0xff29, "I"], [0xff2a, "J"],
  [0xff2b, "K"], [0xff2c, "L"], [0xff2d, "M"], [0xff2e, "N"], [0xff2f, "O"],
  [0xff30, "P"], [0xff31, "Q"], [0xff32, "R"], [0xff33, "S"], [0xff34, "T"],
  [0xff35, "U"], [0xff36, "V"], [0xff37, "W"], [0xff38, "X"], [0xff39, "Y"],
  [0xff3a, "Z"], [0xff41, "a"], [0xff42, "b"], [0xff43, "c"], [0xff44, "d"],
  [0xff45, "e"], [0xff46, "f"], [0xff47, "g"], [0xff48, "h"], [0xff49, "i"],
  [0xff4a, "j"], [0xff4b, "k"], [0xff4c, "l"], [0xff4d, "m"], [0xff4e, "n"],
  [0xff4f, "o"], [0xff50, "p"], [0xff51, "q"], [0xff52, "r"], [0xff53, "s"],
  [0xff54, "t"], [0xff55, "u"], [0xff56, "v"], [0xff57, "w"], [0xff58, "x"],
  [0xff59, "y"], [0xff5a, "z"],
]);

const VS_SUPPLEMENT = [0xe0100, 0xe01f0]; // range start/end (exclusive end)
const BIDI_CPS = new Set([0x061c, 0x200e, 0x200f, 0x202a, 0x202b, 0x202c, 0x202d, 0x202e, 0x2066, 0x2067, 0x2068, 0x2069]);
const PRESERVABLE_BIDI_CPS = new Set([0x061c, 0x200e, 0x200f, 0x2066, 0x2067, 0x2068, 0x2069]);
const ZW_FAMILY = new Set([0x200b, 0x200c, 0x200d, 0x2060, 0xfeff, 0x180e]);
const EMOJI_GLUE_CODEPOINTS = new Set([0x200d, 0xfe0e, 0xfe0f]);
const SCRIPT_JOINERS = new Set([0x200c, 0x200d]);
const TAG_RANGE = [0xe0020, 0xe0080];
const ORTHOGRAPHIC_CF = new Set([0x0600, 0x0601, 0x0602, 0x0603, 0x0604, 0x0605, 0x06dd, 0x070f, 0x08e2, 0x110bd, 0x110cd]);
const MONGOLIAN_FVS = new Set([0x180b, 0x180c, 0x180d]);
const KHMER_VOWELS = new Set([0x17b4, 0x17b5]);
const HANGUL_FILLERS = new Set([0x115f, 0x1160]);
const SCRIPT_GLUE = new Set([...MONGOLIAN_FVS, ...KHMER_VOWELS, ...HANGUL_FILLERS]);

function inRange(cp, [start, end]) { return cp >= start && cp < end; }

function isPrivateUse(cp) {
  return (0xe000 <= cp && cp <= 0xf8ff) || (0xf0000 <= cp && cp <= 0xffffd) || (0x100000 <= cp && cp <= 0x10fffd);
}

function isStripCp(cp) {
  if (STRIP_CODEPOINTS.has(cp)) return true;
  if (inRange(cp, VS_SUPPLEMENT)) return true;
  if (0xe0001 <= cp && cp <= 0xe007f) return true;
  return isPrivateUse(cp);
}

function stripKind(cp) {
  if (0xe0001 <= cp && cp <= 0xe007f) return "tag_chars";
  if (inRange(cp, VS_SUPPLEMENT) || (0xfe00 <= cp && cp <= 0xfe0f) || (0x180b <= cp && cp <= 0x180d)) return "variation_selector";
  if (BIDI_CPS.has(cp)) return "bidi";
  if (ZW_FAMILY.has(cp)) return "zwj_family";
  if (isPrivateUse(cp)) return "private_use";
  return "strip";
}

function isEmojiGlue(cp) { return EMOJI_GLUE_CODEPOINTS.has(cp); }

function isEmojiBase(cp) {
  if (0x1f000 <= cp && cp <= 0x1faff) return true;
  if (0x2190 <= cp && cp <= 0x25ff) return true;
  if (0x2600 <= cp && cp <= 0x27bf) return true;
  if (0x2b00 <= cp && cp <= 0x2bff) return true;
  if (cp === 0x00a9 || cp === 0x00ae || cp === 0x2122 || cp === 0x3030 || cp === 0x303d || cp === 0x3297 || cp === 0x3299) return true;
  return cp === 0x0023 || cp === 0x002a || (0x0030 <= cp && cp <= 0x0039);
}

// ---- Unicode category helpers (JS property escapes) ----
const RE_LETTER = /^\p{L}$/u;
const RE_LETTER_OR_MARK = /^[\p{L}\p{M}]$/u;
const RE_CF = /^\p{Cf}$/u;

function isLetter(cp) { return RE_LETTER.test(String.fromCodePoint(cp)); }
function isLetterOrMark(cp) { return RE_LETTER_OR_MARK.test(String.fromCodePoint(cp)); }
function isCf(cp) { return RE_CF.test(String.fromCodePoint(cp)); }

function joiningScript(cp) {
  for (const [start, end, name] of [[0x0600, 0x08ff, "arabic"], [0x0900, 0x0dff, "indic"], [0x0f00, 0x109f, "south-asian"], [0x1780, 0x17ff, "khmer"], [0x1800, 0x18af, "mongolian"]]) {
    if (start <= cp && cp <= end && isLetterOrMark(cp)) return name;
  }
  return null;
}

function isCjkIdeograph(cp) {
  return (0x3400 <= cp && cp <= 0x4dbf) || (0x4e00 <= cp && cp <= 0x9fff) || (0xf900 <= cp && cp <= 0xfaff) || (0x20000 <= cp && cp <= 0x323af);
}
function isMongolianBase(cp) { return 0x1800 <= cp && cp <= 0x18af; }
function isVariationSelector(cp) { return inRange(cp, VS_SUPPLEMENT) || (0xfe00 <= cp && cp <= 0xfe0f) || (0x180b <= cp && cp <= 0x180d); }
function isMongolianLetter(cp) { return 0x1800 <= cp && cp <= 0x18af && isLetter(cp); }
function isKhmerLetter(cp) { return 0x1780 <= cp && cp <= 0x17ff && isLetter(cp); }
function isHangulJamo(cp) {
  return (0x1100 <= cp && cp <= 0x11ff) || (0xa960 <= cp && cp <= 0xa97c) || (0xd7b0 <= cp && cp <= 0xd7c6);
}

function validFlagTagIndices(cps) {
  const valid = new Set();
  let i = 0;
  while (i < cps.length) {
    if (cps[i] !== 0x1f3f4) { i += 1; continue; }
    let j = i + 1;
    while (j < cps.length && 0xe0020 <= cps[j] && cps[j] <= 0xe007e) j += 1;
    if (j > i + 1 && j < cps.length && cps[j] === 0xe007f) {
      for (let k = i + 1; k <= j; k++) valid.add(k);
      i = j + 1;
    } else {
      i += 1;
    }
  }
  return valid;
}

function validBidiEmbeddingIndices(cps) {
  const valid = new Set();
  const stack = [];
  for (let index = 0; index < cps.length; index++) {
    const cp = cps[index];
    if (cp === 0x202a || cp === 0x202b || cp === 0x202d || cp === 0x202e) {
      stack.push([cp, index]);
    } else if (cp === 0x202c) {
      if (!stack.length) continue;
      const [opener, openerIndex] = stack.pop();
      if (opener === 0x202a || opener === 0x202b) {
        valid.add(openerIndex);
        valid.add(index);
      }
    }
  }
  return valid;
}

function isGlue(cp) {
  return isEmojiGlue(cp) || isVariationSelector(cp) || SCRIPT_JOINERS.has(cp) || inRange(cp, TAG_RANGE) || SCRIPT_GLUE.has(cp);
}

function decide(ch, prevKept, prevInput, nextInput, opts) {
  const cp = ch.codePointAt(0);
  const { validFlagTag, validBidiEmbedding, normalizeSpaces, treatConfusables, stripEmojiGlue, stripBidi } = opts;
  if (validBidiEmbedding && !stripBidi) return ["keep", ch, null];
  if (PRESERVABLE_BIDI_CPS.has(cp) && !stripBidi) return ["keep", ch, null];
  if (prevInput !== null && !stripEmojiGlue) {
    const prevCp = prevInput.codePointAt(0);
    if (inRange(cp, VS_SUPPLEMENT) && isCjkIdeograph(prevCp)) return ["keep", ch, null];
    if (0x180b <= cp && cp <= 0x180d && isMongolianBase(prevCp)) return ["keep", ch, null];
    if (0xfe00 <= cp && cp <= 0xfe0d && isCjkIdeograph(prevCp)) return ["keep", ch, null];
  }
  if (isEmojiGlue(cp) && !stripEmojiGlue) {
    if ((cp === 0xfe0e || cp === 0xfe0f) && prevInput !== null && isEmojiBase(prevInput.codePointAt(0))) return ["keep", ch, null];
    if (cp === 0x200d && prevKept !== null && nextInput !== null && isEmojiBase(prevKept.codePointAt(0)) && isEmojiBase(nextInput.codePointAt(0))) return ["keep", ch, null];
  }
  if (!stripEmojiGlue) {
    if (SCRIPT_JOINERS.has(cp) && prevInput !== null && nextInput !== null) {
      const prevScript = joiningScript(prevInput.codePointAt(0));
      const nextScript = joiningScript(nextInput.codePointAt(0));
      if (prevScript !== null && prevScript === nextScript) return ["keep", ch, null];
    }
    if (inRange(cp, TAG_RANGE) && validFlagTag) return ["keep", ch, null];
    if (MONGOLIAN_FVS.has(cp) && prevKept !== null && isMongolianLetter(prevKept.codePointAt(0))) return ["keep", ch, null];
    if (KHMER_VOWELS.has(cp) && prevKept !== null && isKhmerLetter(prevKept.codePointAt(0))) return ["keep", ch, null];
    if (HANGUL_FILLERS.has(cp) && prevKept !== null && isHangulJamo(prevKept.codePointAt(0))) return ["keep", ch, null];
    if (ORTHOGRAPHIC_CF.has(cp)) return ["keep", ch, null];
  }
  if (isStripCp(cp)) return ["strip", "", stripKind(cp)];
  if (normalizeSpaces && SPACE_HOMOGLYPHS.has(cp)) return ["replace", SPACE_HOMOGLYPHS.get(cp), "space"];
  if (treatConfusables && LATIN_CONFUSABLES.has(cp)) return ["replace", LATIN_CONFUSABLES.get(cp), "confusable"];
  if (isCf(cp) && !SPACE_HOMOGLYPHS.has(cp)) return ["strip", "", "other_cf"];
  return ["keep", ch, null];
}

function charLabel(ch) {
  const cp = ch.codePointAt(0);
  const name = (function codePointName(cp) {
    try {
      // No unicodedata in JS; best effort from a small table is overkill.
      return "";
    } catch { return ""; }
  })(cp);
  return `U+${cp.toString(16).toUpperCase().padStart(4, "0")}${name ? " " + name : ""} (${cfCategory(cp)})`;
}

function cfCategory(cp) {
  const ch = String.fromCodePoint(cp);
  if (isCf(cp)) return "Cf";
  if (isLetter(cp)) return "L";
  if (/^\p{M}$/u.test(ch)) return "M";
  if (/^\p{Z}$/u.test(ch)) return "Z";
  if (/^\p{P}$/u.test(ch)) return "P";
  if (/^\p{S}$/u.test(ch)) return "S";
  if (/^\p{N}$/u.test(ch)) return "N";
  return "Cn";
}

function hitConfidence(kind) { return kind === "space" ? "informational" : "probable"; }

function inspectText(text, opts = {}) {
  const cps = Array.from(text, (ch) => ch.codePointAt(0));
  const aggressive = !!opts.aggressive;
  const stripEmojiGlue = !!opts.stripEmojiGlue;
  const buckets = new Map();
  let prevKept = null;
  const flagTags = validFlagTagIndices(cps);
  const bidiEmb = validBidiEmbeddingIndices(cps);
  for (let i = 0; i < cps.length; i++) {
    const ch = String.fromCodePoint(cps[i]);
    const [action, outChar, kind] = decide(ch, prevKept, i > 0 ? String.fromCodePoint(cps[i - 1]) : null, i + 1 < cps.length ? String.fromCodePoint(cps[i + 1]) : null, {
      validFlagTag: flagTags.has(i),
      validBidiEmbedding: bidiEmb.has(i),
      normalizeSpaces: true,
      treatConfusables: aggressive,
      stripEmojiGlue,
      stripBidi: true,
    });
    if (kind === null) {
      if (!isGlue(cps[i])) prevKept = outChar;
      continue;
    }
    const key = cps[i] + "|" + kind;
    if (!buckets.has(key)) buckets.set(key, { cp: cps[i], kind, offsets: [] });
    buckets.get(key).offsets.push(i);
    if (action === "replace") prevKept = outChar;
  }
  const hits = [...buckets.values()].sort((a, b) => b.offsets.length - a.offsets.length || a.cp - b.cp);
  const total = hits.reduce((s, h) => s + h.offsets.length, 0);
  const charHits = hits.map((h) => ({
    codepoint: `U+${h.cp.toString(16).toUpperCase().padStart(4, "0")}`,
    char: String.fromCodePoint(h.cp),
    label: charLabel(String.fromCodePoint(h.cp)),
    count: h.offsets.length,
    kind: h.kind,
    confidence: hitConfidence(h.kind),
    sample_offsets: h.offsets.slice(0, 10),
  }));
  return { length: text.length, suspicious_total: total, hits: charHits };
}

function cleanText(text, opts = {}) {
  const cps = Array.from(text, (ch) => ch.codePointAt(0));
  const nfkc = !!opts.nfkc;
  const aggressiveHomoglyphs = !!opts.aggressiveHomoglyphs;
  const normalizeSpaces = opts.normalizeSpaces !== false;
  const stripEmojiGlue = !!opts.stripEmojiGlue;
  const stripBidi = !!opts.stripBidi;
  const removed = new Map();
  const replaced = new Map();
  const outChars = [];
  let prevKept = null;
  const flagTags = validFlagTagIndices(cps);
  const bidiEmb = validBidiEmbeddingIndices(cps);
  for (let i = 0; i < cps.length; i++) {
    const ch = String.fromCodePoint(cps[i]);
    const [action, outChar, _kind] = decide(ch, prevKept, i > 0 ? String.fromCodePoint(cps[i - 1]) : null, i + 1 < cps.length ? String.fromCodePoint(cps[i + 1]) : null, {
      validFlagTag: flagTags.has(i),
      validBidiEmbedding: bidiEmb.has(i),
      normalizeSpaces,
      treatConfusables: aggressiveHomoglyphs,
      stripEmojiGlue,
      stripBidi,
    });
    if (action === "keep") {
      outChars.push(outChar);
      if (!isGlue(cps[i])) prevKept = outChar;
    } else if (action === "replace") {
      outChars.push(outChar);
      replaced.set(charLabel(ch), (replaced.get(charLabel(ch)) || 0) + 1);
      prevKept = outChar;
    } else {
      removed.set(charLabel(ch), (removed.get(charLabel(ch)) || 0) + 1);
    }
  }
  let result = outChars.join("");
  let nfkcChanged = false;
  if (nfkc) {
    const before = result;
    result = result.normalize("NFKC");
    nfkcChanged = result !== before;
    if (nfkcChanged) {
      // Approximate changed span count: differing prefix/suffix trim.
      let start = 0;
      while (start < before.length && start < result.length && before[start] === result[start]) start++;
      let end = 0;
      while (end < before.length - start && end < result.length - start && before[before.length - 1 - end] === result[result.length - 1 - end]) end++;
      const changed = Math.max(before.length, result.length) - start - end;
      replaced.set("NFKC_normalize", (replaced.get("NFKC_normalize") || 0) + (changed || 1));
    }
  }
  return {
    text: result,
    stats: {
      input_length: text.length,
      output_length: result.length,
      removed: Object.fromEntries(removed),
      replaced: Object.fromEntries(replaced),
      removed_count: [...removed.values()].reduce((a, b) => a + b, 0),
      replaced_count: [...replaced.values()].reduce((a, b) => a + b, 0),
      nfkc_changed: nfkcChanged,
    },
  };
}

export { inspectText, cleanText, decide, isGlue };
