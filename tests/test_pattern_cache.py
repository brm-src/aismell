"""Pattern loading must not reparse YAML for every segment or repeated run."""
from unittest.mock import patch

from aismell.core import analyze, load_patterns
import aismell.core as core


def test_patterns_are_loaded_once_per_language_per_process():
    if hasattr(load_patterns, "cache_clear"):
        load_patterns.cache_clear()
    try:
        with patch.object(core.yaml, "safe_load", wraps=core.yaml.safe_load) as load:
            for language, text in (("en", "The team reads the report."), ("es", "El equipo revisa el informe.")):
                for _ in range(2):
                    analyze(" ".join([text] * 24), lang=language)
            assert load.call_count == 2
    finally:
        if hasattr(load_patterns, "cache_clear"):
            load_patterns.cache_clear()
