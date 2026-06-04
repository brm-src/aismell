"""DOCX support for aismell — read .docx, write a marked-up copy.

A .docx is a ZIP containing XML. We use stdlib only:
    - zipfile to read/write the package
    - xml.etree.ElementTree to parse and rewrite document.xml,
      comments.xml, [Content_Types].xml, and the relationships file.

What the marked-up copy contains:
    - Yellow highlight on every matched span (line + structural alike).
    - A Word/LibreOffice review comment anchored to each match, with
      the rule message and our suggestion. Renders in the right margin
      sidebar like any human reviewer's comment.

Limitations (v1):
    - We only process paragraphs in the main document body. Tables,
      headers, footers, footnotes are passed through untouched. This
      is fine for typical essays/blog posts/PRs/articles.
    - We do not split matches across paragraphs. Each match is local
      to its paragraph (which is how analyze() already works).
"""
from __future__ import annotations

import datetime as _dt
import re
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET

from .core import Hit, StructuralFinding, analyze


KIND_LABELS_ES = {
    "em-dash": "guiones largos repetidos",
    "list-density": "exceso de listas",
    "ellipses": "pausas dramáticas",
    "section-headers": "encabezados genéricos",
    "emphasis-overload": "énfasis tipográfico excesivo",
    "tricolon": "serie de tres elementos",
    "rhetorical-qa": "pregunta retórica",
    "binary-reframe": "contraste prefabricado",
    "negative-listing": "lista negativa",
    "false-agency": "agencia falsa",
    "passive-voice": "voz pasiva evasiva",
    "wh-starters": "arranques interrogativos repetidos",
    "paragraph-connectors": "conectores al inicio de párrafo",
    "paragraph-symmetry": "párrafos demasiado simétricos",
    "synthetic-academic": "textura académica sintética",
    "low-specificity": "baja especificidad",
    "vague-sentence-stack": "frases abstractas acumuladas",
    "essay-scaffolding": "andamiaje de ensayo",
    "rhythm": "ritmo plano",
}
KIND_LABELS_EN = {
    "em-dash": "repeated em dashes",
    "list-density": "too many lists",
    "ellipses": "dramatic pauses",
    "section-headers": "generic headings",
    "emphasis-overload": "typographic emphasis overload",
    "tricolon": "three-part series",
    "rhetorical-qa": "rhetorical question",
    "binary-reframe": "prefabricated contrast",
    "negative-listing": "negative list",
    "false-agency": "false agency",
    "passive-voice": "evasive passive voice",
    "wh-starters": "repeated question-word openings",
    "paragraph-connectors": "paragraph-opening connectors",
    "paragraph-symmetry": "overly symmetric paragraphs",
    "synthetic-academic": "synthetic academic texture",
    "low-specificity": "low specificity",
    "vague-sentence-stack": "stacked abstract sentences",
    "essay-scaffolding": "essay scaffold",
    "rhythm": "flat rhythm",
}


def _kind_label(kind: str, lang: str) -> str:
    labels = KIND_LABELS_ES if lang == "es" else KIND_LABELS_EN
    return labels.get(kind, kind.replace("-", " "))


def _format_hit_comment(hit: Hit, lang: str) -> str:
    matched = hit.matched.strip()
    msg = hit.pattern.message.strip()
    sug = (hit.pattern.suggestion or "").strip()
    if lang == "es":
        advice = sug or "reescribe esta parte con una afirmación más directa y específica"
        if "activa" in advice and "voz" not in advice:
            advice += "; voz activa significa nombrar quién realiza la acción y qué hace"
        return (
            f"Hallazgo: expresión con olor a IA.\n"
            f"Texto marcado: «{matched}».\n"
            f"Por qué importa: {msg}.\n"
            f"Qué cambiar: {advice}. Ajusta la frase según el argumento de este documento; no reemplaces mecánicamente."
        )
    advice = sug or "rewrite this part with a more direct and specific claim"
    return (
        f"Finding: AI-smell expression.\n"
        f"Marked text: “{matched}”.\n"
        f"Why it matters: {msg}.\n"
        f"What to change: {advice}. Adapt it to this document; do not replace mechanically."
    )


def _format_structural_comment(finding: StructuralFinding, lang: str) -> str:
    label = _kind_label(finding.kind, lang)
    msg = finding.message.strip()
    sug = (finding.suggestion or "").strip()
    if lang == "es":
        advice = sug or "revisa este patrón en el contexto del párrafo y decide si aporta precisión o solo forma"
        if finding.kind == "passive-voice":
            advice = "usa voz activa: nombra quién hizo la acción y qué hizo; por ejemplo, «el equipo omitió X» es más claro que «se cometieron errores»"
        elif finding.kind == "false-agency":
            advice = "cambia abstracciones que actúan solas por actores concretos: autor, institución, muestra, entrevistado, dato o decisión documentada"
        elif finding.kind == "low-specificity":
            advice = "agrega evidencia local: cita, autor, fecha, caso, muestra, lugar o consecuencia verificable dentro del documento"
        return f"Hallazgo: {label}.\nPor qué importa: {msg}.\nQué cambiar: {advice}."
    advice = sug or "review this pattern in context and decide whether it adds precision or only polish"
    return f"Finding: {label}.\nWhy it matters: {msg}.\nWhat to change: {advice}."


