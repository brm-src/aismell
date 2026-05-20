"""Smoke tests for docx annotation."""

import sys
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aismell.docx import annotate_docx
from tests._docx_builder import build_docx

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def test_annotate_docx_adds_comments():
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        src = td / "in.docx"
        dst = td / "out.docx"
        build_docx(src, [
            "Vale la pena destacar que esto profundiza en las complejidades.",
            "Por otra parte, el futuro se ve brillante para quienes adopten esta tecnología robusta.",
            "En conclusión, espero que esto te sirva.",
        ])
        result = annotate_docx(src, dst, lang="es")
        assert result.findings >= 3, f"expected >=3 findings, got {result.findings}"
        assert dst.exists()

        # Validate output structure
        with zipfile.ZipFile(dst, "r") as zf:
            names = set(zf.namelist())
            assert "word/document.xml" in names
            assert "word/comments.xml" in names
            comments_xml = zf.read("word/comments.xml")
            doc_xml = zf.read("word/document.xml")

        comments = ET.fromstring(comments_xml).findall(f"{W}comment")
        assert len(comments) == result.findings, (
            f"comments.xml has {len(comments)} but report says {result.findings}"
        )

        # Document must contain commentRangeStart/End and highlight
        doc = ET.fromstring(doc_xml)
        n_starts = len(list(doc.iter(f"{W}commentRangeStart")))
        n_ends = len(list(doc.iter(f"{W}commentRangeEnd")))
        n_highlights = len(list(doc.iter(f"{W}highlight")))
        assert n_starts == n_ends == result.findings
        assert n_highlights >= 1


def test_annotate_docx_preserves_clean_text():
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        src = td / "in.docx"
        dst = td / "out.docx"
        build_docx(src, [
            "Ayer me senté a escribir y no salió nada.",
            "Tres horas mirando la pantalla.",
            "Al final cerré el laptop.",
        ])
        result = annotate_docx(src, dst, lang="es")
        # Should be very low or zero
        assert result.score < 0.1
        with zipfile.ZipFile(dst, "r") as zf:
            doc_xml = zf.read("word/document.xml")
        n_highlights = len(list(ET.fromstring(doc_xml).iter(f"{W}highlight")))
        assert n_highlights == result.findings  # 0 or very few


if __name__ == "__main__":
    failed = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  ✓ {name}")
            except AssertionError as e:
                print(f"  ✗ {name}: {e}")
                failed += 1
            except Exception as e:
                print(f"  ✗ {name}: {type(e).__name__}: {e}")
                failed += 1
    if failed:
        print(f"\n{failed} failed")
        sys.exit(1)
    print("\nall docx tests passed")
