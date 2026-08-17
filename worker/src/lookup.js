const LOOKUP_LIMIT = 12;
const REQUEST_TIMEOUT_MS = 8000;
const USER_AGENT = "ai-bibliography-check/1.0 (https://github.com/brm-src/ai-bibliography-check)";

function normalize(value) {
  return String(value || "").toLowerCase().normalize("NFKD")
    .replace(/[\u0300-\u036f]/gu, "")
    .replace(/[^\p{L}\p{N}]+/gu, " ")
    .trim();
}

function tokens(value) {
  return new Set(normalize(value).split(/\s+/u).filter((token) => token.length > 2));
}

function overlap(left, right) {
  if (!left.size || !right.size) return 0;
  let common = 0;
  for (const token of left) if (right.has(token)) common += 1;
  return common / Math.max(left.size, right.size);
}

function canonicalDoi(value) {
  return normalize(value).replace(/^doi\s*:??\s*/u, "").replace(/^https?\s+doi\s+org\s*/u, "").replace(/\s+/gu, "");
}

function yearFromCrossref(item) {
  return item?.published?.["date-parts"]?.[0]?.[0]
    || item?.issued?.["date-parts"]?.[0]?.[0]
    || null;
}

function crossrefRecord(item) {
  return {
    title: item?.title?.[0] || "",
    author: item?.author?.slice(0, 2).map((author) => [author.given, author.family].filter(Boolean).join(" ")).join("; ") || "",
    year: yearFromCrossref(item),
    doi: item?.DOI || "",
    url: item?.URL || "",
  };
}

function openAlexRecord(item) {
  return {
    title: item?.title || "",
    author: item?.authorships?.slice(0, 2).map((author) => author?.author?.display_name || "").filter(Boolean).join("; "),
    year: item?.publication_year || null,
    doi: item?.doi || "",
    url: item?.primary_location?.landing_page_url || item?.id || "",
  };
}

async function fetchJson(url, fetchImpl) {
  const response = await fetchImpl(url, {
    headers: {
      Accept: "application/json",
      "User-Agent": USER_AGENT,
    },
    signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

function queryFor(entry) {
  if (entry.identifier?.startsWith("doi:")) return entry.identifier.slice(4);
  return [entry.title, entry.authorPrefix].filter(Boolean).join(" ").slice(0, 500);
}

function scoreCandidate(entry, candidate) {
  if (entry.identifier?.startsWith("doi:") && candidate.doi
      && canonicalDoi(entry.identifier.slice(4)) === canonicalDoi(candidate.doi)) return 1;
  const titleScore = overlap(tokens(entry.title), tokens(candidate.title));
  const authorScore = overlap(tokens(entry.authorPrefix), tokens(candidate.author));
  const yearScore = entry.year && candidate.year && String(entry.year).slice(0, 4) === String(candidate.year) ? 1 : 0;
  return titleScore * 0.72 + authorScore * 0.18 + yearScore * 0.10;
}

function classify(score, hasCandidates) {
  if (!hasCandidates) return "not-found";
  if (score >= 0.72) return "found";
  if (score >= 0.45) return "possible";
  return "not-found";
}

async function lookupOne(entry, fetchImpl) {
  const query = queryFor(entry);
  if (!query) return { entry: entry.number, query: "", status: "insufficient-data", sources: [] };
  const doiQuery = entry.identifier?.startsWith("doi:");
  const crossrefUrl = doiQuery
    ? `https://api.crossref.org/works/${encodeURIComponent(query)}`
    : `https://api.crossref.org/works?query.bibliographic=${encodeURIComponent(query)}&rows=3`;
  const openAlexUrl = doiQuery
    ? `https://api.openalex.org/works?filter=doi:${encodeURIComponent(`https://doi.org/${query}`)}&per-page=3`
    : `https://api.openalex.org/works?search=${encodeURIComponent(query)}&per-page=3`;

  const responses = await Promise.allSettled([
    fetchJson(crossrefUrl, fetchImpl),
    fetchJson(openAlexUrl, fetchImpl),
  ]);
  const sourceResults = [];
  const sourceStatuses = [];
  responses.forEach((result, index) => {
    const source = index === 0 ? "Crossref" : "OpenAlex";
    if (result.status === "rejected") {
      sourceStatuses.push({ source, status: "unavailable" });
      return;
    }
    const rawItems = index === 0
      ? (doiQuery ? [result.value?.message] : result.value?.message?.items || [])
      : (doiQuery ? result.value?.results || [] : result.value?.results || []);
    const items = rawItems.filter(Boolean).map(index === 0 ? crossrefRecord : openAlexRecord);
    const ranked = items.map((candidate) => ({ ...candidate, score: scoreCandidate(entry, candidate) }))
      .sort((a, b) => b.score - a.score);
    sourceStatuses.push({ source, status: ranked.length ? "responded" : "empty" });
    if (ranked[0]) sourceResults.push({ source, ...ranked[0] });
  });

  sourceResults.sort((a, b) => b.score - a.score);
  const best = sourceResults[0] || null;
  const unavailable = sourceStatuses.every((source) => source.status === "unavailable");
  return {
    entry: entry.number,
    query,
    status: unavailable ? "unavailable" : classify(best?.score || 0, sourceResults.length > 0),
    score: best ? Number(best.score.toFixed(2)) : 0,
    sources: sourceStatuses,
    match: best ? {
      source: best.source,
      title: best.title,
      author: best.author,
      year: best.year,
      doi: best.doi || null,
      url: best.url || null,
    } : null,
  };
}

export async function lookupBibliography(entries, fetchImpl = globalThis.fetch) {
  const selected = Array.isArray(entries) ? entries.slice(0, LOOKUP_LIMIT) : [];
  const results = await Promise.all(selected.map(async (entry) => {
    try {
      return await lookupOne(entry, fetchImpl);
    } catch {
      return {
        entry: entry.number,
        query: queryFor(entry),
        status: "unavailable",
        score: 0,
        sources: [{ source: "Crossref", status: "unavailable" }, { source: "OpenAlex", status: "unavailable" }],
        match: null,
      };
    }
  }));
  const checked = results.filter((result) => ["found", "possible", "not-found"].includes(result.status)).length;
  const unavailable = results.filter((result) => result.status === "unavailable").length;
  return {
    status: unavailable === results.length && results.length ? "unavailable" : "complete",
    sources: ["Crossref", "OpenAlex"],
    checked,
    limit: LOOKUP_LIMIT,
    skipped: Math.max(0, (entries?.length || 0) - selected.length),
    results,
  };
}

export { LOOKUP_LIMIT };
