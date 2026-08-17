"""Conservative automatic cleanup for short everyday texts.

This is deliberately not a generative rewriter. It removes only framing that
adds no information, preserving wording, facts, links, names, and tone.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .core import detect_lang


@dataclass(frozen=True)
class CleanResult:
    text: str
    language: str
    changes: int


_RULES: dict[str, tuple[str, ...]] = {
    "es": (
        r"\bcabe mencionar que\s+",
        r"\bes importante (?:notar|señalar|destacar|mencionar) que\s+",
        r"\bvale la pena destacar que\s+",
        r"\ben este sentido,?\s+",
        r"\bdicho esto,?\s+",
        r"\ben (?:resumen|síntesis|definitiva),?\s+",
        r"\ben última instancia,?\s+",
    ),
    "en": (
        r"^\s*(?:here'?s the thing|let'?s be clear)\s*:\s*",
        r"\b(?:it is|it's) worth noting that\s+",
        r"\bit is important to (?:note|mention|highlight) that\s+",
        r"\bin this regard,?\s+",
        r"\bthat said,?\s+",
        r"\bin (?:summary|conclusion),?\s+",
        r"\bultimately,?\s+",
        r"\s+i hope this helps!?\s*$",
    ),
}

_PROTECTED = re.compile(
    r"`[^`]*`|https?://[^\s]+|\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b",
    re.IGNORECASE,
)
_SENTENCE_START = re.compile(r"(^|[.!?]\s+)([a-záéíóúüñ])")


def _protect(text: str) -> tuple[str, list[str]]:
    values: list[str] = []

    def replace(match: re.Match[str]) -> str:
        values.append(match.group(0))
        return f"\ue000{len(values) - 1}\ue001"

    return _PROTECTED.sub(replace, text), values


def _restore(text: str, values: list[str]) -> str:
    for index, value in enumerate(values):
        text = text.replace(f"\ue000{index}\ue001", value)
    return text


def _tidy(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    text = re.sub(r"(^|[.!?]\s+)([a-záéíóúüñ])", lambda m: m.group(1) + m.group(2).upper(), text)
    return text.strip()


def clean(text: str, lang: str | None = None) -> CleanResult:
    """Remove high-confidence AI framing from a short text without rewriting it."""
    language = lang or detect_lang(text)
    language = language if language in _RULES else "en"
    masked, protected = _protect(text)
    changes = 0

    for pattern in _RULES[language]:
        masked, count = re.subn(pattern, "", masked, flags=re.IGNORECASE)
        changes += count

    return CleanResult(text=_restore(_tidy(masked), protected), language=language, changes=changes)
