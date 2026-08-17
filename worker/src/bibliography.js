const MAX_BIBLIOGRAPHY_CHARS = 12000;
const MAX_ANALYSIS_CHARS = 3000;
const YEAR_RE = /\b(?:1[5-9]\d{2}|20\d{2}|21\d{2})[a-z]?\b/iu;

function cleanEntry(value) {
  return value
    .replace(/^\s*(?:\[\d+\]|\d+[.)]|[-*])\s*/u, "")
    .replace(/\s+/gu, " ")
    .trim();
}

function startsEntry(line) {
  return /^\s*(?:\[\d+\]|\d+[.)]|[-*]\s+)/u.test(line)
    || YEAR_RE.test(line) && /^[A-ZÁÉÍÓÚÑÜÀ-ÖØ-Þ]/u.test(line.trim());
}

export function splitBibliographyDetailed(text) {
  const entries = [];
  let current = [];
  let blankSeparators = 0;
  let explicitMarkers = 0;
  const flush = () => {
    const value = cleanEntry(current.join(" "));
    if (value) entries.push(value);
    current = [];
  };

  for (const line of text.replace(/\r/gu, "").split("\n")) {
    if (!line.trim()) {
      if (current.length) blankSeparators += 1;
      flush();
      continue;
    }
    if (/^\s*(?:\[\d+\]|\d+[.)]|[-*]\s+)/u.test(line)) explicitMarkers += 1;
    if (current.length && startsEntry(line)) flush();
    current.push(line.trim());
  }
  flush();

  const separator = blankSeparators > 0
    ? "blank-line boundaries"
    : explicitMarkers > 0
      ? "explicit entry markers"
      : "author/year line boundaries";
  return { entries, separator, blankSeparators, explicitMarkers };
}

export function splitBibliography(text) {
  return splitBibliographyDetailed(text).entries;
}

function trimIdentifier(value) {
  return value.replace(/[).,;\]}]+$/u, "").replace(/[?#].*$/u, "").toLowerCase();
}

function identifiersFor(entry) {
  const identifiers = [];
  const doiMatches = entry.matchAll(/(?:https?:\/\/)?doi\.org\/(10\.\d{4,9}\/[\S]+)|\bdoi:\s*(10\.\d{4,9}\/[\S]+)/giu);
  for (const match of doiMatches) identifiers.push(`doi:${trimIdentifier(match[1] || match[2])}`);
  if (identifiers.length === 0) {
    for (const match of entry.matchAll(/https?:\/\/[^\s)>]+/giu)) identifiers.push(`url:${trimIdentifier(match[0])}`);
  }
  return [...new Set(identifiers)];
}

function sourceId(entry) {
  return identifiersFor(entry)[0] || "";
}

function beforeYear(entry) {
  const match = YEAR_RE.exec(entry);
  return match ? entry.slice(0, match.index).replace(/^\s*(?:\[\d+\]|\d+[.)])\s*/u, "").trim() : "";
}

function titleCandidate(entry, yearMatch) {
  if (!yearMatch) return "";
  const afterYear = entry.slice(yearMatch.index + yearMatch[0].length)
    .replace(/^\s*[a-z]?\s*[.():,;-]+\s*/iu, "");
  const withoutIdentifier = afterYear.split(/https?:\/\/|\bdoi:\s*/iu)[0].trim();
  return withoutIdentifier.split(/(?<=[.!?])\s+/u)[0]
    .replace(/[.]+$/u, "")
    .trim();
}

function normalizeKey(value) {
  return String(value || "").toLowerCase().normalize("NFKD")
    .replace(/[\u0300-\u036f]/gu, "")
    .replace(/[^\p{L}\p{N}]+/gu, " ")
    .trim();
}

function looksLikeAuthor(entry, yearMatch) {
  const prefix = beforeYear(entry);
  if (!prefix || /^(?:n\.?\s*d\.?|s\.?\s*f\.?)$/iu.test(prefix)) return false;
  if (/,|\bet al\.?\b|\b(?:and|y)\b/iu.test(prefix)) return true;
  const words = prefix.split(/\s+/u).filter(Boolean);
  return words.length >= 2 && words.length <= 12;
}

