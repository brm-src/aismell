"""aismell — sniff AI-smell in text."""

from .core import analyze, detect_lang, load_patterns
from .render import render

__version__ = "0.2.0"
__all__ = ["analyze", "detect_lang", "load_patterns", "render", "__version__"]
