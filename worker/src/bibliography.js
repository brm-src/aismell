const MAX_BIBLIOGRAPHY_CHARS = 12000;
const MAX_ANALYSIS_CHARS = 3000;

function cleanEntry(value) {
  return value
    .replace(/^\s*(?:\[\d+\]|\d+[.)]|[-*])\s*/u, "")
    .replace(/\s+/gu, " ")
    .trim();
}

function startsEntry(line) {
  return /^\s*(?:\[\d+\]|\d+[.)]|[-*]\s+)/u.test(line)
    || /\b(?:19|20)\d{2}[a-z]?\b/u.test(line) && /^[A-ZÁÉÍÓÚÑÜÀ-ÖØ-Þ]/u.test(line.trim());
}

export function splitBibliography(text) {
  const entries = [];
  let current = [];
  const flush = () => {
    const value = cleanEntry(current.join(" "));
    if (value) entries.push(value);
    current = [];
  };

  for (const line of text.replace(/\r/gu, "").split("\n")) {
    if (!line.trim()) {
      flush();
      continue;
    }
    if (current.length && startsEntry(line)) flush();
    current.push(line.trim());
  }
  flush();
  return entries;
}

function sourceId(entry) {
  const doi = entry.match(/(?:https?:\/\/)?doi\.org\/(10\.\d{4,9}\/[\S]+)|\bdoi:\s*(10\.\d{4,9}\/[\S]+)/iu);
  if (doi) return `doi:${doi[1] || doi[2]}`.replace(/[).,;]+$/u, "").toLowerCase();
  const url = entry.match(/https?:\/\/[^\s)>]+/iu);
  return url ? `url:${url[0].replace(/[).,;]+$/u, "").toLowerCase()}` : "";
}

function looksLikeAuthor(entry) {
  const withoutMarker = entry.replace(/^\s*(?:\[\d+\]|\d+[.)])\s*/u, "");
  return /^[A-ZÁÉÍÓÚÑÜÀ-ÖØ-Þ][^.!?]{0,90},/u.test(withoutMarker)
    || /\b(?:et al\.|and|y)\b/iu.test(withoutMarker.split(/\b(?:19|20)\d{2}\b/u)[0] || "");
}

function pushFinding(findings, code, severity, message, entry) {
  findings.push({ code, severity, message, entry });
}

export function checkBibliography(text, analysis = {}) {
  const source = String(text || "").trim();
  if (!source) throw new Error("empty");
  if (source.length > MAX_BIBLIOGRAPHY_CHARS) throw new Error("too-long");

  const entries = splitBibliography(source);
  const findings = [];
  const identifiers = new Map();
  const normalized = new Map();
  let parentheticalYears = 0;
  let bareYears = 0;

  entries.forEach((entry, index) => {
    const year = entry.match(/\b(?:19|20)\d{2}[a-z]?\b/iu)?.[0] || "";
    if (!year) pushFinding(findings, "missing-year", "high", "No encontré un año de publicación claro.", index + 1);
    if (!looksLikeAuthor(entry)) pushFinding(findings, "missing-author", "high", "No encontré un autor reconocible al comienzo.", index + 1);

    if (/\(\s*(?:19|20)\d{2}[a-z]?\s*\)/u.test(entry)) parentheticalYears += 1;
    if (/(?:^|[.,\s])(?:19|20)\d{2}[a-z]?(?:[.,;)]|$)/u.test(entry) && !/\(\s*(?:19|20)\d{2}/u.test(entry)) bareYears += 1;

    const id = sourceId(entry);
    if (id) {
      if (identifiers.has(id)) {
        pushFinding(findings, "duplicate-source", "high", `Comparte DOI o URL con la entrada ${identifiers.get(id)}.`, index + 1);
      } else {
        identifiers.set(id, index + 1);
      }
    }

    const key = entry.toLowerCase().replace(/[^\p{L}\p{N}]+/gu, " ").trim();
    if (key.length > 24) {
      if (normalized.has(key)) {
        pushFinding(findings, "duplicate-entry", "high", `Parece duplicar la entrada ${normalized.get(key)}.`, index + 1);
      } else {
        normalized.set(key, index + 1);
      }
    }
  });

  if (parentheticalYears && bareYears) {
    pushFinding(findings, "mixed-year-style", "medium", "La lista mezcla años entre paréntesis con años sueltos; elige un estilo.", null);
  }

  const aismellFindings = Array.isArray(analysis.findings) ? analysis.findings : [];
  for (const finding of aismellFindings.slice(0, 8)) {
    const findingId = typeof finding === "string" ? finding : finding?.id;
    if (typeof findingId !== "string") continue;
    const matched = typeof finding?.matched === "string" && finding.matched ? `: “${finding.matched}”` : "";
    pushFinding(findings, "aismell-signal", "medium", `aismell detectó una señal de redacción formulaica${matched}.`, null);
  }

  const counts = { high: 0, medium: 0, low: 0 };
  for (const finding of findings) counts[finding.severity] = (counts[finding.severity] || 0) + 1;
  const score = Math.max(0, 100 - counts.high * 18 - counts.medium * 8 - counts.low * 3);
  const status = counts.high ? "attention" : counts.medium ? "review" : "ready";

  return {
    score,
    status,
    entryCount: entries.length,
    entries: entries.map((entry, index) => ({
      number: index + 1,
      preview: entry.length > 110 ? `${entry.slice(0, 107)}…` : entry,
      year: entry.match(/\b(?:19|20)\d{2}[a-z]?\b/iu)?.[0] || null,
      identifier: sourceId(entry) || null,
    })),
    findings: findings.slice(0, 40),
    counts,
    analysis: {
      language: analysis.language || "unknown",
      findingCount: aismellFindings.length,
      truncated: source.length > MAX_ANALYSIS_CHARS,
    },
  };
}

export { MAX_BIBLIOGRAPHY_CHARS, MAX_ANALYSIS_CHARS };