# OOXML namespaces
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
PKG_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
COMMENTS_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments"
COMMENTS_CT = "application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"

ET.register_namespace("w", W_NS)


def _w(tag: str) -> str:
    return f"{{{W_NS}}}{tag}"


# ---------- low-level docx helpers ----------

def _para_text(p_elem: ET.Element) -> str:
    """Concatenate visible text inside a <w:p> across all <w:r><w:t>."""
    parts: list[str] = []
    for t in p_elem.iter(_w("t")):
        if t.text:
            parts.append(t.text)
    return "".join(parts)


def _t_runs(p_elem: ET.Element) -> list[tuple[ET.Element, ET.Element]]:
    """Return a flat ordered list of (parent_run, text_element) pairs in
    document order. We need both because to split text we replace the
    text element inside its run."""
    pairs: list[tuple[ET.Element, ET.Element]] = []
    for r in p_elem.iter(_w("r")):
        for t in r.findall(_w("t")):
            pairs.append((r, t))
    return pairs


def _split_run_at(p_elem: ET.Element, char_start: int, char_end: int):
    """Within paragraph p_elem, split text runs so that the [start,end)
    span sits in its own run. Returns (start_run, marked_run, end_run)
    where marked_run contains exactly the matched text. The caller is
    responsible for deciding what to wrap or style on marked_run.

    If the match crosses multiple <w:t> nodes, we only keep the first
    one wrapped (good enough for highlighting; conservative). v2 can
    span them properly.
    """
    pairs = _t_runs(p_elem)
    cursor = 0
    for run, t_elem in pairs:
        text = t_elem.text or ""
        run_end = cursor + len(text)
        if cursor <= char_start < run_end:
            local_start = char_start - cursor
            local_end = min(char_end - cursor, len(text))
            before = text[:local_start]
            matched = text[local_start:local_end]
            after = text[local_end:]
            return _split_one_run(run, t_elem, before, matched, after, p_elem)
        cursor = run_end
    return None


def _serialize_xml(elem: ET.Element) -> bytes:
    """Stable XML serialization with declaration. Avoids the
    `standalone` kwarg which is not on older Pythons."""
    body = ET.tostring(elem, encoding="UTF-8")
    if body.startswith(b"<?xml"):
        return body
    return b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n' + body


def _clone(elem: ET.Element) -> ET.Element:
    """Deep-copy an ElementTree element (stdlib lacks a public clone)."""
    raw = ET.tostring(elem, encoding="unicode")
    return ET.fromstring(raw)


def _highlight_rpr(rpr: ET.Element | None, color: str = "yellow") -> ET.Element:
    """Return an <w:rPr> with highlight applied (cloning the original
    properties if any)."""
    new_rpr = _clone(rpr) if rpr is not None else ET.Element(_w("rPr"))
    # Drop any existing highlight to avoid duplicates
    for h in list(new_rpr.findall(_w("highlight"))):
        new_rpr.remove(h)
    h = ET.SubElement(new_rpr, _w("highlight"))
    h.set(_w("val"), color)
    return new_rpr


def _split_one_run(
    run: ET.Element,
    t_elem: ET.Element,
    before: str,
    matched: str,
    after: str,
    p_elem: ET.Element,
) -> tuple[ET.Element, ET.Element, ET.Element | None]:
    """Replace `run` in `p_elem` with up to three runs:
        before-run | marked-run (highlighted) | after-run
    Returns (before_run, marked_run, after_run_or_None).
    """
    # Find the position of `run` inside its parent (paragraph or hyperlink wrapper)
    parent = None
    for candidate in p_elem.iter():
        for i, child in enumerate(list(candidate)):
            if child is run:
                parent = candidate
                index = i
                break
        if parent is not None:
            break
    if parent is None:
        # fallback: just rewrite text content
        t_elem.text = before + matched + after
        return run, run, None

    rpr = run.find(_w("rPr"))

    new_runs: list[ET.Element] = []

    # before
    if before:
        before_run = ET.Element(_w("r"))
        if rpr is not None:
            before_run.append(_clone(rpr))
        bt = ET.SubElement(before_run, _w("t"))
        bt.text = before
        bt.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        new_runs.append(before_run)
    else:
        before_run = None

    # matched (highlighted)
    marked_run = ET.Element(_w("r"))
    marked_run.append(_highlight_rpr(rpr))
    mt = ET.SubElement(marked_run, _w("t"))
    mt.text = matched
    mt.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    new_runs.append(marked_run)

    # after
    if after:
        after_run = ET.Element(_w("r"))
        if rpr is not None:
            after_run.append(_clone(rpr))
        at = ET.SubElement(after_run, _w("t"))
        at.text = after
        at.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        new_runs.append(after_run)
    else:
        after_run = None

    # Replace the original run with the new sequence
    parent.remove(run)
    for i, nr in enumerate(new_runs):
        parent.insert(index + i, nr)

    return (before_run or marked_run), marked_run, after_run


