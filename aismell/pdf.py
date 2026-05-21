"""PDF support for aismell — read .pdf, write a marked-up copy.

Uses PyMuPDF (`fitz`) to:
    - extract text per page with character-level coordinates
    - rebuild a flat text view that maps cleanly back to (page, x, y, w, h)
    - draw yellow highlight annotations on every match
    - attach a sticky-note (text annotation) at the same spot with the
      rule message and our suggestion

We keep PyMuPDF as a soft dependency. The module raises a clear error
if it isn't installed; the rest of aismell continues working without it.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .core import Hit, analyze

try:
    import fitz  # PyMuPDF
    _HAS_FITZ = True
except ImportError:
    fitz = None  # type: ignore
    _HAS_FITZ = False


PYMUPDF_INSTALL_HINT = (
    "PDF support needs PyMuPDF. Install it with one of:\n"
    "  Arch:    sudo pacman -S python-pymupdf\n"
    "  Debian:  sudo apt install python3-pymupdf\n"
    "  Fedora:  sudo dnf install python3-pymupdf\n"
    "  macOS:   brew install pymupdf  (or pip install --user pymupdf)\n"
    "  Any:     pip install --user pymupdf"
)


@dataclass
class PdfResult:
    findings: int
    sentences: int
    score: float
    severity_label: str
    output_path: Path


@dataclass
class _CharSpan:
    page_index: int
    rect: "fitz.Rect"
    char: str


def _extract_chars(doc: "fitz.Document") -> tuple[str, list[_CharSpan]]:
    """Walk every char in every page, returning a flat text and a
    parallel list of CharSpan(page, rect). Page boundaries are
    represented as a single '\\n' in the flat text (with no CharSpan
    so coordinates stay aligned)."""
    flat: list[str] = []
    spans: list[_CharSpan] = []
    for page_index, page in enumerate(doc):
        # "rawdict" gives us every character with its bbox.
        raw = page.get_text("rawdict")
        for block in raw.get("blocks", []):
            if block.get("type") != 0:  # 0 = text
                continue
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    for ch in span.get("chars", []):
                        c = ch.get("c", "")
                        if not c:
                            continue
                        bbox = ch.get("bbox")
                        if not bbox:
                            continue
                        flat.append(c)
                        spans.append(_CharSpan(
                            page_index=page_index,
                            rect=fitz.Rect(*bbox),
                            char=c,
                        ))
                # newline at end of each visual line for sentence splitting
                flat.append("\n")
                spans.append(_CharSpan(page_index=page_index, rect=fitz.Rect(0, 0, 0, 0), char="\n"))
        # blank line between pages
        flat.append("\n")
        spans.append(_CharSpan(page_index=page_index, rect=fitz.Rect(0, 0, 0, 0), char="\n"))
    return "".join(flat), spans


def _rects_for_span(spans: list[_CharSpan], char_start: int, char_end: int) -> list[tuple[int, "fitz.Rect"]]:
    """Group character rects into one or more rects per page so a
    multi-line match is highlighted as multiple boxes (not a giant
    bounding rectangle that swallows the gap)."""
    if char_start >= len(spans):
        return []
    char_end = min(char_end, len(spans))
    by_page: dict[int, list[fitz.Rect]] = {}
    current_page: int | None = None
    current_rect: fitz.Rect | None = None
    for i in range(char_start, char_end):
        cs = spans[i]
        if cs.char == "\n":
            if current_rect is not None and current_page is not None:
                by_page.setdefault(current_page, []).append(current_rect)
                current_rect = None
            current_page = None
            continue
        if cs.rect.width <= 0:
            continue
        if cs.page_index != current_page:
            if current_rect is not None and current_page is not None:
                by_page.setdefault(current_page, []).append(current_rect)
            current_page = cs.page_index
            current_rect = fitz.Rect(cs.rect)
            continue
        # Same line if y0 is close
        if current_rect is not None and abs(cs.rect.y0 - current_rect.y0) < 2:
            current_rect.include_rect(cs.rect)
        else:
            if current_rect is not None:
                by_page.setdefault(current_page, []).append(current_rect)
            current_rect = fitz.Rect(cs.rect)
    if current_rect is not None and current_page is not None:
        by_page.setdefault(current_page, []).append(current_rect)

    out: list[tuple[int, fitz.Rect]] = []
    for page_index, rects in by_page.items():
        for r in rects:
            out.append((page_index, r))
    return out


def annotate_pdf(
    in_path: Path,
    out_path: Path,
    lang: str | None = None,
    strict: bool = False,
    author: str = "aismell",
) -> PdfResult:
    if not _HAS_FITZ:
        raise RuntimeError(PYMUPDF_INSTALL_HINT)

    in_path = Path(in_path)
    out_path = Path(out_path)
    if not in_path.exists():
        raise FileNotFoundError(f"pdf not found: {in_path}")

    doc = fitz.open(in_path)
    flat_text, spans = _extract_chars(doc)
    if not flat_text.strip():
        doc.close()
        raise ValueError(
            "no extractable text in pdf (likely a scan — needs OCR first)"
        )

    report, _ = analyze(flat_text, lang=lang, strict=strict)

    findings_added = 0
    for hit in report.hits:
        # Resolve the global char offset of this hit. analyze() uses
        # line numbers from .splitlines(); we rebuild a line index here.
        char_offset = _line_col_to_char_offset(flat_text, hit.line, hit.col)
        if char_offset is None:
            continue
        char_end = char_offset + (hit.end - hit.col)
        rects = _rects_for_span(spans, char_offset, char_end)
        if not rects:
            continue
        # Comment text
        comment_body = hit.pattern.message
        if hit.pattern.suggestion:
            comment_body += f"  →  {hit.pattern.suggestion}"
        for page_index, rect in rects:
            page = doc[page_index]
            highlight = page.add_highlight_annot(rect)
            highlight.set_info(
                title=author,
                content=f"[{hit.pattern.id}] {comment_body}",
            )
            highlight.update()
        findings_added += 1

    # Structural findings: attach as page-level text annotations on page 0
    if report.structural and len(doc) > 0:
        first_page = doc[0]
        y = 30
        for finding in report.structural:
            content = f"[{finding.kind}] {finding.message}"
            if finding.suggestion:
                content += f"  →  {finding.suggestion}"
            try:
                first_page.add_text_annot(
                    fitz.Point(20, y),
                    content,
                )
                y += 20
            except Exception:
                pass

    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(out_path, garbage=3, deflate=True)
    doc.close()

    return PdfResult(
        findings=findings_added + len(report.structural),
        sentences=report.sentences,
        score=report.score,
        severity_label=report.severity_label,
        output_path=out_path,
    )


def _line_col_to_char_offset(text: str, line_1based: int, col: int) -> int | None:
    """Convert (1-based line, 0-based column) into a char offset within `text`."""
    if line_1based < 1:
        return None
    cur_line = 1
    pos = 0
    for i, ch in enumerate(text):
        if cur_line == line_1based:
            return i + col
        if ch == "\n":
            cur_line += 1
    return None
