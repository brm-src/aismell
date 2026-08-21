from pathlib import Path


APP_JS = Path(__file__).resolve().parents[1] / "docs" / "app.js"


def test_semantic_pass_runs_in_a_worker_not_on_the_main_thread():
    source = APP_JS.read_text(encoding="utf-8")

    assert 'new Worker("./embedding-worker.js", { type: "module" })' in source
    assert "await runSemanticAnalysis(" in source
    assert 'import("./embedding-analysis.js")' not in source
