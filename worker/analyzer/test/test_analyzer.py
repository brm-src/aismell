import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from analyzer import analyze_for_rewrite


def test_uses_the_actual_aismell_span_and_language_for_english():
    result = analyze_for_rewrite("It is important to note that the report is ready.")

    assert result["language"] == "en"
    assert result["findings"][0]["id"] == "en.important_to_note"
    assert result["findings"][0]["matched"] == "It is important to note"
    assert "score" in result
    assert "statistical" in result["scoreComponents"]
    assert result["stats"]["word_count"] > 0


def test_uses_the_actual_aismell_span_and_language_for_spanish():
    result = analyze_for_rewrite("Es importante señalar que el informe está listo.")

    assert result["language"] == "es"
    assert result["findings"][0]["id"] == "es.es_importante_notar"


def test_passes_new_structural_evidence_to_the_rewrite_worker():
    result = analyze_for_rewrite(" ".join(["The system supports the team every day."] * 12))

    assert result["score"] > 0
    assert result["stats"]["trigram_repetition"] > 0.035
    assert any(item["id"] == "statistical-uniformity" for item in result["findings"])
