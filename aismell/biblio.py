"""aismell biblio — detect references and (optionally) verify they exist.

Parser is pure Python, runs in browser (Pyodide) and CLI.
Verification needs network: CLI uses urllib; web uses JS fetch.

References detected:
- DOIs:    10.xxxx/yyyy or doi.org/10.xxxx/yyyy
- arXiv:   arXiv:YYMM.NNNNN or arXiv:YYMM.NNNNNvN
- Plain citations: "Author, X. (YEAR). Title. Journal..."
- ISBNs:   ISBN-10 or ISBN-13

Verification (CLI):
- DOI    -> api.crossref.org/works/{doi}      -> exists / not found
- arXiv  -> export.arxiv.org/api/query        -> exists / not found
- Title  -> api.crossref.org/works?query=...  -> fuzzy match score
"""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Iterable

# -------- patterns --------

# DOI: starts with "10." then ≥4 digits, slash, then suffix
_DOI_RE = re.compile(
    r"\b(10\.\d{4,9}/[-._;()/:A-Z0-9]+)\b",
    re.IGNORECASE,
)

# arXiv new style (YYMM.NNNNN, optionally with vN), or old style (cs.AI/0203012)
_ARXIV_RE = re.compile(
    r"\barXiv:\s*(\d{4}\.\d{4,5})(v\d+)?\b|"
    r"\barXiv:\s*([a-z\-]+(?:\.[A-Z]{2})?/\d{7})(v\d+)?\b",
    re.IGNORECASE,
)

# ISBN (10 or 13)
_ISBN_RE = re.compile(
    r"\bISBN(?:-1[03])?:?\s*((?:97[89][- ]?)?\d{1,5}[- ]?\d{1,7}[- ]?\d{1,7}[- ]?[\dXx])\b",
    re.IGNORECASE,
)

# Plain citation heuristic: "Surname, Initial. (YEAR). Title."
# (not perfect — flags candidates for fuzzy CrossRef lookup)
_CITATION_RE = re.compile(
    r"([A-ZÁÉÍÓÚÑ][a-záéíóúñü]+(?:[-\s][A-ZÁÉÍÓÚÑ][a-záéíóúñü]+)*),"  # surname
    r"\s+(?:[A-ZÁÉÍÓÚÑ]\.\s*)+"                                       # initials
    r"(?:&\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñü]+,\s+(?:[A-ZÁÉÍÓÚÑ]\.\s*)+)*"      # co-authors
    r"\((\d{4})\)\.\s*"                                               # year
    r"([^.]{10,200})\.",                                              # title
)


# -------- data --------

@dataclass
class Reference:
    kind: str                 # 'doi' | 'arxiv' | 'isbn' | 'citation'
    raw: str                  # what we matched
    line: int                 # 1-indexed
    col: int                  # start column
    end: int                  # end column
    identifier: str = ""      # canonical id (DOI string, arXiv id, ISBN digits)
    title: str = ""           # for plain citations
    year: str = ""            # for plain citations
    author: str = ""          # for plain citations


@dataclass
class VerifyResult:
    reference: Reference
    status: str               # 'exists' | 'not_found' | 'error' | 'unverifiable'
    detail: str = ""          # title found, error message, etc.


@dataclass
class ApaScore:
    reference: Reference
    score: float
    status: str               # 'plausible' | 'suspicious'
    issues: list[str] = field(default_factory=list)


@dataclass
class BiblioReport:
    references: list[Reference] = field(default_factory=list)
    verified: list[VerifyResult] = field(default_factory=list)


# -------- parsing --------

def find_references(text: str) -> list[Reference]:
    """Scan text and return all reference candidates found."""
    refs: list[Reference] = []
    seen: set[tuple[str, str]] = set()

    lines = text.splitlines()
    for i, line in enumerate(lines, start=1):
        # DOIs
        for m in _DOI_RE.finditer(line):
            ident = m.group(1).rstrip(".,;:)")
            key = ("doi", ident.lower())
            if key in seen:
                continue
            seen.add(key)
            refs.append(Reference(
                kind="doi",
                raw=m.group(0),
                line=i,
                col=m.start(),
                end=m.end(),
                identifier=ident,
            ))

        # arXiv
        for m in _ARXIV_RE.finditer(line):
            ident = m.group(1) or m.group(3)
            if not ident:
                continue
            key = ("arxiv", ident.lower())
            if key in seen:
                continue
            seen.add(key)
            refs.append(Reference(
                kind="arxiv",
                raw=m.group(0),
                line=i,
                col=m.start(),
                end=m.end(),
                identifier=ident,
            ))

        # ISBN
        for m in _ISBN_RE.finditer(line):
            digits = re.sub(r"[- ]", "", m.group(1))
            key = ("isbn", digits)
            if key in seen:
                continue
            seen.add(key)
            refs.append(Reference(
                kind="isbn",
                raw=m.group(0),
                line=i,
                col=m.start(),
                end=m.end(),
                identifier=digits,
            ))

    # Plain citations are multi-line so we run on full text
    for m in _CITATION_RE.finditer(text):
        # Find which line this starts on
        line_no = text.count("\n", 0, m.start()) + 1
        line_start = text.rfind("\n", 0, m.start()) + 1
        col = m.start() - line_start
        end = m.end() - line_start
        title = m.group(3).strip()
        author = m.group(1).strip()
        year = m.group(2).strip()
        key = ("cit", f"{author}|{year}|{title[:60].lower()}")
        if key in seen:
            continue
        seen.add(key)
        # Skip if this region already covered by a DOI/arXiv hit
        overlap = any(
            r.line == line_no and not (r.end <= col or r.col >= end)
            for r in refs
        )
        if overlap:
            continue
        refs.append(Reference(
            kind="citation",
            raw=lines[line_no - 1].strip() if 0 <= line_no - 1 < len(lines) else m.group(0),
            line=line_no,
            col=col,
            end=end,
            title=title,
            author=author,
            year=year,
        ))

    return refs