def _wrap_with_comment(
    p_elem: ET.Element,
    marked_run: ET.Element,
    comment_id: int,
):
    """Insert <w:commentRangeStart> before marked_run and
    <w:commentRangeEnd> + reference after."""
    parent = None
    for cand in p_elem.iter():
        for i, child in enumerate(list(cand)):
            if child is marked_run:
                parent = cand
                index = i
                break
        if parent is not None:
            break
    if parent is None:
        return

    start = ET.Element(_w("commentRangeStart"))
    start.set(_w("id"), str(comment_id))
    end = ET.Element(_w("commentRangeEnd"))
    end.set(_w("id"), str(comment_id))
    ref_run = ET.Element(_w("r"))
    rpr = ET.SubElement(ref_run, _w("rPr"))
    rs = ET.SubElement(rpr, _w("rStyle"))
    rs.set(_w("val"), "CommentReference")
    cr = ET.SubElement(ref_run, _w("commentReference"))
    cr.set(_w("id"), str(comment_id))

    parent.insert(index, start)
    parent.insert(index + 2, end)
    parent.insert(index + 3, ref_run)


# ---------- main API ----------

@dataclass
class DocxResult:
    findings: int
    sentences: int
    score: float
    severity_label: str
    output_path: Path


def annotate_docx(
    in_path: Path,
    out_path: Path,
    lang: str | None = None,
    strict: bool = False,
    author: str = "aismell",
) -> DocxResult:
    """Read a .docx, run aismell over its paragraphs, write a copy
    with yellow highlights and review comments at every finding."""
    in_path = Path(in_path)
    out_path = Path(out_path)
    if not in_path.exists():
        raise FileNotFoundError(f"docx not found: {in_path}")

    # Copy the source so we don't mutate it on disk while building.
    if in_path.resolve() != out_path.resolve():
        shutil.copyfile(in_path, out_path)

    # Read the document XML and the full paragraph text for analysis.
    with zipfile.ZipFile(out_path, "r") as zf:
        try:
            doc_xml = zf.read("word/document.xml")
        except KeyError as exc:
            raise ValueError("not a Word .docx (missing word/document.xml)") from exc
        existing_files = set(zf.namelist())
        rels_xml = zf.read("word/_rels/document.xml.rels")
        ct_xml = zf.read("[Content_Types].xml")
        existing_comments_xml: bytes | None = None
        if "word/comments.xml" in existing_files:
            existing_comments_xml = zf.read("word/comments.xml")

    doc_tree = ET.ElementTree(ET.fromstring(doc_xml))
    body = doc_tree.getroot().find(_w("body"))
    if body is None:
        raise ValueError("docx has no body")

    # Concatenate all paragraph text with newlines for analysis. Paragraph
    # boundaries become newline boundaries — analyze() splits sentences
    # and runs structural checks across the whole doc.
    paragraphs = list(body.iter(_w("p")))
    para_texts: list[str] = [_para_text(p) for p in paragraphs]
    full_text = "\n".join(para_texts)

    report, lang_used = analyze(full_text, lang=lang, strict=strict)

    # We need each hit's paragraph index and offset within that paragraph.
    # analyze() returns line numbers (1-based, from text.splitlines()).
    # Since we joined paragraphs with single \n, line N = paragraph (N-1).

    # Group hits by paragraph index.
    para_hits: dict[int, list[Hit]] = {}
    for hit in report.hits:
        para_idx = hit.line - 1
        if 0 <= para_idx < len(paragraphs):
            para_hits.setdefault(para_idx, []).append(hit)

    # Build comments. Existing comments (if any) are preserved.
    comments_root, next_id = _load_or_create_comments(existing_comments_xml)

    # Apply hits paragraph by paragraph. Process in reverse character
    # order within each paragraph so earlier offsets stay valid.
    for para_idx, hits in para_hits.items():
        p_elem = paragraphs[para_idx]
        for hit in sorted(hits, key=lambda h: h.col, reverse=True):
            comment_id = next_id
            next_id += 1
            split = _split_run_at(p_elem, hit.col, hit.end)
            if split is None:
                continue
            _, marked_run, _ = split
            _wrap_with_comment(p_elem, marked_run, comment_id)
            comment_text = _format_hit_comment(hit, lang_used)
            _append_comment(comments_root, comment_id, author, comment_text)

    # Structural findings: we don't have a per-paragraph anchor for some,
    # so we attach them as comments on the first paragraph.
    if report.structural and paragraphs:
        first_para = paragraphs[0]
        for finding in report.structural:
            comment_id = next_id
            next_id += 1
            # Insert an anchor at the very start of the first run.
            anchor = _anchor_at_para_start(first_para)
            if anchor is None:
                continue
            _wrap_with_comment(first_para, anchor, comment_id)
            text = _format_structural_comment(finding, lang_used)
            _append_comment(comments_root, comment_id, author, text)

    new_doc_xml = _serialize_xml(doc_tree.getroot())
    new_comments_xml = _serialize_xml(comments_root)
    new_rels_xml = _ensure_comments_rel(rels_xml)
    new_ct_xml = _ensure_comments_content_type(ct_xml)

    # Rewrite the zip with our updated members.
    _rewrite_zip(
        out_path,
        overrides={
            "word/document.xml": new_doc_xml,
            "word/comments.xml": new_comments_xml,
            "word/_rels/document.xml.rels": new_rels_xml,
            "[Content_Types].xml": new_ct_xml,
        },
    )

    return DocxResult(
        findings=report.total_findings,
        sentences=report.sentences,
        score=report.score,
        severity_label=report.severity_label,
        output_path=out_path,
    )