function inspectEntry(entry, index) {
  const yearMatch = YEAR_RE.exec(entry);
  const year = yearMatch?.[0] || "";
  const title = titleCandidate(entry, yearMatch);
  const identifiers = identifiersFor(entry);
  const hasUrl = /https?:\/\//iu.test(entry);
  const hasDoiToken = /\bdoi\b|doi\.org/iu.test(entry);
  const pages = /\b\d{1,5}\s*[-–]\s*\d{1,5}\b/u.test(entry);
  const volumeIssue = /\b\d+\s*\(\s*\d+\s*\)/u.test(entry);
  const author = looksLikeAuthor(entry, yearMatch);
  return {
    number: index + 1,
    author,
    authorPrefix: beforeYear(entry),
    year: year || null,
    title,
    titleKey: normalizeKey(title),
    identifiers,
    identifier: identifiers[0] || null,
    hasUrl,
    hasDoiToken,
    pages,
    volumeIssue,
    yearStyle: yearMatch && /\(\s*\d{4}[a-z]?\s*\)/iu.test(entry) ? "parenthetical" : year ? "bare" : "unknown",
    preview: entry.length > 110 ? `${entry.slice(0, 107)}…` : entry,
  };
}

function pushFinding(findings, code, severity, message, entry) {
  findings.push({ code, severity, message, entry });
}

export function checkBibliography(text, analysis = {}) {
  const source = String(text || "").trim();
  if (!source) throw new Error("empty");
  if (source.length > MAX_BIBLIOGRAPHY_CHARS) throw new Error("too-long");

  const parsed = splitBibliographyDetailed(source);
  const entries = parsed.entries;
  const inspected = entries.map(inspectEntry);
  const findings = [];
  const identifiers = new Map();
  const normalized = new Map();
  const titles = new Map();
  let parentheticalYears = 0;
  let bareYears = 0;
  let malformedDoi = 0;

  inspected.forEach((item, index) => {
    if (!item.year) pushFinding(findings, "missing-year", "high", "No encontré un año de publicación claro.", item.number);
    if (!item.author) pushFinding(findings, "missing-author", "high", "No encontré un autor reconocible antes del año.", item.number);
    if (item.titleKey.split(/\s+/u).filter(Boolean).length < 2) {
      pushFinding(findings, "missing-title", "medium", "No encontré un título identificable después del año.", item.number);
    }
    if (item.yearStyle === "parenthetical") parentheticalYears += 1;
    if (item.yearStyle === "bare") bareYears += 1;
    if (item.hasDoiToken && !item.identifiers.some((id) => id.startsWith("doi:"))) malformedDoi += 1;

    for (const id of item.identifiers) {
      if (identifiers.has(id)) {
        pushFinding(findings, "duplicate-source", "high", `Comparte DOI o URL con la entrada ${identifiers.get(id)}.`, item.number);
      } else {
        identifiers.set(id, item.number);
      }
    }

    const key = normalizeKey(entries[index]);
    if (key.length > 24) {
      if (normalized.has(key)) {
        pushFinding(findings, "duplicate-entry", "high", `Parece duplicar la entrada ${normalized.get(key)}.`, item.number);
      } else {
        normalized.set(key, item.number);
      }
    }
    if (item.titleKey.length > 12) {
      if (titles.has(item.titleKey)) {
        pushFinding(findings, "duplicate-title", "medium", `Comparte título normalizado con la entrada ${titles.get(item.titleKey)}.`, item.number);
      } else {
        titles.set(item.titleKey, item.number);
      }
    }
  });

  if (parentheticalYears && bareYears) {
    pushFinding(findings, "mixed-year-style", "medium", "La lista mezcla años entre paréntesis con años sueltos; elige un estilo.", null);
  }
  if (malformedDoi) {
    pushFinding(findings, "malformed-doi", "medium", `Encontré ${malformedDoi} mención${malformedDoi === 1 ? "" : "es"} de DOI sin un identificador DOI completo.`, null);
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
  const covered = {
    authors: inspected.filter((item) => item.author).length,
    years: inspected.filter((item) => item.year).length,
    titles: inspected.filter((item) => item.titleKey.length > 12).length,
    identifiers: inspected.filter((item) => item.identifiers.length > 0).length,
    pagesOrVolume: inspected.filter((item) => item.pages || item.volumeIssue).length,
  };

  return {
    score,
    status,
    entryCount: entries.length,
    entries: inspected,
    findings: findings.slice(0, 40),
    counts,
    method: {
      source: "pasted-text",
      parser: "line scanner with blank-line, explicit-marker, and author/year boundaries",
      separator: parsed.separator,
      fields: ["author prefix", "publication year", "title span", "DOI/URL", "pages or volume(issue)", "date style"],
      duplicateIndexes: ["canonical DOI", "normalized URL", "normalized full entry", "normalized title"],
      covered,
      aismell: {
        endpoint: "/analyze through the aismell Worker service binding",
        characters: Math.min(source.length, MAX_ANALYSIS_CHARS),
        truncated: source.length > MAX_ANALYSIS_CHARS,
      },
    },
    analysis: {
      language: analysis.language || "unknown",
      findingCount: aismellFindings.length,
      truncated: source.length > MAX_ANALYSIS_CHARS,
    },
  };
}

export { MAX_BIBLIOGRAPHY_CHARS, MAX_ANALYSIS_CHARS };
