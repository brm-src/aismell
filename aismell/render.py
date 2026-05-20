"""ANSI rendering for aismell reports."""

from __future__ import annotations

import os
import sys

from .core import Hit, Report, StructuralFinding


_USE_COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None


def _c(code: str, s: str) -> str:
    if not _USE_COLOR:
        return s
    return f"\033[{code}m{s}\033[0m"


RED = "31;1"
YEL = "33;1"
GRN = "32;1"
CYA = "36"
DIM = "2"
BOLD = "1"


SEV_GLYPH = {1: "·", 2: "⚠", 3: "🔴"}
SEV_COLOR = {1: CYA, 2: YEL, 3: RED}


# i18n strings
_T = {
    "es": {
        "summary": "{path}  •  {n} oraciones  •  smell: {pct}% ({label})",
        "no_findings": "limpio. nada que delatar.",
        "header_findings": "Hallazgos línea por línea",
        "header_structural": "Hallazgos estructurales",
        "suggestion": "→",
        "global": "(global)",
        "stdin": "<stdin>",
    },
    "en": {
        "summary": "{path}  •  {n} sentences  •  smell: {pct}% ({label})",
        "no_findings": "clean. nothing tells.",
        "header_findings": "Line-by-line findings",
        "header_structural": "Structural findings",
        "suggestion": "→",
        "global": "(global)",
        "stdin": "<stdin>",
    },
}


def render(path: str, report: Report, lang: str) -> str:
    t = _T.get(lang, _T["en"])
    out: list[str] = []

    pct = int(report.score * 100)
    label = report.severity_label
    if report.score >= 0.6:
        label_c = _c(RED, label)
    elif report.score >= 0.3:
        label_c = _c(YEL, label)
    else:
        label_c = _c(GRN, label)

    summary = t["summary"].format(
        path=_c(BOLD, path),
        n=report.sentences,
        pct=pct,
        label=label_c,
    )
    out.append(summary)
    out.append("")

    if report.total_findings == 0:
        out.append(_c(GRN, t["no_findings"]))
        return "\n".join(out)

    if report.hits:
        out.append(_c(BOLD, t["header_findings"]))
        # group by line
        for hit in sorted(report.hits, key=lambda h: (h.line, h.col)):
            out.append(_render_hit(hit, t))
        out.append("")

    if report.structural:
        out.append(_c(BOLD, t["header_structural"]))
        for f in report.structural:
            out.append(_render_struct(f, t))
        out.append("")

    return "\n".join(out).rstrip() + "\n"


def _render_hit(hit: Hit, t: dict[str, str]) -> str:
    sev = hit.pattern.severity
    glyph = _c(SEV_COLOR[sev], SEV_GLYPH[sev])
    line = f"L{hit.line:<4}"
    # highlight match in context
    before = hit.text[: hit.col]
    matched = _c(SEV_COLOR[sev] + ";4", hit.text[hit.col : hit.end])
    after = hit.text[hit.end :]
    context = (before + matched + after).strip()
    if len(context) > 100:
        # truncate around the match
        s, e = max(0, hit.col - 35), min(len(hit.text), hit.end + 35)
        context = ("…" if s > 0 else "") + before[s:] + matched + after[: hit.end - s + 35] + ("…" if e < len(hit.text) else "")
        context = context.strip()
    msg = _c(DIM, hit.pattern.message)
    sug = ""
    if hit.pattern.suggestion:
        sug = f"\n        {t['suggestion']} {_c(GRN, hit.pattern.suggestion)}"
    return f"  {glyph} {line} {context}\n        {msg} [{hit.pattern.id}]{sug}"


def _render_struct(f: StructuralFinding, t: dict[str, str]) -> str:
    sev = f.severity
    glyph = _c(SEV_COLOR[sev], SEV_GLYPH[sev])
    where = f"L{f.line}" if f.line else t["global"]
    msg = _c(DIM, f.message)
    sug = ""
    if f.suggestion:
        sug = f"\n        {t['suggestion']} {_c(GRN, f.suggestion)}"
    return f"  {glyph} {where:<6} {msg} [{f.kind}]{sug}"
