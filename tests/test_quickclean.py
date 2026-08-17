"""Tests for the conservative short-text cleaner used by the desktop plugin."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aismell.quickclean import clean


def test_cleans_common_spanish_ai_fillers_without_changing_the_message():
    result = clean(
        "Hola Ana, cabe mencionar que el informe ya está listo. "
        "En este sentido, te lo mando hoy. En resumen, gracias."
    )

    assert result.text == "Hola Ana, el informe ya está listo. Te lo mando hoy. Gracias."
    assert result.language == "es"
    assert result.changes == 3


def test_cleans_high_confidence_english_conversational_framing():
    result = clean("Here's the thing: the file is ready. I hope this helps!")

    assert result.text == "The file is ready."
    assert result.language == "en"
    assert result.changes == 2
