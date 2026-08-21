from pathlib import Path


APP_JS = Path(__file__).resolve().parents[1] / "docs" / "app.js"


def test_heavy_embedding_pass_is_not_on_default_analysis_path():
    source = APP_JS.read_text(encoding="utf-8")

    assert "const semanticEmbeddingsEnabled = false;" in source
    assert "if (!fileAnalysis && semanticEmbeddingsEnabled)" in source
