"""The dependency-free sync must mirror canonical sources from any cwd."""

import shutil
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]


def test_sync_copies_all_consumers_and_is_reproducible():
    with TemporaryDirectory(prefix="aismell sync ") as directory:
        root = Path(directory)
        shutil.copytree(ROOT / "aismell", root / "aismell", ignore=shutil.ignore_patterns("__pycache__"))
        (root / "docs/patterns").mkdir(parents=True)
        (root / "worker/src").mkdir(parents=True)
        shutil.copy(ROOT / "docs/sync.sh", root / "docs/sync.sh")
        shutil.copy(ROOT / "worker/src/unicode_strip.js", root / "worker/src/unicode_strip.js")
        (root / "docs/patterns/stale.yaml").write_text("stale")
        for filename in ("app.js", "index.html"):
            (root / "docs" / filename).write_text("untouched")

        for cwd in (root.parent, root / "docs"):
            subprocess.run(["bash", str(root / "docs/sync.sh")], cwd=cwd, check=True, capture_output=True)
            for target in (root / "docs", root / "worker/analyzer/src/aismell"):
                assert (target / "core.py").read_bytes() == (root / "aismell/core.py").read_bytes()
                assert {p.name for p in (target / "patterns").glob("*.yaml")} >= {p.name for p in (root / "aismell/patterns").glob("*.yaml")}
                for source in (root / "aismell/patterns").glob("*.yaml"):
                    assert (target / "patterns" / source.name).read_bytes() == source.read_bytes()
            assert (root / "docs/patterns/stale.yaml").read_text() == "stale"
            for filename in ("docx.py", "biblio.py"):
                assert (root / "docs" / filename).read_bytes() == (root / "aismell" / filename).read_bytes()
            for source in (root / "aismell/patterns").glob("*.yaml"):
                assert (root / "docs" / source.name).read_bytes() == source.read_bytes()
            assert (root / "docs/unicode_strip.js").read_bytes() == (root / "worker/src/unicode_strip.js").read_bytes()
            for filename in ("app.js", "index.html"):
                assert (root / "docs" / filename).read_text() == "untouched"
