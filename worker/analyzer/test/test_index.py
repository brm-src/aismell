import asyncio
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace


SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))


def test_analyzer_does_not_log_private_exception_messages(monkeypatch, capsys):
    # The Workers runtime is unavailable in CPython; keep its boundary inert.
    monkeypatch.setitem(sys.modules, "workers", SimpleNamespace(
        Response=lambda body, **kwargs: SimpleNamespace(body=body, **kwargs),
        WorkerEntrypoint=object,
    ))
    spec = importlib.util.spec_from_file_location("analyzer_entrypoint", SRC / "index.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    private_text = "PRIVATE-SENTINEL-REPORT"

    def fail(text):
        raise RuntimeError(text)

    async def request_json():
        return {"text": private_text}

    monkeypatch.setattr(module, "analyze_for_rewrite", fail)
    request = SimpleNamespace(url="https://analyzer.example/analyze", method="POST", json=request_json)
    result = asyncio.run(module.Default().fetch(request))

    assert result.status == 503
    assert json.loads(result.body) == {"error": "analyze-unavailable"}
    assert private_text not in capsys.readouterr().out