def _anchor_at_para_start(p_elem: ET.Element) -> ET.Element | None:
    """Return the first run in the paragraph (creating an empty one if
    none exists) so a comment can be anchored to it."""
    first_run = p_elem.find(_w("r"))
    if first_run is not None:
        return first_run
    new_r = ET.Element(_w("r"))
    ET.SubElement(new_r, _w("t")).text = ""
    p_elem.insert(0, new_r)
    return new_r


# ---------- comments.xml ----------

def _load_or_create_comments(existing: bytes | None) -> tuple[ET.Element, int]:
    if existing:
        root = ET.fromstring(existing)
        ids = [int(c.get(_w("id"), "0")) for c in root.findall(_w("comment"))]
        return root, (max(ids) + 1 if ids else 0)
    root = ET.Element(_w("comments"))
    return root, 0


def _append_comment(root: ET.Element, cid: int, author: str, text: str):
    c = ET.SubElement(root, _w("comment"))
    c.set(_w("id"), str(cid))
    c.set(_w("author"), author)
    c.set(_w("date"), _dt.datetime.now().isoformat(timespec="seconds"))
    c.set(_w("initials"), "ai")
    p = ET.SubElement(c, _w("p"))
    r = ET.SubElement(p, _w("r"))
    t = ET.SubElement(r, _w("t"))
    t.text = text
    t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")


def _ensure_comments_rel(rels_xml: bytes) -> bytes:
    root = ET.fromstring(rels_xml)
    for rel in root.findall(f"{{{PKG_NS}}}Relationship"):
        if rel.get("Type") == COMMENTS_REL:
            return rels_xml  # already present
    used = {rel.get("Id") for rel in root.findall(f"{{{PKG_NS}}}Relationship")}
    next_n = 1
    while f"rId{next_n}" in used:
        next_n += 1
    rel = ET.SubElement(root, f"{{{PKG_NS}}}Relationship")
    rel.set("Id", f"rId{next_n}")
    rel.set("Type", COMMENTS_REL)
    rel.set("Target", "comments.xml")
    return _serialize_xml(root)


def _ensure_comments_content_type(ct_xml: bytes) -> bytes:
    root = ET.fromstring(ct_xml)
    for ov in root.findall(f"{{{CT_NS}}}Override"):
        if ov.get("PartName") == "/word/comments.xml":
            return ct_xml
    ov = ET.SubElement(root, f"{{{CT_NS}}}Override")
    ov.set("PartName", "/word/comments.xml")
    ov.set("ContentType", COMMENTS_CT)
    return _serialize_xml(root)


def _rewrite_zip(path: Path, overrides: dict[str, bytes]):
    """Rewrite a .docx zip in-place, replacing the listed members and
    inserting any new ones."""
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with zipfile.ZipFile(path, "r") as zin, zipfile.ZipFile(
        tmp_path, "w", zipfile.ZIP_DEFLATED
    ) as zout:
        seen: set[str] = set()
        for item in zin.infolist():
            if item.filename in overrides:
                zout.writestr(item, overrides[item.filename])
            else:
                zout.writestr(item, zin.read(item.filename))
            seen.add(item.filename)
        for name, data in overrides.items():
            if name not in seen:
                zout.writestr(name, data)
    tmp_path.replace(path)