# -------- verification (CLI / Python with network) --------

_USER_AGENT = "aismell/0.4 (https://github.com/brm-src/aismell; mailto:caaq.x@gmail.com)"


def _fetch_json(url: str, timeout: float = 8.0) -> dict | None:
    req = urllib.request.Request(url, headers={
        "User-Agent": _USER_AGENT,
        "Accept": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            if r.status != 200:
                return None
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None


def _fetch_text(url: str, timeout: float = 8.0, retries: int = 2) -> str | None:
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                if r.status != 200:
                    return None
                return r.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < retries:
                time.sleep(3 * (attempt + 1))  # arXiv asks 3s between calls
                continue
            return None
        except Exception:
            return None
    return None


def verify_doi(doi: str) -> VerifyResult:
    url = f"https://api.crossref.org/works/{urllib.parse.quote(doi, safe='/')}"
    data = _fetch_json(url)
    if data and data.get("status") == "ok":
        msg = data["message"]
        title = (msg.get("title") or [""])[0]
        authors = msg.get("author") or []
        first_author = ""
        if authors:
            first_author = authors[0].get("family", "") or authors[0].get("name", "")
        year = ""
        for k in ("published-print", "published-online", "issued"):
            d = msg.get(k, {}).get("date-parts", [[]])
            if d and d[0]:
                year = str(d[0][0])
                break
        detail = title
        if first_author:
            detail = f"{first_author} ({year}) {title}" if year else f"{first_author}: {title}"
        return VerifyResult(reference=None, status="exists", detail=detail)
    return VerifyResult(reference=None, status="not_found",
                        detail="CrossRef no devolvió este DOI")


def verify_arxiv(arxiv_id: str) -> VerifyResult:
    url = f"https://export.arxiv.org/api/query?id_list={urllib.parse.quote(arxiv_id)}"
    text = _fetch_text(url)
    if not text:
        return VerifyResult(reference=None, status="error",
                            detail="no se pudo consultar arXiv")
    if "<entry>" not in text:
        return VerifyResult(reference=None, status="not_found",
                            detail="arXiv no devolvió este id")
    title_m = re.search(r"<entry>.*?<title>(.*?)</title>", text, re.DOTALL)
    title = re.sub(r"\s+", " ", title_m.group(1).strip()) if title_m else ""
    return VerifyResult(reference=None, status="exists", detail=title)


def verify_citation(ref: Reference) -> VerifyResult:
    """Fuzzy lookup: query CrossRef, then OpenAlex, by title + author/year."""
    if not ref.title:
        return VerifyResult(reference=ref, status="unverifiable", detail="")
    query = ref.title
    if ref.author:
        query = f"{query} {ref.author}"
    url = (
        "https://api.crossref.org/works?rows=1&"
        + urllib.parse.urlencode({"query.bibliographic": query})
    )
    data = _fetch_json(url)
    if data:
        items = data.get("message", {}).get("items", [])
        if items:
            item = items[0]
            found_title = (item.get("title") or [""])[0]
            score = item.get("score", 0.0)
            if _title_similar(ref.title, found_title) and score >= 45:
                return VerifyResult(reference=ref, status="exists",
                                    detail=f"CrossRef: {found_title}")
            if score >= 60:
                return VerifyResult(reference=ref, status="not_found",
                                    detail=f"título distinto: {found_title}")

    oa = verify_citation_openalex(ref)
    if oa.status == "exists":
        return oa
    ss = verify_citation_semantic_scholar(ref)
    if ss.status == "exists":
        return ss
    if data is None and oa.status == "error" and ss.status == "error":
        return VerifyResult(reference=ref, status="error",
                            detail="CrossRef/OpenAlex/Semantic Scholar no respondieron")
    return VerifyResult(reference=ref, status="not_found",
                        detail="sin match en CrossRef/OpenAlex/Semantic Scholar")


def _title_norm(s: str) -> str:
    return re.sub(r"\W+", "", s.lower())


def _title_similar(a: str, b: str) -> bool:
    norm_a = _title_norm(a)
    norm_b = _title_norm(b)
    if not norm_a or not norm_b:
        return False
    if norm_a in norm_b or norm_b in norm_a:
        return True
    # Token overlap catches small subtitle/punctuation differences.
    toks_a = {t for t in re.findall(r"\w+", a.lower()) if len(t) > 3}
    toks_b = {t for t in re.findall(r"\w+", b.lower()) if len(t) > 3}
    return bool(toks_a) and len(toks_a & toks_b) / len(toks_a) >= 0.75


def verify_citation_openalex(ref: Reference) -> VerifyResult:
    if not ref.title:
        return VerifyResult(reference=ref, status="unverifiable", detail="")
    params = {"search": ref.title, "per-page": "3"}
    if ref.year:
        params["filter"] = f"from_publication_date:{ref.year}-01-01,to_publication_date:{ref.year}-12-31"
    url = "https://api.openalex.org/works?" + urllib.parse.urlencode(params)
    data = _fetch_json(url)
    if not data:
        return VerifyResult(reference=ref, status="error", detail="OpenAlex no respondió")
    for item in data.get("results", []):
        found = item.get("display_name") or item.get("title") or ""
        year = str(item.get("publication_year") or "")
        if _title_similar(ref.title, found) and (not ref.year or not year or year == ref.year):
            yr = f" ({year})" if year else ""
            return VerifyResult(reference=ref, status="exists", detail=f"OpenAlex{yr}: {found}")
    return VerifyResult(reference=ref, status="not_found", detail="sin match en OpenAlex")


def verify_citation_semantic_scholar(ref: Reference) -> VerifyResult:
    if not ref.title:
        return VerifyResult(reference=ref, status="unverifiable", detail="")
    params = {"query": ref.title, "limit": "3", "fields": "title,year"}
    url = "https://api.semanticscholar.org/graph/v1/paper/search?" + urllib.parse.urlencode(params)
    data = _fetch_json(url)
    if not data:
        return VerifyResult(reference=ref, status="error", detail="Semantic Scholar no respondió")
    for item in data.get("data", []):
        found = item.get("title") or ""
        year = str(item.get("year") or "")
        if _title_similar(ref.title, found) and (not ref.year or not year or year == ref.year):
            yr = f" ({year})" if year else ""
            return VerifyResult(reference=ref, status="exists", detail=f"Semantic Scholar{yr}: {found}")
    return VerifyResult(reference=ref, status="not_found", detail="sin match en Semantic Scholar")


def verify_isbn(isbn: str) -> VerifyResult:
    clean = re.sub(r"[^0-9Xx]", "", isbn)
    if not clean:
        return VerifyResult(reference=None, status="unverifiable", detail="ISBN vacío")
    url = f"https://openlibrary.org/isbn/{urllib.parse.quote(clean)}.json"
    data = _fetch_json(url)
    if data and data.get("title"):
        return VerifyResult(reference=None, status="exists", detail=f"OpenLibrary: {data.get('title')}")
    return VerifyResult(reference=None, status="not_found", detail="OpenLibrary no encontró este ISBN")


def score_apa_reference(ref: Reference) -> ApaScore:
    """Local plausibility check for DOI-less APA-ish references; not existence proof."""
    issues: list[str] = []
    score = 0.0
    if ref.author:
        score += 0.2
    else:
        issues.append("falta autor")
    if ref.year and re.match(r"^(19|20)\d{2}$", ref.year):
        score += 0.2
    else:
        issues.append("año inválido o ausente")
    if ref.title and 3 <= len(ref.title.split()) <= 28:
        score += 0.2
    else:
        issues.append("título raro por longitud")
    remainder = ref.raw[ref.raw.find(ref.title) + len(ref.title):] if ref.title in ref.raw else ref.raw
    if re.search(r"\b(Revista|Journal|Press|Editorial|University|Universidad|Proceedings|Tesis|Thesis)\b", remainder, re.I):
        score += 0.2
    else:
        issues.append("falta fuente/editorial/revista")
    if re.search(r"\b\d+\s*\(\d+\)|\bpp?\.\s*\d+|\b\d+\s*[-–]\s*\d+", remainder, re.I):
        score += 0.1
    else:
        issues.append("faltan volumen/número/páginas")
    if ref.kind in {"doi", "arxiv", "isbn"} or ref.identifier:
        score += 0.1
    else:
        issues.append("sin identificador DOI/arXiv/ISBN")
    return ApaScore(reference=ref, score=min(1.0, score), status="plausible" if score >= 0.7 else "suspicious", issues=issues)


def verify_all(refs: list[Reference]) -> list[VerifyResult]:
    """Verify each reference. Network-bound — call from CLI only."""
    out: list[VerifyResult] = []
    for r in refs:
        if r.kind == "doi":
            res = verify_doi(r.identifier)
        elif r.kind == "arxiv":
            res = verify_arxiv(r.identifier)
        elif r.kind == "citation":
            res = verify_citation(r)
        elif r.kind == "isbn":
            res = verify_isbn(r.identifier)
        else:
            res = VerifyResult(reference=r, status="unverifiable",
                               detail="tipo de referencia no verificable")
        res.reference = r
        out.append(res)
    return out
