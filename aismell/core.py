"""aismell core detector — sniffs AI-smell line by line."""

from __future__ import annotations

import re
import statistics
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("aismell needs PyYAML. install: pip install pyyaml") from exc


PATTERNS_DIR = Path(__file__).resolve().parent.parent / "patterns"


@dataclass
class Pattern:
    id: str
    kind: str  # phrase | regex
    severity: int
    pattern: str
    message: str
    suggestion: str = ""
    _compiled: re.Pattern | None = field(default=None, repr=False)

    def compile(self) -> re.Pattern:
        if self._compiled is None:
            if self.kind == "phrase":
                # case-insensitive whole-ish word match
                self._compiled = re.compile(
                    r"\b" + self.pattern + r"\b",
                    re.IGNORECASE,
                )
            else:
                self._compiled = re.compile(self.pattern)
        return self._compiled


@dataclass
class Hit:
    line: int
    col: int
    end: int
    text: str           # full sentence/line context
    matched: str        # what matched
    pattern: Pattern


@dataclass
class StructuralFinding:
    line: int
    kind: str           # 'rhythm' | 'list-density' | 'em-dash' | 'tricolon'
    severity: int
    message: str
    suggestion: str = ""


@dataclass
class Report:
    sentences: int
    hits: list[Hit] = field(default_factory=list)
    structural: list[StructuralFinding] = field(default_factory=list)
    score: float = 0.0  # 0..1
    severity_label: str = ""

    @property
    def total_findings(self) -> int:
        return len(self.hits) + len(self.structural)


# ---------- loading ----------

def load_patterns(lang: str) -> list[Pattern]:
    path = PATTERNS_DIR / f"{lang}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"patterns file not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    out: list[Pattern] = []
    for raw in data.get("patterns", []):
        out.append(Pattern(
            id=raw["id"],
            kind=raw["kind"],
            severity=int(raw["severity"]),
            pattern=raw["pattern"],
            message=raw["message"],
            suggestion=raw.get("suggestion", ""),
        ))
    return out


# ---------- language detection ----------

_ES_HINTS = re.compile(
    r"\b(que|para|como|pero|porque|según|también|así|este|esta|del|los|las|una|uno|"
    r"hacia|cuando|aunque|entonces|aquí|allí|qué|sí|no)\b",
    re.IGNORECASE,
)
_EN_HINTS = re.compile(
    r"\b(the|and|of|to|in|that|is|with|for|on|as|by|are|this|from|but|or|"
    r"because|when|where|which|though)\b",
    re.IGNORECASE,
)


def detect_lang(text: str) -> str:
    es = len(_ES_HINTS.findall(text))
    en = len(_EN_HINTS.findall(text))
    return "es" if es >= en else "en"


# ---------- sentence splitting (simple, language-agnostic) ----------

_SENT_SPLIT = re.compile(r"(?<=[\.\?!¡¿…])\s+(?=[A-ZÁÉÍÓÚÑ¿¡])|\n+")


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENT_SPLIT.split(text) if s.strip()]


# ---------- structural checks ----------

def _check_em_dashes(text: str, lines: list[str]) -> list[StructuralFinding]:
    out: list[StructuralFinding] = []
    for i, line in enumerate(lines, start=1):
        count = line.count("—")
        if count >= 2:
            out.append(StructuralFinding(
                line=i,
                kind="em-dash",
                severity=2,
                message=f"{count} em-dashes en una línea — la IA los abusa",
                suggestion="reemplaza por comas, paréntesis o puntos",
            ))
    return out


def _check_rhythm(sentences: list[str]) -> list[StructuralFinding]:
    """If sentence lengths cluster too tight, flag monorhythm."""
    if len(sentences) < 6:
        return []
    lengths = [len(s.split()) for s in sentences]
    mean = statistics.mean(lengths)
    if mean < 5:
        return []
    try:
        std = statistics.stdev(lengths)
    except statistics.StatisticsError:
        return []
    cv = std / mean if mean else 0
    if cv < 0.35:
        return [StructuralFinding(
            line=0,
            kind="rhythm",
            severity=2,
            message=f"varianza de oración baja (CV={cv:.2f}) — ritmo plano AI",
            suggestion="mezcla oraciones cortas y largas",
        )]
    return []


def _check_list_density(text: str) -> list[StructuralFinding]:
    lines = text.splitlines()
    bullets = sum(1 for ln in lines if re.match(r"\s*([-*•]|\d+\.)\s", ln))
    if not lines:
        return []
    ratio = bullets / max(len(lines), 1)
    if bullets >= 5 and ratio > 0.4:
        return [StructuralFinding(
            line=0,
            kind="list-density",
            severity=1,
            message=f"{bullets} bullets ({ratio:.0%} del texto) — densidad alta de listas",
            suggestion="convierte alguno en prosa para variar el formato",
        )]
    return []


def _check_tricolon(sentences: list[str]) -> list[StructuralFinding]:
    """Flag sentences that contain exactly three comma-separated items in a list."""
    out: list[StructuralFinding] = []
    pattern = re.compile(r"\b\w+\b,\s+\b\w+\b,?\s+(?:and|y)\s+\b\w+\b", re.IGNORECASE)
    triples = sum(1 for s in sentences if pattern.search(s))
    if triples >= 3:
        out.append(StructuralFinding(
            line=0,
            kind="tricolon",
            severity=1,
            message=f"{triples} oraciones con regla de tres — patrón AI",
            suggestion="rompe alguna en dos items o cuatro",
        ))
    return out


# ---------- main analyze ----------

def analyze(
    text: str,
    lang: str | None = None,
    strict: bool = False,
) -> tuple[Report, str]:
    """Analyze text. Returns (report, lang_used)."""
    lang = lang or detect_lang(text)
    patterns = load_patterns(lang)

    lines = text.splitlines()
    sentences = split_sentences(text)
    report = Report(sentences=len(sentences))

    min_severity = 2 if strict else 1

    # phrase / regex hits, line-anchored
    for i, line in enumerate(lines, start=1):
        for p in patterns:
            if p.severity < min_severity:
                continue
            for m in p.compile().finditer(line):
                report.hits.append(Hit(
                    line=i,
                    col=m.start(),
                    end=m.end(),
                    text=line,
                    matched=m.group(0),
                    pattern=p,
                ))

    # structural checks
    if not strict:
        report.structural.extend(_check_em_dashes(text, lines))
        report.structural.extend(_check_list_density(text))
        report.structural.extend(_check_tricolon(sentences))
    report.structural.extend(_check_rhythm(sentences))

    # score
    weight = sum(h.pattern.severity for h in report.hits)
    weight += sum(f.severity for f in report.structural)
    # normalize against sentence count (cap at 1.0)
    report.score = min(1.0, weight / max(len(sentences), 1) / 3.0)

    if report.score >= 0.6:
        report.severity_label = "alto" if lang == "es" else "high"
    elif report.score >= 0.3:
        report.severity_label = "moderado" if lang == "es" else "moderate"
    elif report.score > 0:
        report.severity_label = "bajo" if lang == "es" else "low"
    else:
        report.severity_label = "limpio" if lang == "es" else "clean"

    return report, lang
