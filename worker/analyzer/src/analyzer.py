"""Shared analyzer contract backed by the actual aismell engine."""

from __future__ import annotations

from typing import Any

from aismell.core import analyze

MAX_CHARS = 3_000


def analyze_for_rewrite(text: str) -> dict[str, Any]:
    """Return high-confidence aismell evidence suitable for an opt-in rewrite."""
    source = text.strip()
    if not source:
        raise ValueError("empty")
    if len(source) > MAX_CHARS:
        raise ValueError("too-long")

    report, language = analyze(source, strict=True, include_segments=False)
    findings = []
    for hit in report.hits:
        findings.append({
            "id": hit.pattern.id,
            "matched": hit.matched,
            "message": hit.pattern.message,
            "suggestion": hit.pattern.suggestion,
            "severity": hit.pattern.severity,
        })
    return {
        "language": language,
        "findings": findings[:24],
    }
