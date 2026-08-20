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

    report, language = analyze(source, strict=False, include_segments=False)
    findings = []
    for hit in report.hits:
        if hit.pattern.severity < 2:
            continue
        findings.append({
            "id": hit.pattern.id,
            "matched": hit.matched,
            "message": hit.pattern.message,
            "suggestion": hit.pattern.suggestion,
            "severity": hit.pattern.severity,
            "kind": "lexical",
        })
    for finding in report.structural:
        if finding.severity < 2:
            continue
        findings.append({
            "id": finding.kind,
            "matched": "",
            "message": finding.message,
            "suggestion": finding.suggestion,
            "severity": finding.severity,
            "kind": "structural",
        })
    return {
        "language": language,
        "score": round(report.score * 100),
        "scoreComponents": report.score_components,
        "stats": report.stats,
        "findings": findings[:24],
    }
