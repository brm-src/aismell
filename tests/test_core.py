"""Smoke tests for aismell core."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aismell.core import analyze, detect_lang, split_sentences


def test_detects_spanish():
    text = "Vale la pena destacar que esto es importante para el futuro."
    assert detect_lang(text) == "es"


def test_detects_english():
    text = "It is worth noting that this delves into the complexities."
    assert detect_lang(text) == "en"


def test_clean_text_low_score():
    text = (
        "Ayer me senté a escribir y no salió nada. "
        "Tres horas mirando la pantalla. "
        "El problema no era el tema."
    )
    report, lang = analyze(text)
    assert lang == "es"
    assert report.score < 0.2


def test_dirty_text_high_score():
    text = (
        "Vale la pena destacar que esto se erige como un testimonio. "
        "En última instancia, el futuro se ve brillante. "
        "Tiempos emocionantes nos esperan."
    )
    report, _ = analyze(text)
    assert report.score >= 0.5
    assert report.total_findings >= 3


def test_strict_filters_low_severity():
    text = "Por otro lado, esto es importante."
    report_normal, _ = analyze(text, strict=False)
    report_strict, _ = analyze(text, strict=True)
    assert len(report_strict.hits) <= len(report_normal.hits)


def test_em_dash_structural():
    text = "Esto — y eso — y aquello — son ejemplos."
    report, _ = analyze(text, lang="es")
    assert any(f.kind == "em-dash" for f in report.structural)


def test_english_delve_caught():
    text = "Let's delve into the complexities of this tapestry."
    report, lang = analyze(text, lang="en")
    assert lang == "en"
    ids = [h.pattern.id for h in report.hits]
    assert "en.delve" in ids
    assert "en.tapestry" in ids


def test_split_sentences():
    text = "Una. Dos. ¿Tres? ¡Cuatro!"
    assert len(split_sentences(text)) == 4


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
    print("\nall tests passed")
