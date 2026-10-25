"""aismell core detector — sniffs AI-smell line by line."""

from __future__ import annotations

import json
import math
import re
import statistics
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("aismell needs PyYAML. install: pip install pyyaml") from exc


PATTERNS_DIR = Path(__file__).resolve().parent / "patterns"


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
    count: int = 1      # instances behind a document-wide finding


@dataclass
class SectionScore:
    name: str             # apertura | cuerpo | cierre
    score: float
    sentences: int
    reasons: list[str] = field(default_factory=list)


@dataclass
class SegmentScore:
    """A local, human-readable snapshot of one contiguous text window."""

    index: int
    start_sentence: int
    end_sentence: int
    sentences: int
    score: float
    label: str
    confidence: str
    findings: int
    text: str


@dataclass
class Report:
    sentences: int
    hits: list[Hit] = field(default_factory=list)
    structural: list[StructuralFinding] = field(default_factory=list)
    sections: list[SectionScore] = field(default_factory=list)
    score: float = 0.0  # 0..1
    severity_label: str = ""
    era: str = "unknown"       # 'pre-llm' | 'post-llm' | 'unknown'
    era_max_year: int = 0      # largest year found in the text
    notes: list[str] = field(default_factory=list)
    segments: list[SegmentScore] = field(default_factory=list)
    stats: dict[str, float | int] = field(default_factory=dict)
    score_components: dict[str, float] = field(default_factory=dict)
    rates: dict[str, dict[str, float]] = field(default_factory=dict)
    features: dict[str, float] = field(default_factory=dict)
    style_reasons: list[str] = field(default_factory=list)
    human_exceed: float | None = None  # share of human reference texts scoring above this one
    context: str | None = None  # fiction | academic | info | web

    @property
    def total_findings(self) -> int:
        return len(self.hits) + len(self.structural)


# ---------- loading ----------

# Mentioned years describe the subject, not the document's provenance.
_YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")


def detect_era(text: str) -> tuple[str, int]:
    """Return unknown provenance and the largest mentioned year, if any."""
    years = [int(m) for m in _YEAR_RE.findall(text)]
    return "unknown", max(years, default=0)


# Discourse-connector / filler pattern families. In academic prose these are
# genre markers, not AI tells. When they dominate the hits AND the text is
# clearly academic (citations present), the score must not rise from them.
_CONNECTOR_FAMILIES = {
    "primer_lugar", "segundo_lugar", "tercer_lugar",
    "este_sentido", "no_obstante", "por_lo_tanto", "en_sintesis",
    "en_resumen", "en_definitiva", "en_otras_palabras", "ademas",
    "consecuentemente", "en_el_marco", "se_argumenta", "se_sostiene",
    "cabe_", "es_importante", "es_fundamental", "hay_que", "conviene",
    "vale_la_pena", "resulta_", "filler", "calco", "conector",
    "in_this_sense", "first_and_foremost", "furthermore", "moreover",
    "nevertheless", "in_conclusion", "in_summary", "in_other_words",
    "it_is_important", "it_should_be", "consequently", "additionally",
    "notably", "namely", "hence", "therefore", "thus",
}
_CITATION_RE_ACADEMIC = re.compile(
    r"\([^()]{0,60}(?:19|20)\d{2}[^()]{0,60}\)"
)


# Rules are fixed during a CLI/browser/Worker process; clear this cache after
# editing a pattern file in a long-lived Python embedding.
@lru_cache(maxsize=2)
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
    r"hacia|cuando|aunque|entonces|aquí|allí|qué|sí|no|gracias|hola|por favor|"
    r"señor|señora|muy|está|están|estoy|estamos|era|eras|éramos)\b",
    re.IGNORECASE,
)
_ES_ACCENT_CHARS = re.compile(r"[áéíóúüñÁÉÍÓÚÜÑ]")
_EN_HINTS = re.compile(
    r"\b(the|and|of|to|in|that|is|with|for|on|as|by|are|this|from|but|or|"
    r"because|when|where|which|though|thank you|please|sir|madam)\b",
    re.IGNORECASE,
)


def detect_lang(text: str) -> str:
    es = len(_ES_HINTS.findall(text))
    en = len(_EN_HINTS.findall(text))
    # strong punctuation + accent marks are strong Spanish hints.
    es_extra = 0
    if "¿" in text or "¡" in text:
        es_extra += 2
    if _ES_ACCENT_CHARS.search(text):
        es_extra += 1
    es = es + es_extra
    return "es" if es >= en else "en"


# ---------- sentence splitting (simple, language-agnostic) ----------

_SENT_SPLIT = re.compile(r"(?<=[\.\?!¡¿…])\s+(?=[A-ZÁÉÍÓÚÑ¿¡])|\n+")


_HARD_WRAP = re.compile(r"(?<![.!?:;»\"”])[ \t]*\n[ \t]*(?=[a-záéíóúñü(])")


def split_sentences(text: str) -> list[str]:
    # A line break before a lowercase word is a hard wrap (PDF, e-text), not a
    # sentence boundary; splitting there fakes short, choppy sentences.
    return [s.strip() for s in _SENT_SPLIT.split(_HARD_WRAP.sub(" ", text)) if s.strip()]


def _authorial_lines(lines: list[str]) -> list[tuple[int, str]]:
    """Return lines that should count as the author's prose.

    aismell often documents bad phrases as examples. Code blocks,
    blockquotes, and Markdown tables are examples more often than author voice,
    so lexical hits there should not poison the score.
    """
    out: list[tuple[int, str]] = []
    in_fence = False
    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith(("```", "~~~")):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if stripped.startswith(">"):
            continue
        if stripped.startswith("|") and stripped.endswith("|"):
            continue
        out.append((i, line))
    return out


def _inside_spans(line: str, start: int, end: int, delimiters: list[tuple[str, str]]) -> bool:
    for opener, closer in delimiters:
        pos = 0
        while True:
            left = line.find(opener, pos)
            if left == -1:
                break
            right = line.find(closer, left + len(opener))
            if right == -1:
                break
            span_start = left + len(opener)
            span_end = right
            if span_start <= start and end <= span_end:
                return True
            pos = right + len(closer)
    return False


def _match_is_quoted_example(line: str, start: int, end: int) -> bool:
    """Skip quoted inline examples or `hope this helps`, not mere emphasis.

    This keeps documentation of slop from being scored as slop.
    """
    return _inside_spans(line, start, end, [
        ("`", "`"),
        ('"', '"'),
        ("“", "”"),
    ])


# ---------- structural checks ----------

def _check_em_dashes(text: str, lines: list[str], lang: str = "es") -> list[StructuralFinding]:
    out: list[StructuralFinding] = []
    for i, line in enumerate(lines, start=1):
        # Dialogue lines (Spanish raya, "—dijo—") use dashes as punctuation.
        if line.lstrip().startswith(("—", "–", "-")):
            continue
        count = line.count("—") + line.count("–") + line.count("--")
        if count >= 2:
            out.append(StructuralFinding(
                line=i,
                kind="em-dash",
                severity=2,
                message=(f"{count} rayas (—/–/--) en una línea — la IA las abusa" if lang == "es"
                         else f"{count} dashes (—/–/--) in one line — AI overuses them"),
                suggestion=("reemplaza por comas, paréntesis o puntos" if lang == "es"
                            else "replace them with commas, parentheses or periods"),
            ))
    return out


def _check_rhythm(sentences: list[str], lang: str = "en") -> list[StructuralFinding]:
    """If sentence lengths cluster too tight, flag monorhythm.

    Spanish calibration (Deep Technical Analysis, June 2026):
    Machine ES: μ≈25-30 words, σ≈3-5 words
    Human ES: σ≥12 words
    English keeps original threshold (CV<0.35)."""
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

    # Spanish: stricter because sentences are naturally longer but machine text is even flatter
    if lang == "es":
        threshold = 0.30
        # Extra: if std is very tight in absolute terms (σ < 6) and mean is in machine range (20-35)
        if cv < threshold or (std < 6 and 20 < mean < 35):
            return [StructuralFinding(
                line=0,
                kind="rhythm",
                severity=2,
                message=f"varianza de oración baja (CV={cv:.2f}, σ={std:.1f} palabras) — ritmo plano de IA (texto máquina ES: σ≈3-5, humano: σ≥12)",
                suggestion="mezcla oraciones cortas (5-10 palabras) y largas (40-60)",
            )]
        return []

    if cv < 0.35:
        return [StructuralFinding(
            line=0,
            kind="rhythm",
            severity=2,
            message=f"sentence length variance low (CV={cv:.2f}) — flat machine rhythm",
            suggestion="mix short and long sentences",
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
            suggestion="convierte algunas viñetas en párrafos con una idea completa: afirmación, evidencia y consecuencia",
        )]
    return []


def _check_ellipses(text: str, lang: str) -> list[StructuralFinding]:
    """Google Doc AI-isms: repeated ellipses used for fake drama."""
    # Trailing off inside dialogue is ordinary punctuation, not narration.
    narration = [ln for ln in text.splitlines() if not ln.lstrip().startswith(("—", "–", "-", '"', "“", "«"))]
    count = sum(ln.count("...") + ln.count("…") for ln in narration)
    if count < 3:
        return []
    return [StructuralFinding(
        line=0,
        kind="ellipses",
        severity=2,
        message=(
            f"{count} elipsis — pausa dramática artificial típica de IA"
            if lang == "es" else
            f"{count} ellipses — artificial dramatic pause typical of AI"
        ),
        suggestion=(
            "usa puntos normales salvo que alguien realmente se interrumpa"
            if lang == "es" else
            "use periods unless someone is genuinely trailing off"
        ),
    )]


def _check_section_headers(text: str, lang: str) -> list[StructuralFinding]:
    """Google Doc AI-isms: generic essay/chatbot headings.

    Markdown documentation legitimately has many headings. Flag the LLM-ish
    shape only when the heading labels themselves are generic response scaffolds.
    """
    generic = re.compile(
        r"^(understanding|overview|key takeaways|the problem|the solution|"
        r"moving forward|conclusion|summary|contexto|introducción|desarrollo|"
        r"conclusión|resumen|puntos clave|el problema|la solución)\b",
        re.I,
    )
    headers = 0
    for ln in text.splitlines():
        s = ln.strip()
        if not s:
            continue
        if re.match(r"^#{1,4}\s+\S", s):
            label = re.sub(r"^#{1,4}\s+", "", s).strip()
            if generic.match(label):
                headers += 1
        elif generic.match(s):
            headers += 1
    if headers < 3:
        return []
    return [StructuralFinding(
        line=0,
        kind="section-headers",
        severity=2,
        message=(
            f"{headers} encabezados genéricos — formato de respuesta IA"
            if lang == "es" else
            f"{headers} generic section headers — AI answer formatting"
        ),
        suggestion=(
            "reemplaza los rótulos genéricos por subtítulos específicos o por prosa"
            if lang == "es" else
            "replace generic labels with specific headings or prose"
        ),
    )]


def _check_emphasis_overload(text: str, lang: str) -> list[StructuralFinding]:
    """Google Doc AI-isms: excessive markdown emphasis in prose.

    README-style bold labels ("**pipx:**", "**1. Phrase patterns.**") are
    structure, not breathless emphasis, so they do not count here.
    """
    total = 0
    emphasis_rx = re.compile(r"\*\*([^*]+)\*\*|(?<!\*)\*([^*\n]+)\*(?!\*)")
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        is_bullet = bool(re.match(r"^[-*•]\s+", stripped))
        leading_bold = re.match(r"^\*\*([^*]+)\*\*", stripped)
        if leading_bold:
            label = leading_bold.group(1).strip()
            # README labels and numbered mini-headings are structure, not
            # breathless emphasis. Ignore the whole line when it starts that way.
            if is_bullet or label.endswith((":", ".")) or re.match(r"\d+\.\s+", label):
                continue
        label_prefix = re.match(r"^(?:[-*•]\s+|\d+\.\s+)?", stripped)
        label_start = label_prefix.end() if label_prefix else 0
        for match in emphasis_rx.finditer(stripped):
            content = (match.group(1) or match.group(2) or "").strip()
            # A single italicized word or a quoted UI label is not emphasis overload.
            if match.group(2) and len(content.split()) == 1:
                continue
            if content.startswith(('"', "'", "“")) and content.endswith(('"', "'", "”")):
                continue
            tail = stripped[match.end():].lstrip()
            span_starts_label = match.start() == label_start
            label_like = span_starts_label and (
                content.endswith((":", "."))
                or re.match(r"\d+\.\s+.+", content)
                or tail.startswith((":", "."))
            )
            if label_like:
                continue
            total += 1
    if total < 4:
        return []
    return [StructuralFinding(
        line=0,
        kind="emphasis-overload",
        severity=2,
        message=(
            f"{total} énfasis en negrita/cursiva — subrayado excesivo típico de IA"
            if lang == "es" else
            f"{total} bold/italic emphases — over-explained AI emphasis"
        ),
        suggestion=(
            "deja que la frase pese por sí sola"
            if lang == "es" else
            "let the sentence carry the emphasis"
        ),
    )]


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


def _check_rhetorical_qa(sentences: list[str], lang: str) -> list[StructuralFinding]:
    """Google Doc AI-isms: question immediately answered by the writer."""
    pattern = re.compile(
        r"(¿?\b(qué|por qué|cómo|cuándo|dónde|what|why|how|when|where)\b[^?\n]{0,90}\?\s*(because|porque|the answer|la respuesta|esto|that|it|simple|sencillo)\b|\b(the result|el resultado|why|por qué)\?\s*\w+)",
        re.IGNORECASE,
    )
    hits = sum(1 for s in sentences if pattern.search(s))
    if hits < 2:
        return []
    return [StructuralFinding(
        line=0,
        kind="rhetorical-qa",
        severity=3,
        message=(
            f"{hits} preguntas retóricas respondidas al tiro — patrón IA"
            if lang == "es" else
            f"{hits} rhetorical questions answered immediately — AI pattern"
        ),
        suggestion=(
            "convierte la pregunta y respuesta en una afirmación"
            if lang == "es" else
            "turn the question-answer pair into a statement"
        ),
    )]


def _check_binary_reframes(text: str, lang: str) -> list[StructuralFinding]:
    if lang == "es":
        patterns = [
            r"\bno\s+porque\b[^.!?]{1,160}[.!?]\s*porque\b",
            r"\bno\s+es\s+el\s+problema\b[^.!?]{0,160}[.!?]\s*[^.!?]{0,80}\b(sí|lo\s+es)\b",
            r"\bla\s+respuesta\s+no\s+es\b[^.!?]{1,120}[.!?]\s*\bes\b",
            r"\bparece\b[^.!?]{1,160}[.!?]\s*\ben\s+realidad\b",
            r"\bno\b[^.!?]{1,120}[.!?]\s*\bsino\b",
        ]
        msg = "contraste binario partido — reencuadre mecánico típico de IA"
        suggestion = "afirma el punto fuerte directo, sin la pista falsa previa"
    else:
        patterns = [
            r"\bnot\s+because\b[^.!?]{1,160}[.!?]\s*because\b",
            r"\b(isn['’]?t|is\s+not|aren['’]?t|are\s+not)\s+the\s+problem\b[^.!?]{0,160}[.!?]\s*[^.!?]{0,80}\b(is|are)\b",
            r"\bthe\s+answer\s+(isn['’]?t|is\s+not)\b[^.!?]{1,120}[.!?]\s*\bit['’]?s\b",
            r"\bit\s+feels\s+like\b[^.!?]{1,160}[.!?]\s*\b(it['’]?s\s+actually|actually)\b",
            r"\bnot\b[^.!?]{1,120}[.!?]\s*\bbut\b",
        ]
        msg = "split binary reframe — mechanical AI contrast"
        suggestion = "state the stronger point directly, without the decoy"
    if any(re.search(p, text, re.IGNORECASE | re.DOTALL) for p in patterns):
        return [StructuralFinding(line=0, kind="binary-reframe", severity=3, message=msg, suggestion=suggestion)]
    return []


def _check_negative_listing(text: str, lang: str) -> list[StructuralFinding]:
    if lang == "es":
        pattern = r"\bno\s+(era|fue|es)\b[^.!?]{1,120}[.!?]\s*\bno\s+(era|fue|es)\b[^.!?]{1,120}[.!?]\s*\b(era|fue|es)\b"
        msg = "listado negativo antes del punto — acumulación dramática de IA"
        suggestion = "di primero la tesis central y usa la negación solo si corrige una confusión real"
    else:
        pattern = r"\bnot\s+(a|an|the)?\b[^.!?]{1,120}[.!?]\s*\bnot\s+(a|an|the)?\b[^.!?]{1,120}[.!?]\s*\b(a|an|the|it\s+was)\b"
        msg = "negative listing before the point — AI dramatic buildup"
        suggestion = "state the central claim first; use negation only if it corrects a real misconception"
    if re.search(pattern, text, re.IGNORECASE | re.DOTALL):
        return [StructuralFinding(line=0, kind="negative-listing", severity=2, message=msg, suggestion=suggestion)]
    return []


def _check_false_agency(text: str, lang: str) -> list[StructuralFinding]:
    if lang == "es":
        patterns = [
            r"\bla\s+decisi[oó]n\s+emerge\b",
            r"\blos\s+datos\s+nos\s+dicen\b",
            r"\bel\s+mercado\s+premia\b",
            r"\bla\s+conversaci[oó]n\s+se\s+mueve\s+hacia\b",
            r"\bla\s+cultura\s+cambia\b",
            r"\bla\s+queja\s+se\s+convierte\s+en\b",
        ]
        msg = "cosas abstractas actúan como personas — falsa agencia de IA"
        suggestion = "reemplaza la abstracción por un actor concreto: quién decidió, qué dato muestra algo, quién cambió qué"
    else:
        patterns = [
            r"\bthe\s+decision\s+emerges\b",
            r"\bthe\s+data\s+tells\s+us\b",
            r"\bthe\s+market\s+rewards\b",
            r"\bthe\s+conversation\s+moves\s+toward\b",
            r"\bthe\s+culture\s+shifts\b",
            r"\bthe\s+complaint\s+becomes\s+a\s+fix\b",
        ]
        msg = "abstract things act like people — false AI agency"
        suggestion = "replace the abstraction with a concrete actor: who decided, what data shows it, who changed what"
    hits = sum(1 for p in patterns if re.search(p, text, re.IGNORECASE))
    if hits >= 1:
        sev = 3 if hits >= 2 else 2
        return [StructuralFinding(line=0, kind="false-agency", severity=sev, message=f"{hits} casos: {msg}", suggestion=suggestion)]
    return []


def _check_passive_voice(text: str, lang: str) -> list[StructuralFinding]:
    if lang == "es":
        patterns = [
            r"\bse\s+cometieron\s+errores\b",
            r"\bla\s+decisi[oó]n\s+fue\s+tomada\b",
            r"\bel\s+producto\s+fue\s+creado\b",
            r"\bse\s+cree\s+que\b",
        ]
        msg = "voz pasiva evasiva — esconde quién hizo qué"
        suggestion = "usa voz activa: nombra quién hizo la acción y qué hizo; por ejemplo, cambia «se cometieron errores» por «el equipo omitió X»"
    else:
        patterns = [
            r"\bmistakes\s+were\s+made\b",
            r"\bthe\s+decision\s+was\s+reached\b",
            r"\bthe\s+product\s+was\s+created\b",
            r"\bit\s+is\s+believed\s+that\b",
        ]
        msg = "evasively passive voice — hides who did what"
        suggestion = "use active voice: name who did the action and what they did; e.g. change «mistakes were made» to «the team missed X»"
    hits = sum(1 for p in patterns if re.search(p, text, re.IGNORECASE))
    if hits >= 1:
        sev = 3 if hits >= 2 else 2
        return [StructuralFinding(line=0, kind="passive-voice", severity=sev, message=f"{hits} casos: {msg}", suggestion=suggestion)]
    return []


def _check_wh_starters(sentences: list[str], lang: str) -> list[StructuralFinding]:
    if lang == "es":
        # Interrogatives carry an accent; unaccented que/como/cuando are relatives.
        rx = re.compile(r"^¿?(qué|por\s+qué|cómo|cuándo|dónde)\b", re.IGNORECASE)
        msg = "arranques interrogativos repetidos — molde de explicación IA"
        suggestion = "convierte preguntas retóricas en afirmaciones: sujeto + acción + consecuencia; deja una sola pregunta si de verdad organiza el argumento"
    else:
        rx = re.compile(r"^(what|why|how|when|where|which|who)\b", re.IGNORECASE)
        msg = "repeated Wh- starters — AI explainer template"
        suggestion = "turn rhetorical prompts into claims: subject + action + consequence; keep only one real organizing question"
    # Pseudo-cleft statements ("What makes this hard is trust.") are the tell;
    # real questions belong to dialogue and to rhetorical-qa.
    hits = sum(1 for s in sentences if rx.search(s.strip()) and not s.rstrip().endswith("?"))
    # Narrators say "What I saw was…" now and then; a template repeats it.
    if hits >= max(2, sum(len(s.split()) for s in sentences) // 400):
        return [StructuralFinding(line=0, kind="wh-starters", severity=2, message=f"{hits} casos: {msg}", suggestion=suggestion)]
    return []


_PARAGRAPH_CONNECTORS_ES = re.compile(
    r"^(además|adicionalmente|por otra parte|por otro lado|por un lado|en consecuencia|"
    r"asimismo|posteriormente|en primer lugar|en segundo lugar|finalmente|"
    r"no obstante|sin embargo|otro aspecto|ante este panorama|en definitiva|aun así|en general|"
    r"en síntesis|en suma|en conclusión|en resumen)[,\s]",
    re.IGNORECASE | re.MULTILINE,
)
_PARAGRAPH_CONNECTORS_EN = re.compile(
    r"^(furthermore|moreover|additionally|consequently|hence|"
    r"subsequently|firstly|secondly|finally|in conclusion|that said|"
    r"on the other hand|on one hand|ultimately|overall|in short|still|that being said|"
    r"nonetheless|nevertheless|in summary)[,\s]",
    re.IGNORECASE | re.MULTILINE,
)


def _check_paragraph_connectors(text: str, lang: str) -> list[StructuralFinding]:
    """Pangram research: AI signals strongest when each new paragraph
    starts with an explicit logical connector. Flag if there are 2+."""
    paragraphs = [p for p in re.split(r"\n\s*\n", text) if p.strip()]
    if len(paragraphs) < 2:
        return []
    rx = _PARAGRAPH_CONNECTORS_ES if lang == "es" else _PARAGRAPH_CONNECTORS_EN
    hits = sum(1 for p in paragraphs if rx.match(p.lstrip()))
    # Two signposted paragraphs in a long human essay are normal; a third of them is a template.
    if hits >= 2 and hits / len(paragraphs) >= 0.3:
        msg_es = (
            f"{hits}/{len(paragraphs)} párrafos abren con conector formal — "
            "firma fuerte de IA (Pangram)"
        )
        msg_en = (
            f"{hits}/{len(paragraphs)} paragraphs open with a formal connector — "
            "strong AI tell (Pangram)"
        )
        return [StructuralFinding(
            line=0,
            kind="paragraph-connectors",
            severity=3 if hits >= 3 else 2,
            message=msg_es if lang == "es" else msg_en,
            suggestion=(
                "borra los conectores de apertura, deja que la lógica fluya"
                if lang == "es"
                else "drop the opening connectors, let logic flow"
            ),
        )]
    return []


def _check_paragraph_symmetry(text: str, lang: str) -> list[StructuralFinding]:
    """LLMs produce paragraphs of suspiciously similar length.
    Flag when CV of word-count across 4+ paragraphs is below 0.25."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if len(paragraphs) < 4:
        return []
    word_counts = [len(p.split()) for p in paragraphs]
    if min(word_counts) < 20:
        # Skip when there are very short ones (lists, headers); not interesting.
        return []
    mean = statistics.mean(word_counts)
    try:
        std = statistics.stdev(word_counts)
    except statistics.StatisticsError:
        return []
    cv = std / mean if mean else 0
    if cv < 0.25:
        msg_es = (
            f"{len(paragraphs)} párrafos con longitud casi idéntica (CV={cv:.2f}) — "
            "simetría paramétrica AI"
        )
        msg_en = (
            f"{len(paragraphs)} paragraphs of near-identical length (CV={cv:.2f}) — "
            "AI parametric symmetry"
        )
        return [StructuralFinding(
            line=0,
            kind="paragraph-symmetry",
            severity=2,
            message=msg_es if lang == "es" else msg_en,
            suggestion=(
                "rompe la simetría: mezcla un párrafo largo con uno de una línea"
                if lang == "es"
                else "break symmetry: mix a long paragraph with a one-liner"
            ),
        )]
    return []


_SYNTHETIC_ACADEMIC_ES = re.compile(
    r"\b(transformación|educativa|contemporánea|evaluación|proceso|integral|"
    r"fortalecimiento|trayectorias?|formativas?|incorporación|metodologías?|activas?|"
    r"articular|dimensiones?|pedagógicas?|institucionales?|culturales?|experiencia|"
    r"aprendizaje|pertinente|perspectiva|complejidad|contextos?|escolares?|"
    r"condiciones?|capacidades?|reflexivas?|gestión|curricular|práctica|colaborativa|"
    r"coherencia|objetivos?|estrategias?|propuesta|estudiantes?|diversos?|mejora|"
    r"evidencias?|logro|retroalimentación|"
    r"sistemática|posibilita|consolidar|mejora continua|se configura|herramienta|"
    r"relevante|significativos?|calidad educativa|dimensión|abordaje|problemática)\b",
    re.IGNORECASE,
)
_WEAK_ABSTRACT_VERBS_ES = re.compile(
    r"\b(permite|permiten|posibilita|posibilitan|contribuye|contribuyen|favorece|"
    r"favorecen|promueve|promueven|orienta|orientan|fortalece|fortalecen|"
    r"desarrollar|generar|articular|consolidar|reconoce|comprender)\b",
    re.IGNORECASE,
)
_CONCRETE_ANCHORS = re.compile(
    r"\b\d+(?:[.,]\d+)?\b|[\"“”«»]|\b(yo|me|mi|nos|ayer|hoy|mañana|"
    r"lunes|martes|miércoles|jueves|viernes|sábado|domingo|enero|febrero|marzo|"
    r"abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\b",
    re.IGNORECASE,
)


def _word_count(text: str) -> int:
    return len(re.findall(r"\b[\wáéíóúüñÁÉÍÓÚÜÑ]+\b", text))


def _text_stats(text: str, sentences: list[str]) -> dict[str, float | int]:
    """Return transparent style statistics inspired by soundshuman."""
    tokens = [m.group(0).lower() for m in re.finditer(r"\b[\wáéíóúüñÁÉÍÓÚÜÑ'-]+\b", text)]
    lengths = [_word_count(sentence) for sentence in sentences]
    mean = statistics.mean(lengths) if lengths else 0.0
    deviation = statistics.pstdev(lengths) if len(lengths) > 1 else 0.0
    burstiness = deviation / mean if mean else 0.0
    sample = tokens[:500]
    ttr = len(set(sample)) / len(sample) if sample else 0.0
    trigrams: dict[tuple[str, str, str], int] = {}
    for i in range(len(tokens) - 2):
        key = (tokens[i], tokens[i + 1], tokens[i + 2])
        trigrams[key] = trigrams.get(key, 0) + 1
    repeated = sum(count - 1 for count in trigrams.values() if count > 1)
    return {
        "word_count": len(tokens),
        "sentence_count": len(sentences),
        "mean_sentence_length": round(mean, 2),
        "burstiness": round(burstiness, 4),
        "type_token_ratio": round(ttr, 4),
        "trigram_repetition": round(repeated / max(len(tokens) - 2, 1), 4),
    }


_FUNCTION_WORDS = {
    "es": ("de la que el en y a los se del las un por con no una su para es al lo como más pero sus le ya o "
           "este porque esta entre cuando muy sin sobre también me hasta hay donde desde todo nos todos les ni "
           "eso esto yo mi te tu ese algo así bueno pues entonces creo cada cual través fundamental además "
           "importante permite manera forma clave tanto mismo sino incluso").split(),
    "en": ("the of and to a in is that it for was on with as he be at by i this had not are but from or have an "
           "they which you were her she there would their we him been has when who will no so what if just "
           "my me your like really because then also can each its these such crucial ensuring additionally "
           "however moreover overall key various").split(),
}
_WORD_RX = re.compile(r"[^\W\d_]+(?:['’][^\W\d_]+)?", re.UNICODE)


def _style_features(text: str, sentences: list[str], lang: str) -> dict[str, float]:
    """Length-normalized stylometry. Every value is a rate or ratio so short and
    long texts are comparable. Paragraph layout is left out on purpose: it depends
    on how the text was pasted (single vs blank-line breaks), not on who wrote it."""
    text = _HARD_WRAP.sub(" ", text)
    # Formatting (bold, headings, bullets) is judged by the explainable rules;
    # here it would only teach "markdown = AI", which a human README breaks.
    text = re.sub(r"(?m)^\s*(?:#{1,6}|[-*•]|\d+[.)])\s+", "", text.replace("**", "").replace("__", ""))
    words = _WORD_RX.findall(text)
    n = max(len(words), 1)
    low = [w.lower() for w in words]
    per100 = lambda count: 100.0 * count / n
    lens = [len(_WORD_RX.findall(s)) for s in sentences] or [0]
    mean = statistics.mean(lens)
    first_words = [(_WORD_RX.findall(s) or [""])[0].lower() for s in sentences]
    caps_mid = sum(1 for s in sentences for w in _WORD_RX.findall(s)[1:] if w[:1].isupper())
    sample = low[:300]
    counts: dict[str, int] = {}
    for w in low:
        counts[w] = counts.get(w, 0) + 1
    f = {
        "sent_mean": mean,
        "sent_cv": statistics.pstdev(lens) / mean if mean else 0.0,
        "sent_short": sum(1 for x in lens if x < 8) / len(lens),
        "sent_long": sum(1 for x in lens if x > 35) / len(lens),
        "word_len": sum(len(w) for w in words) / n,
        "ttr300": len(set(sample)) / max(len(sample), 1),
        "hapax": sum(1 for c in counts.values() if c == 1) / max(len(counts), 1),
        "first_word_div": len(set(first_words)) / max(len(first_words), 1),
        "caps_mid": per100(caps_mid),
        "digits": per100(len(re.findall(r"\d+", text))),
        "comma": per100(text.count(",")),
        "semicolon": per100(text.count(";")),
        "colon": per100(text.count(":")),
        "paren": per100(text.count("(")),
        "quote": per100(len(re.findall(r"[\"«»“”]", text))),
        "question": per100(text.count("?")),
        "exclaim": per100(text.count("!")),
        "dash": per100(len(re.findall(r"—|–| - ", text))),
        "ellipsis": per100(len(re.findall(r"\.\.\.|…", text))),
        "repeat_punct": per100(len(re.findall(r"[!?]{2,}|\.{4,}", text))),
        "contraction": per100(len(re.findall(r"\b\w+['’](?:t|s|re|ve|ll|d|m)\b", text))) if lang == "en" else 0.0,
        "sent_max": max(lens),
        "word_len_sd": statistics.pstdev([len(w) for w in words]) if len(words) > 1 else 0.0,
        "conj_start": sum(1 for w in first_words if w in ("y", "pero", "and", "but", "so", "or", "o")) / max(len(first_words), 1),
    }
    suffixes = {
        "es": {"sfx_adverb": ("mente",), "sfx_nominal": ("ción", "sión", "miento"), "sfx_gerund": ("ando", "iendo"),
               "sfx_quality": ("idad", "ismo"), "sfx_able": ("able", "ible")},
        "en": {"sfx_adverb": ("ly",), "sfx_nominal": ("tion", "sion", "ment"), "sfx_gerund": ("ing",),
               "sfx_quality": ("ity", "ness"), "sfx_able": ("able", "ible")},
    }.get(lang, {})
    for key, ends in suffixes.items():
        f[key] = per100(sum(1 for w in low if len(w) > 5 and w.endswith(ends)))
    for w in _FUNCTION_WORDS.get(lang, ()):
        f["fw_" + w] = per100(counts.get(w, 0))
    return f


# BEGIN STYLE MODEL (generated by tools/style_model/train.py; do not edit by hand)
_STYLE_MODEL: dict = {
    "es": {"genre": {"classes": ["academic", "fiction", "info", "web"], "coef": [[-0.47338, 0.66029, 0.01957, -0.22616, 0.0, -0.15797, 0.19038, -0.04349, 0.04982, 0.32886, -0.12143, -0.08091, -0.06488, -0.1614, -0.08549, 0.07992, -0.32495, -0.11969, 0.27122, 0.25471, -0.09969, 0.0381, 0.09033, 0.36806, 0.05775, -0.19544, -0.02115, -0.14033, 0.42638, -0.10419, 0.17626, -0.04152, 0.08069, -0.07349, -0.16157, 0.09079, -0.16509, -0.27447, 0.02023, -0.31536, -0.0923, 0.00482, 0.08988, 0.14407, 0.21404, -0.31987, -0.05022, -0.08703, 0.11106, 0.05906, -0.0949, 0.04305, 0.1215, -0.10084, -0.03838, -0.01512, 0.00413, -0.15522, -0.32056, 0.18937, 0.24714, -0.1988, 0.17498, -0.03163, -0.09897, -0.33648, 0.10922, -0.09342, 0.12844, 0.01183, -0.25567, 0.10878, -0.25805, 0.2081, -0.24093, -0.30395, 0.08948, 0.05156, -0.27603, 0.02351, 0.00416, 0.18706, 0.01323, -0.02299, -0.18242, 0.2331, -0.06108, 0.28763, 0.06166, -0.98948, 0.38499, -0.4009, -0.34244, 0.00422, 0.0, -0.42822, -0.09107, 0.11485, -0.02054, 0.14313, -0.01444, -0.30017, -0.0478, -0.08803, -0.42001, -0.10528, -0.22161, -0.08296, -0.49812, 0.08782, -0.04192, -0.076, 0.58188, 0.39877, 0.68024, -0.35563, 0.16457, 0.92831, 0.89815], [-0.89031, 0.05917, 0.71406, 0.16551, 0.0, 0.45075, -0.68616, 0.30848, 0.31242, -0.09449, 0.31519, -0.26572, 0.22387, 0.15691, 0.01887, -0.00163, 0.09883, -0.18726, -0.15187, -0.21876, 0.03919, -0.00688, -0.11852, -0.33314, -0.07946, -0.03721, -0.06194, 0.36722, -0.32118, -0.06336, 0.05778, -0.42349, -0.19411, -0.19645, 0.24951, -0.04855, -0.02313, 0.16525, -0.21621, 0.09489, -0.03022, -0.35162, -0.42704, 0.21982, 0.02099, 0.37553, 0.02858, -0.12575, 0.10376, -0.01747, -0.09422, 0.07705, -0.00087, -0.07276, -0.15874, 0.10397, 0.31064, -0.19545, 0.02374, -0.25282, -0.09877, 0.04008, -0.22005, -0.16232, 0.09913, -0.30002, 0.24366, 0.03842, 0.11672, 0.04845, 0.4461, 0.01125, -0.05721, -0.00358, -0.00261, 0.18066, 0.09743, -0.00395, 0.26026, 0.127, 0.13576, 0.17724, -0.05722, 0.10376, 0.07403, 0.0227, -0.15233, -0.26316, -0.14406, 0.61402, -0.49814, 0.4748, -0.02117, -0.36676, 0.0, -0.28524, -0.12726, 0.13196, 0.29851, -0.15582, 0.14676, 0.19106, -0.13435, 0.94161, 0.42057, -0.09042, 0.11592, -0.2053, 0.2547, -0.10917, -0.00682, 0.01806, -0.64975, -0.54869, -0.411, 0.07201, 0.34955, -0.64587, -0.78028], [0.51714, -0.90433, -0.35506, 0.0883, 0.0, -0.55632, 0.348, -0.46278, -0.22378, -0.18406, -0.05379, 0.1226, -0.04251, -0.15103, 0.00134, -0.04777, -0.00314, 0.19193, 0.0998, -0.02458, -0.00424, -0.06545, -0.00517, 0.00582, -0.01927, 0.07728, 0.02261, -0.03978, -0.00238, 0.07308, -0.06861, 0.25848, 0.07385, 0.17289, -0.08656, 0.06143, 0.18669, 0.0696, 0.12866, 0.24612, 0.05159, 0.17864, 0.24798, 0.15108, 0.06072, -0.10217, 0.06161, 0.20094, -0.0868, -0.10301, -0.08103, -0.17838, -0.09858, 0.10588, 0.11323, -0.08309, -0.0592, 0.08912, 0.15317, -0.1307, -0.0201, 0.00668, 0.00945, 0.15133, 0.0251, 0.28656, -0.06666, 0.05695, -0.32155, -0.06207, 0.07348, -0.08047, 0.29044, -0.10665, 0.06593, 0.0342, -0.13671, 0.04579, -0.03026, -0.1979, 0.00754, -0.0386, 0.00322, 0.05207, -0.09649, -0.31762, -0.06885, -0.18949, -0.21212, 0.23794, 0.24759, 0.06747, 0.17452, 0.32217, 0.0, 0.2894, 0.45583, -0.09057, -0.17163, 0.21263, 0.06952, 0.00835, -0.00964, -0.78018, -0.2342, -0.14959, 0.55583, 1.2971, 0.22993, -0.07979, 0.2051, 0.01922, -0.02702, -0.04405, -0.13345, 0.09922, 0.05371, 0.03883, -0.14402], [0.84654, 0.18487, -0.37857, -0.02765, 0.0, 0.26354, 0.14778, 0.19779, -0.13846, -0.05031, -0.13998, 0.22403, -0.11647, 0.15553, 0.06528, -0.03053, 0.22927, 0.11501, -0.21915, -0.01136, 0.06474, 0.03423, 0.03336, -0.04074, 0.04098, 0.15537, 0.06048, -0.18711, -0.10282, 0.09447, -0.16543, 0.20654, 0.03957, 0.09705, -0.00139, -0.10367, 0.00153, 0.03962, 0.06732, -0.02565, 0.07092, 0.16817, 0.08918, -0.51497, -0.29575, 0.04651, -0.03997, 0.01184, -0.12801, 0.06142, 0.27014, 0.05828, -0.02204, 0.06772, 0.0839, -0.00576, -0.25557, 0.26154, 0.14365, 0.19415, -0.12827, 0.15204, 0.03562, 0.04261, -0.02527, 0.34994, -0.28621, -0.00195, 0.07639, 0.00179, -0.26392, -0.03956, 0.02482, -0.09787, 0.1776, 0.08909, -0.0502, -0.0934, 0.04603, 0.0474, -0.14747, -0.32569, 0.04077, -0.13284, 0.20489, 0.06182, 0.28227, 0.16503, 0.29453, 0.13752, -0.13444, -0.14137, 0.18908, 0.04037, 0.0, 0.42406, -0.2375, -0.15624, -0.10633, -0.19994, -0.20184, 0.10076, 0.19179, -0.07339, 0.23364, 0.34529, -0.45015, -1.00884, 0.01349, 0.10114, -0.15636, 0.03872, 0.09489, 0.19397, -0.13579, 0.18441, -0.56782, -0.32127, 0.02615]], "intercept": [-4.70084, -2.28028, 3.26317, 3.71795]}, "human_cdf_by_genre": {"academic": [[0.0, 0.0], [0.0, 0.025], [0.0, 0.05], [0.0, 0.075], [0.0, 0.1], [0.0001, 0.125], [0.0001, 0.15], [0.0001, 0.175], [0.0001, 0.2], [0.0003, 0.225], [0.0003, 0.25], [0.0004, 0.275], [0.0005, 0.3], [0.0006, 0.325], [0.0009, 0.35], [0.0011, 0.375], [0.0013, 0.4], [0.0015, 0.425], [0.0018, 0.45], [0.0021, 0.475], [0.0029, 0.5], [0.0038, 0.525], [0.0052, 0.55], [0.0057, 0.575], [0.0066, 0.6], [0.0084, 0.625], [0.0101, 0.65], [0.0128, 0.675], [0.0209, 0.7], [0.0226, 0.725], [0.0247, 0.75], [0.0315, 0.775], [0.0394, 0.8], [0.0515, 0.825], [0.0623, 0.85], [0.0711, 0.875], [0.1, 0.9], [0.2052, 0.925], [0.3285, 0.95], [0.5119, 0.975], [0.7933, 1.0]], "fiction": [[0.0, 0.0], [0.0, 0.025], [0.0001, 0.05], [0.0002, 0.075], [0.0002, 0.1], [0.0003, 0.125], [0.0006, 0.15], [0.0009, 0.175], [0.0012, 0.2], [0.0014, 0.225], [0.0016, 0.25], [0.0022, 0.275], [0.0028, 0.3], [0.0032, 0.325], [0.0042, 0.35], [0.0049, 0.375], [0.0067, 0.4], [0.0072, 0.425], [0.0085, 0.45], [0.0097, 0.475], [0.011, 0.5], [0.0119, 0.525], [0.0143, 0.55], [0.0168, 0.575], [0.0197, 0.6], [0.0218, 0.625], [0.0267, 0.65], [0.0317, 0.675], [0.0412, 0.7], [0.0551, 0.725], [0.0657, 0.75], [0.0726, 0.775], [0.0846, 0.8], [0.1018, 0.825], [0.1275, 0.85], [0.149, 0.875], [0.2025, 0.9], [0.2316, 0.925], [0.3542, 0.95], [0.6405, 0.975], [0.9991, 1.0]], "info": [[0.0, 0.0], [0.0, 0.025], [0.0, 0.05], [0.0, 0.075], [0.0, 0.1], [0.0, 0.125], [0.0, 0.15], [0.0, 0.175], [0.0001, 0.2], [0.0001, 0.225], [0.0001, 0.25], [0.0002, 0.275], [0.0002, 0.3], [0.0003, 0.325], [0.0004, 0.35], [0.0006, 0.375], [0.0007, 0.4], [0.001, 0.425], [0.0012, 0.45], [0.0014, 0.475], [0.0017, 0.5], [0.0022, 0.525], [0.0027, 0.55], [0.0036, 0.575], [0.0051, 0.6], [0.0065, 0.625], [0.0082, 0.65], [0.0098, 0.675], [0.0118, 0.7], [0.0144, 0.725], [0.0174, 0.75], [0.0217, 0.775], [0.0287, 0.8], [0.0364, 0.825], [0.0447, 0.85], [0.0602, 0.875], [0.0834, 0.9], [0.1239, 0.925], [0.1874, 0.95], [0.3911, 0.975], [0.9581, 1.0]], "web": [[0.0, 0.0], [0.0, 0.025], [0.0, 0.05], [0.0001, 0.075], [0.0001, 0.1], [0.0002, 0.125], [0.0002, 0.15], [0.0003, 0.175], [0.0003, 0.2], [0.0005, 0.225], [0.0007, 0.25], [0.0007, 0.275], [0.0009, 0.3], [0.0012, 0.325], [0.0013, 0.35], [0.0016, 0.375], [0.002, 0.4], [0.0024, 0.425], [0.0032, 0.45], [0.0042, 0.475], [0.0054, 0.5], [0.0064, 0.525], [0.0074, 0.55], [0.0096, 0.575], [0.0116, 0.6], [0.0152, 0.625], [0.0189, 0.65], [0.0243, 0.675], [0.0283, 0.7], [0.0354, 0.725], [0.0427, 0.75], [0.0482, 0.775], [0.0585, 0.8], [0.0743, 0.825], [0.0908, 0.85], [0.1346, 0.875], [0.1597, 0.9], [0.1963, 0.925], [0.2734, 0.95], [0.5157, 0.975], [0.9931, 1.0]]}, "keys": ["caps_mid", "colon", "comma", "conj_start", "contraction", "dash", "digits", "ellipsis", "exclaim", "first_word_div", "fw_a", "fw_adem\u00e1s", "fw_al", "fw_algo", "fw_as\u00ed", "fw_bueno", "fw_cada", "fw_clave", "fw_como", "fw_con", "fw_creo", "fw_cual", "fw_cuando", "fw_de", "fw_del", "fw_desde", "fw_donde", "fw_el", "fw_en", "fw_entonces", "fw_entre", "fw_es", "fw_ese", "fw_eso", "fw_esta", "fw_este", "fw_esto", "fw_forma", "fw_fundamental", "fw_hasta", "fw_hay", "fw_importante", "fw_incluso", "fw_la", "fw_las", "fw_le", "fw_les", "fw_lo", "fw_los", "fw_manera", "fw_me", "fw_mi", "fw_mismo", "fw_muy", "fw_m\u00e1s", "fw_ni", "fw_no", "fw_nos", "fw_o", "fw_para", "fw_permite", "fw_pero", "fw_por", "fw_porque", "fw_pues", "fw_que", "fw_se", "fw_sin", "fw_sino", "fw_sobre", "fw_su", "fw_sus", "fw_tambi\u00e9n", "fw_tanto", "fw_te", "fw_todo", "fw_todos", "fw_trav\u00e9s", "fw_tu", "fw_un", "fw_una", "fw_y", "fw_ya", "fw_yo", "hapax", "hit_ids", "hits1", "hits2", "hits3", "log_words", "paren", "question", "quote", "repeat_punct", "rule_anchor_starvation", "rule_chatbot_artifacts", "rule_combined", "rule_discourse", "rule_editorial_distance", "rule_lexical", "rule_narrative", "rule_rhythm_format", "rule_statistical", "semicolon", "sent_cv", "sent_long", "sent_max", "sent_mean", "sent_short", "sfx_able", "sfx_adverb", "sfx_gerund", "sfx_nominal", "sfx_quality", "structural", "structural_kinds", "ttr300", "word_len", "word_len_sd"], "mean": [7.091833, 0.779902, 6.185714, 0.03115, 0.0, 0.21057, 1.591691, 0.187876, 0.213393, 0.76143, 1.909694, 0.06906, 0.520275, 0.066503, 0.084062, 0.013174, 0.088312, 0.016224, 0.518385, 0.978547, 0.010502, 0.030357, 0.139354, 6.657434, 1.09156, 0.134305, 0.111211, 3.066333, 2.78399, 0.036194, 0.211503, 0.817846, 0.068459, 0.05179, 0.16457, 0.277213, 0.065353, 0.062922, 0.017617, 0.112379, 0.100187, 0.034239, 0.028847, 4.254644, 1.09887, 0.173244, 0.04512, 0.470706, 1.570577, 0.039458, 0.191229, 0.123723, 0.062044, 0.10464, 0.471094, 0.062084, 0.850495, 0.121685, 0.329128, 0.881161, 0.019197, 0.25081, 0.850218, 0.07468, 0.033719, 2.649132, 1.157913, 0.201667, 0.104262, 0.216416, 0.710781, 0.280173, 0.161953, 0.054002, 0.107262, 0.133499, 0.101167, 0.05813, 0.081203, 1.318936, 1.026439, 2.98738, 0.151679, 0.065067, 0.741771, 1.161307, 0.040566, 0.168404, 0.063898, 6.108714, 0.369123, 0.210814, 1.013917, 0.013193, 0.0, 0.029495, 0.181633, 0.013354, 0.005508, 0.106176, 0.003527, 0.034916, 0.013109, 0.290902, 0.57839, 0.192098, 59.201123, 26.070729, 0.14342, 0.186813, 0.466787, 0.681607, 2.166433, 0.736243, 8.359876, 1.50536, 0.568246, 4.976379, 3.071169], "scale": [6.65495, 1.400448, 2.231432, 0.052393, 1.0, 0.600147, 2.850771, 0.684186, 0.917716, 0.153292, 0.940956, 0.15156, 0.44518, 0.158525, 0.15754, 0.06369, 0.178006, 0.069272, 0.438144, 0.664835, 0.053664, 0.099748, 0.22944, 2.308109, 0.807431, 0.230093, 0.202879, 1.294061, 1.107056, 0.101908, 0.328528, 0.735127, 0.15288, 0.127761, 0.253251, 0.351158, 0.148585, 0.136841, 0.068839, 0.197606, 0.201803, 0.105554, 0.094533, 1.874669, 0.819844, 0.335462, 0.13854, 0.457988, 1.00936, 0.108933, 0.468991, 0.342266, 0.140329, 0.202071, 0.441259, 0.15282, 0.732776, 0.274101, 0.421979, 0.680295, 0.076731, 0.310077, 0.589481, 0.169748, 0.111618, 1.353064, 0.727537, 0.246146, 0.204491, 0.304138, 0.717684, 0.347138, 0.23654, 0.124468, 0.298843, 0.208763, 0.198566, 0.158191, 0.248138, 0.830445, 0.692705, 1.171999, 0.22637, 0.194445, 0.08027, 1.487231, 0.116172, 0.297037, 0.157072, 0.677397, 0.631384, 0.450426, 1.513645, 0.179351, 1.0, 0.11056, 0.211346, 0.046822, 0.014355, 0.168729, 0.032853, 0.058533, 0.038162, 0.886139, 0.202014, 0.212773, 42.211038, 24.750669, 0.15053, 0.269478, 0.431035, 0.57644, 1.758703, 0.767011, 8.810834, 1.184745, 0.056682, 0.412241, 0.371633], "coef": [-0.57598, 0.12166, -0.22586, -0.32461, 0.0, 0.10866, -0.73041, -0.59774, -0.48512, -0.25169, -0.14076, 0.13015, -0.25336, 0.2332, -0.32167, -0.0185, 0.2304, 0.07167, 0.07475, -0.29901, 0.11604, -0.16724, 0.26539, -0.06721, 0.04206, 0.17867, 0.3695, 0.54305, -0.07888, -0.23978, -0.06311, 0.30884, 0.16896, -0.08721, -0.32207, 0.01086, 0.14784, -0.02733, 0.5705, -0.02195, -0.31794, 0.00296, 0.0119, 0.76868, -0.12983, -0.25753, 0.01572, 0.00937, -0.17246, -0.10372, 0.34534, 0.34121, 0.13806, -0.1431, 0.31488, -0.12028, 0.08599, 0.14993, 0.03238, -0.14983, 0.00766, 0.08455, 0.07091, -0.29679, -0.41812, 0.02399, -0.41502, 0.33888, 0.64693, 0.08733, 0.1977, 0.18272, 0.28213, -0.16516, 0.14706, -0.17396, -0.24762, -0.11736, -0.0401, 0.43379, 0.59339, 0.25233, -0.05199, -0.13067, 1.02621, 0.08365, 0.15226, 0.14698, 0.24452, -0.06969, -0.24141, -0.3914, -0.00797, -0.02566, 0.0, 0.4422, 0.40849, 0.06681, 0.12736, 0.31612, 0.13895, -0.28715, -0.13055, -0.52204, -0.37799, -1.02984, -0.64295, -0.31769, 0.40561, 0.01229, 0.22633, 0.16025, -0.04104, 0.33893, -0.32597, 0.22008, -0.11712, -0.00799, -0.13623], "intercept": -3.26514, "human_cdf": [[0.0, 0.0], [0.0, 0.025], [0.0, 0.05], [0.0, 0.075], [0.0, 0.1], [0.0001, 0.125], [0.0001, 0.15], [0.0002, 0.175], [0.0002, 0.2], [0.0003, 0.225], [0.0004, 0.25], [0.0005, 0.275], [0.0007, 0.3], [0.0009, 0.325], [0.0011, 0.35], [0.0013, 0.375], [0.0016, 0.4], [0.002, 0.425], [0.0025, 0.45], [0.0032, 0.475], [0.0044, 0.5], [0.0055, 0.525], [0.0067, 0.55], [0.0081, 0.575], [0.0097, 0.6], [0.0115, 0.625], [0.0143, 0.65], [0.0177, 0.675], [0.0213, 0.7], [0.0257, 0.725], [0.0322, 0.75], [0.0407, 0.775], [0.0481, 0.8], [0.0616, 0.825], [0.0756, 0.85], [0.1025, 0.875], [0.143, 0.9], [0.1884, 0.925], [0.2672, 0.95], [0.522, 0.975], [0.9991, 1.0]], "ai_recall_at": {"0.9": 0.939, "0.95": 0.902, "0.99": 0.703}, "n": {"human": 1468, "ai": 491}},
    "en": {"genre": {"classes": ["academic", "fiction", "info", "web"], "coef": [[-0.57307, -0.29821, -0.18647, -0.22859, -0.59954, -0.37485, 0.32373, 0.01674, -0.09473, 0.12001, -0.13881, 0.12344, 0.31008, 0.19653, -0.1324, 0.01481, -0.06949, -0.14898, 0.21251, -0.22638, -0.18271, -0.11434, -0.04634, 0.00585, -0.01799, 0.21718, -0.21258, 0.04152, -0.02454, -0.23805, 0.11183, -0.46744, -0.39662, -0.33122, -0.21314, 0.32165, -0.2635, -0.17984, -0.062, 0.26562, -0.21242, -0.18629, -0.28142, 0.12399, 0.19842, -0.15819, 0.18471, -0.13651, -0.15059, -0.04561, 0.08191, 0.40165, -0.36825, 0.32163, -0.04046, -0.2569, -0.17242, 0.04824, 0.17004, -0.20165, -0.06861, 0.28604, -0.44985, 0.17104, -0.19481, 0.3622, 0.00484, 0.26664, -0.2657, 0.56062, -0.3658, -0.09693, 0.14845, 0.2546, -0.38589, -0.61391, -0.29197, -0.236, -0.2416, -0.24109, -0.40037, 0.30204, 0.30458, 0.15712, 0.04661, -0.79956, 0.49147, -0.36635, -0.35446, -0.16302, 0.0, 0.06229, 0.00663, -0.13136, -0.14349, 0.1455, -0.00168, -0.19074, -0.19361, 0.00463, -0.27508, 0.0317, -0.24147, 0.18541, -0.33212, -0.29762, 0.23214, -0.06564, 0.19936, 0.21725, 0.37113, -0.20699, -0.28196, 0.91099, 0.08689], [-0.15848, -0.03021, 0.67532, 0.10936, -0.20517, 0.23878, -0.32792, -0.07943, 0.13288, -0.18516, 0.18123, -0.14023, -0.39094, -0.26815, -0.10925, -0.1561, -0.1958, 0.20592, -0.09921, -0.31027, 0.23048, 0.09609, 0.25468, -0.31602, -0.07074, -0.1531, 0.23641, -0.16339, 0.01692, 0.32951, -0.3356, 0.02062, 0.33511, 0.40353, 0.01853, -0.29347, 0.11724, 0.16237, -0.07726, -0.625, 0.28721, -0.12147, -0.10979, 0.09397, 0.10747, 0.22301, -0.03778, 0.52132, 0.16244, 0.50179, 0.43748, -0.64533, 0.59197, -0.35493, -0.23013, 0.27371, -0.01846, 0.01073, -0.23232, 0.53175, -0.27109, 0.14105, 0.37818, -0.26574, -0.20607, -0.03445, -0.09072, -0.13844, 0.05424, -0.09079, 0.10925, 0.05385, -0.07239, 0.08918, -0.00989, 0.03386, 0.31197, -0.04889, 0.48857, -0.04698, -0.00339, -0.09712, -0.00373, -0.27631, 0.02556, 0.70716, -0.59227, 0.183, 0.41618, -0.09075, 0.0, -0.28462, 0.03814, -0.08284, 0.20802, 0.07067, 0.06805, -0.06834, 0.12649, 0.36072, 0.58301, -0.1792, -0.0444, -0.38432, 0.46083, 0.07238, -0.0473, -0.22598, 0.14203, -0.27491, -0.21197, 0.26205, 0.07657, -0.26293, -0.28005], [0.35481, -0.05558, -0.24985, 0.0997, 0.53621, 0.14061, -0.18637, -0.19062, -0.24118, -0.07924, -0.10115, 0.263, 0.10409, 0.06953, -0.01724, 0.11375, 0.20709, -0.08598, -0.10559, 0.22746, -0.00311, 0.06693, 0.07216, 0.13535, 0.16431, -0.09396, -0.01756, -0.03264, -0.02996, -0.06735, 0.31017, 0.24839, 0.06958, 0.10941, 0.21327, 0.10605, -0.32628, -0.27028, 0.09655, 0.10876, -0.0905, 0.21803, 0.23679, -0.06575, -0.46606, -0.10133, -0.03806, -0.5433, -0.0596, -0.33182, -0.26861, 0.0826, -0.40191, 0.10541, 0.05789, 0.09705, -0.20934, 0.01461, 0.0255, -0.15991, 0.3832, -0.19522, -0.13497, -0.05858, 0.15419, -0.375, 0.06802, -0.03927, -0.11667, -0.48425, 0.18187, 0.01185, -0.07261, -0.02211, 0.56346, 0.39327, -0.15458, 0.13372, -0.43303, -0.42737, 0.46079, -0.43917, 0.01325, 0.2412, 0.13739, 0.06736, -0.11435, -0.2288, 0.33341, 0.12814, 0.0, 0.25317, 0.18669, 0.32544, -0.27669, -0.1844, -0.12541, -0.08569, -0.00485, -0.32283, -0.23486, -0.01887, 0.60299, -0.08271, -0.46637, 0.12464, -0.17633, 0.17138, -0.47858, -0.1843, 0.02416, 0.08675, 0.00109, 0.09295, -0.04173], [0.37674, 0.384, -0.239, 0.01952, 0.26849, -0.00454, 0.19056, 0.25332, 0.20304, 0.14439, 0.05873, -0.24622, -0.02323, 0.00208, 0.25889, 0.02754, 0.0582, 0.02905, -0.0077, 0.30919, -0.04467, -0.04867, -0.28051, 0.17481, -0.07559, 0.02988, -0.00626, 0.1545, 0.03758, -0.02411, -0.08641, 0.19843, -0.00808, -0.18173, -0.01866, -0.13423, 0.47254, 0.28775, 0.04271, 0.25062, 0.01571, 0.08972, 0.15442, -0.15221, 0.16017, 0.03651, -0.10886, 0.15848, 0.04775, -0.12436, -0.25078, 0.16108, 0.17819, -0.07211, 0.2127, -0.11386, 0.40022, -0.07357, 0.03678, -0.1702, -0.04349, -0.23187, 0.20664, 0.15328, 0.24669, 0.04725, 0.01786, -0.08893, 0.32814, 0.01442, 0.07468, 0.03124, -0.00344, -0.32167, -0.16768, 0.18679, 0.13458, 0.15116, 0.18606, 0.71544, -0.05704, 0.23425, -0.31409, -0.12201, -0.20955, 0.02505, 0.21516, 0.41215, -0.39512, 0.12562, 0.0, -0.03083, -0.23147, -0.11124, 0.21216, -0.03177, 0.05904, 0.34477, 0.07197, -0.04252, -0.07307, 0.16637, -0.31712, 0.28162, 0.33766, 0.1006, -0.00851, 0.12024, 0.13719, 0.24196, -0.18332, -0.14181, 0.20429, -0.74101, 0.23488]], "intercept": [-3.90146, -2.45705, 1.91557, 4.44293]}, "human_cdf_by_genre": {"academic": [[0.0002, 0.0], [0.0004, 0.025], [0.0013, 0.05], [0.0043, 0.075], [0.0089, 0.1], [0.0134, 0.125], [0.0196, 0.15], [0.0269, 0.175], [0.0311, 0.2], [0.0458, 0.225], [0.0612, 0.25], [0.0649, 0.275], [0.0706, 0.3], [0.0979, 0.325], [0.1083, 0.35], [0.127, 0.375], [0.141, 0.4], [0.1702, 0.425], [0.2102, 0.45], [0.2213, 0.475], [0.2581, 0.5], [0.2695, 0.525], [0.2923, 0.55], [0.3391, 0.575], [0.407, 0.6], [0.4496, 0.625], [0.4993, 0.65], [0.5288, 0.675], [0.5505, 0.7], [0.5897, 0.725], [0.6152, 0.75], [0.6316, 0.775], [0.7024, 0.8], [0.759, 0.825], [0.8014, 0.85], [0.8329, 0.875], [0.8745, 0.9], [0.905, 0.925], [0.9296, 0.95], [0.9555, 0.975], [0.9986, 1.0]], "info": [[0.0, 0.0], [0.0013, 0.025], [0.0032, 0.05], [0.0039, 0.075], [0.0053, 0.1], [0.0089, 0.125], [0.0101, 0.15], [0.0131, 0.175], [0.0166, 0.2], [0.0214, 0.225], [0.0228, 0.25], [0.0264, 0.275], [0.0315, 0.3], [0.0363, 0.325], [0.0409, 0.35], [0.0501, 0.375], [0.0535, 0.4], [0.0667, 0.425], [0.0731, 0.45], [0.0785, 0.475], [0.0927, 0.5], [0.1077, 0.525], [0.1305, 0.55], [0.1369, 0.575], [0.1595, 0.6], [0.172, 0.625], [0.1929, 0.65], [0.2027, 0.675], [0.2308, 0.7], [0.2612, 0.725], [0.3068, 0.75], [0.3355, 0.775], [0.3809, 0.8], [0.4275, 0.825], [0.458, 0.85], [0.5344, 0.875], [0.6149, 0.9], [0.6766, 0.925], [0.81, 0.95], [0.884, 0.975], [0.9668, 1.0]], "web": [[0.0, 0.0], [0.0, 0.025], [0.0001, 0.05], [0.0002, 0.075], [0.0003, 0.1], [0.0004, 0.125], [0.0006, 0.15], [0.0007, 0.175], [0.0009, 0.2], [0.0012, 0.225], [0.0015, 0.25], [0.0019, 0.275], [0.0026, 0.3], [0.0032, 0.325], [0.0037, 0.35], [0.0044, 0.375], [0.0052, 0.4], [0.0062, 0.425], [0.0072, 0.45], [0.0081, 0.475], [0.0097, 0.5], [0.0111, 0.525], [0.0132, 0.55], [0.016, 0.575], [0.0207, 0.6], [0.0236, 0.625], [0.0308, 0.65], [0.0377, 0.675], [0.0486, 0.7], [0.0611, 0.725], [0.0718, 0.75], [0.0872, 0.775], [0.1052, 0.8], [0.1323, 0.825], [0.1669, 0.85], [0.2088, 0.875], [0.2654, 0.9], [0.3713, 0.925], [0.5305, 0.95], [0.8015, 0.975], [1.0, 1.0]]}, "keys": ["caps_mid", "colon", "comma", "conj_start", "contraction", "dash", "digits", "ellipsis", "exclaim", "first_word_div", "fw_a", "fw_additionally", "fw_also", "fw_an", "fw_and", "fw_are", "fw_as", "fw_at", "fw_be", "fw_because", "fw_been", "fw_but", "fw_by", "fw_can", "fw_crucial", "fw_each", "fw_ensuring", "fw_for", "fw_from", "fw_had", "fw_has", "fw_have", "fw_he", "fw_her", "fw_him", "fw_however", "fw_i", "fw_if", "fw_in", "fw_is", "fw_it", "fw_its", "fw_just", "fw_key", "fw_like", "fw_me", "fw_moreover", "fw_my", "fw_no", "fw_not", "fw_of", "fw_on", "fw_or", "fw_overall", "fw_really", "fw_she", "fw_so", "fw_such", "fw_that", "fw_the", "fw_their", "fw_then", "fw_there", "fw_these", "fw_they", "fw_this", "fw_to", "fw_various", "fw_was", "fw_we", "fw_were", "fw_what", "fw_when", "fw_which", "fw_who", "fw_will", "fw_with", "fw_would", "fw_you", "fw_your", "hapax", "hit_ids", "hits1", "hits2", "hits3", "log_words", "paren", "question", "quote", "repeat_punct", "rule_anchor_starvation", "rule_chatbot_artifacts", "rule_combined", "rule_discourse", "rule_editorial_distance", "rule_lexical", "rule_narrative", "rule_rhythm_format", "rule_statistical", "semicolon", "sent_cv", "sent_long", "sent_max", "sent_mean", "sent_short", "sfx_able", "sfx_adverb", "sfx_gerund", "sfx_nominal", "sfx_quality", "structural", "structural_kinds", "ttr300", "word_len", "word_len_sd"], "mean": [7.235893, 0.269465, 5.304934, 0.041299, 1.396873, 0.200079, 1.114982, 0.114072, 0.226951, 0.74172, 2.56127, 0.009174, 0.170639, 0.335561, 3.052991, 0.497262, 0.663779, 0.398044, 0.448132, 0.100688, 0.18784, 0.452283, 0.413629, 0.252723, 0.011377, 0.067547, 0.004325, 1.035328, 0.396149, 0.213933, 0.342128, 0.404061, 0.369377, 0.360811, 0.111034, 0.072829, 1.059424, 0.217477, 1.697424, 1.148477, 0.784915, 0.170383, 0.192679, 0.018866, 0.212413, 0.202742, 0.005529, 0.407427, 0.143546, 0.350807, 2.618612, 0.67173, 0.318511, 0.021361, 0.07842, 0.258796, 0.245828, 0.092069, 1.055549, 5.65678, 0.320469, 0.110405, 0.195376, 0.112617, 0.392175, 0.575512, 2.712671, 0.033849, 0.593068, 0.497742, 0.175458, 0.160155, 0.230381, 0.224659, 0.225923, 0.265692, 0.802117, 0.153785, 0.564071, 0.246138, 0.737367, 0.889, 0.088905, 0.167648, 0.058796, 5.682463, 0.318244, 0.172755, 0.881229, 0.035443, 0.0, 0.016098, 0.177592, 0.039582, 0.001354, 0.088642, 0.001105, 0.043305, 0.009647, 0.156555, 0.47059, 0.090555, 41.811349, 20.543291, 0.147396, 0.260811, 1.278753, 3.20205, 1.673971, 0.555198, 12.148389, 1.695371, 0.60455, 4.768925, 2.51424], "scale": [6.324182, 0.833881, 2.85794, 0.066308, 1.35972, 0.492764, 2.145158, 0.721237, 0.713495, 0.154461, 1.360312, 0.064838, 0.288628, 0.406116, 1.400593, 0.604039, 0.608199, 0.482505, 0.515306, 0.24732, 0.314217, 0.514184, 0.467829, 0.433365, 0.070194, 0.188104, 0.035268, 0.758357, 0.538606, 0.40978, 0.498409, 0.493069, 0.793178, 0.987035, 0.312852, 0.173857, 1.710769, 0.366275, 1.004542, 0.947685, 0.836445, 0.386518, 0.355021, 0.103722, 0.391359, 0.543046, 0.048756, 0.835838, 0.292557, 0.4683, 1.555773, 0.581967, 0.474782, 0.107718, 0.239755, 0.732657, 0.412508, 0.218748, 0.810143, 2.479758, 0.551265, 0.237383, 0.347416, 0.251599, 0.61998, 0.596161, 1.258807, 0.142947, 0.937022, 0.845855, 0.375691, 0.300938, 0.350093, 0.358077, 0.358332, 0.47668, 0.645407, 0.331116, 1.094193, 0.595604, 0.075787, 1.283631, 0.243504, 0.333665, 0.154094, 0.513474, 0.591695, 0.450539, 1.527709, 0.214401, 1.0, 0.090319, 0.205065, 0.079924, 0.007504, 0.161041, 0.018714, 0.056935, 0.03478, 0.438685, 0.228245, 0.136935, 26.439705, 11.08337, 0.197844, 0.38418, 0.941901, 1.662602, 1.745754, 0.76822, 10.282038, 1.166474, 0.082865, 0.589929, 0.519422], "coef": [-0.52962, 0.13361, 0.33795, -0.09513, 0.49596, 0.00798, -0.13641, -0.17301, -0.4709, -0.20199, 0.36036, 0.18389, -0.14987, -0.26813, -0.25844, -0.14606, 0.12557, -0.19048, -0.07164, -0.21964, 0.25122, -0.21036, -0.21086, 0.04303, -0.11644, 0.11229, 0.02582, 0.22408, -0.09502, -0.09881, 0.22273, -0.19956, -0.11668, 0.14085, -0.04702, -0.14086, -0.37221, -0.29124, -0.13249, -0.38408, -0.07878, 0.1035, 0.3114, 0.07987, 0.05918, -0.03385, -0.07007, 0.22915, -0.07225, -0.22828, -0.31927, -0.15059, -0.22009, 0.20528, -0.46477, 0.04413, -0.17713, -0.005, 0.23872, 0.37304, 0.21961, -0.3266, -0.22265, -0.02598, 0.07267, 0.04662, -0.15982, 0.0352, -0.26368, 0.1581, -0.31578, -0.10513, -0.25652, -0.19256, 0.39425, 0.05462, -0.18213, -0.11204, -0.01034, -0.18366, 0.41251, 0.177, 0.16764, 0.25678, 0.31298, -0.11974, -0.60407, 0.01168, 0.33647, -0.34892, 0.0, 0.58291, 0.44668, 0.38564, 0.14549, -0.1274, 0.20474, 0.09729, 0.21831, -0.61753, -0.04931, -0.37543, 0.01135, 0.08145, 0.02796, -0.04003, -0.23107, 0.56887, -0.18165, 0.15472, 0.55773, 0.08431, 0.33161, 0.58113, 0.14319], "intercept": -1.22947, "human_cdf": [[0.0, 0.0], [0.0, 0.025], [0.0002, 0.05], [0.0003, 0.075], [0.0005, 0.1], [0.0007, 0.125], [0.001, 0.15], [0.0014, 0.175], [0.002, 0.2], [0.0027, 0.225], [0.0034, 0.25], [0.004, 0.275], [0.005, 0.3], [0.0061, 0.325], [0.0075, 0.35], [0.0089, 0.375], [0.0103, 0.4], [0.0124, 0.425], [0.0152, 0.45], [0.0196, 0.475], [0.023, 0.5], [0.0298, 0.525], [0.0364, 0.55], [0.0462, 0.575], [0.0553, 0.6], [0.0657, 0.625], [0.0753, 0.65], [0.0914, 0.675], [0.11, 0.7], [0.132, 0.725], [0.1633, 0.75], [0.1939, 0.775], [0.222, 0.8], [0.2632, 0.825], [0.3261, 0.85], [0.4238, 0.875], [0.5158, 0.9], [0.6085, 0.925], [0.7613, 0.95], [0.8799, 0.975], [1.0, 1.0]], "ai_recall_at": {"0.9": 0.794, "0.95": 0.687, "0.99": 0.494}, "n": {"human": 1296, "ai": 713}},
}
# END STYLE MODEL

_FEATURE_TEXT = {
    # feature: ((es high, es low), (en high, en low)); only directions a writer can act on.
    "sent_cv": (("el largo de las oraciones varía mucho", "las oraciones tienen largos muy parecidos"),
                ("sentence length varies a lot", "sentences are all about the same length")),
    "sent_long": (("hay muchas oraciones largas", "casi no hay oraciones largas"),
                  ("many long sentences", "almost no long sentences")),
    "sent_short": (("abundan las frases muy cortas", "casi no hay frases cortas"),
                   ("many very short sentences", "almost no short sentences")),
    "sent_mean": (("las oraciones son largas en promedio", "las oraciones son cortas en promedio"),
                  ("sentences are long on average", "sentences are short on average")),
    "caps_mid": (("hay muchos nombres propios", "casi no aparecen nombres propios: el texto habla en general"),
                 ("many proper names", "almost no proper names: the text stays general")),
    "digits": (("hay muchas cifras y fechas", "casi no hay cifras, fechas ni datos concretos"),
               ("many figures and dates", "almost no figures, dates or concrete data")),
    "first_word_div": (("las oraciones empiezan de formas variadas", "muchas oraciones empiezan con las mismas palabras"),
                       ("sentences open in varied ways", "many sentences open with the same words")),
    "ttr300": (("vocabulario muy variado", "vocabulario repetitivo"), ("very varied vocabulary", "repetitive vocabulary")),
    "word_len": (("palabras largas y abstractas", "palabras cortas"), ("long, abstract words", "short words")),
    "exclaim": (("muchas exclamaciones", "ninguna exclamación"), ("many exclamation marks", "no exclamation marks")),
    "question": (("muchas preguntas", "casi ninguna pregunta"), ("many questions", "almost no questions")),
    "paren": (("muchos paréntesis", "casi ningún paréntesis"), ("many parentheses", "almost no parentheses")),
    "quote": (("muchas citas textuales", "casi ninguna cita textual"), ("many direct quotes", "almost no direct quotes")),
    "comma": (("muchas comas", "pocas comas"), ("many commas", "few commas")),
    "colon": (("muchos dos puntos", "pocos dos puntos"), ("many colons", "few colons")),
    "dash": (("muchas rayas o guiones de inciso", "pocas rayas de inciso"), ("many dashes", "few dashes")),
    "sfx_nominal": (("muchos sustantivos abstractos (-ción, -miento)", "pocos sustantivos abstractos"),
                    ("many abstract nouns (-tion, -ment)", "few abstract nouns")),
    "sfx_adverb": (("muchos adverbios en -mente", "pocos adverbios en -mente"), ("many -ly adverbs", "few -ly adverbs")),
    "sfx_gerund": (("muchos gerundios", "pocos gerundios"), ("many -ing forms", "few -ing forms")),
    "conj_start": (("oraciones que arrancan con «y» o «pero», como al hablar", "casi ninguna oración arranca con «y» o «pero»"),
                   ("sentences that open with “and” or “but”, like speech", "almost no sentence opens with “and” or “but”")),
    "contraction": (("muchas contracciones", "casi ninguna contracción"), ("many contractions", "almost no contractions")),
    "hits3": (("varias frases hechas de IA", "sin frases hechas fuertes"), ("several stock AI phrases", "no strong stock phrases")),
    "hits2": (("frases de plantilla", "pocas frases de plantilla"), ("template phrases", "few template phrases")),
}


def _style_model(features: dict[str, float], lang: str) -> tuple[float, list[str]] | None:
    """Trained logistic combiner over the explainable features. Returns the
    probability-like score and the strongest reasons that pushed it up."""
    m = _STYLE_MODEL.get(lang)
    if not m:
        return None
    contrib = []
    logit = m["intercept"]
    for k, mu, sd, c in zip(m["keys"], m["mean"], m["scale"], m["coef"]):
        z = (features.get(k, 0.0) - mu) / sd
        z = max(-4.0, min(4.0, z))  # one outlier (a table, a list of numbers) cannot decide alone
        logit += c * z
        contrib.append((c * z, k, z))
    p = 1.0 / (1.0 + math.exp(-logit))
    es = lang == "es"
    reasons = []
    # Function words weigh in the score but are not listed: "uses «la» more"
    # gives a writer nothing to act on.
    for value, k, z in sorted(contrib, reverse=True):
        if value < 0.25 or len(reasons) == 4:
            break
        if k in _FEATURE_TEXT:
            reasons.append(_FEATURE_TEXT[k][0 if es else 1][0 if z > 0 else 1])
    return p, reasons


CONTEXT_NAMES = {
    "fiction": ("relato", "story"), "academic": ("texto académico", "academic text"),
    "info": ("texto informativo", "informative text"), "web": ("texto personal o de opinión", "personal or opinion text"),
}


def _context(features: dict[str, float], lang: str) -> str | None:
    """Kind of text (story, academic, informative, personal/opinion) from the same
    standardized features; used to compare against human texts of that kind."""
    m = _STYLE_MODEL.get(lang)
    if not m or "genre" not in m:
        return None
    z = [max(-4.0, min(4.0, (features.get(k, 0.0) - mu) / sd)) for k, mu, sd in zip(m["keys"], m["mean"], m["scale"])]
    g = m["genre"]
    scores = [b + sum(c * x for c, x in zip(row, z)) for row, b in zip(g["coef"], g["intercept"])]
    return g["classes"][scores.index(max(scores))]


def _human_exceed(p: float, lang: str, context: str | None = None) -> float | None:
    """Share of human reference texts (of the same kind when known) scoring above p."""
    m = _STYLE_MODEL.get(lang)
    if not m:
        return None
    qs = m.get("human_cdf_by_genre", {}).get(context) or m["human_cdf"]  # [(score, share_at_or_below)]
    if p <= qs[0][0]:
        return 1.0 - qs[0][1]
    for (s0, c0), (s1, c1) in zip(qs, qs[1:]):
        if p <= s1:
            return 1.0 - (c0 + (c1 - c0) * (p - s0) / max(s1 - s0, 1e-9))
    return 1.0 - qs[-1][1]


def _check_statistical_uniformity(stats: dict[str, float | int], lang: str) -> list[StructuralFinding]:
    """Flag a cluster of weak statistical tells, never one metric alone."""
    if stats.get("word_count", 0) < 80 or stats.get("sentence_count", 0) < 8:
        return []
    signals: list[str] = []
    burstiness = float(stats.get("burstiness", 0))
    ttr = float(stats.get("type_token_ratio", 0))
    trigram_repetition = float(stats.get("trigram_repetition", 0))
    if burstiness < 0.30:
        signals.append("ritmo parejo" if lang == "es" else "flat rhythm")
    if ttr < 0.48:
        signals.append("variedad léxica baja" if lang == "es" else "low lexical variety")
    if trigram_repetition > 0.035:
        signals.append("trigramas repetidos" if lang == "es" else "repeated trigrams")
    if len(signals) < 2:
        return []
    return [StructuralFinding(
        line=0,
        kind="statistical-uniformity",
        severity=2,
        message=(
            "varias métricas de regularidad apuntan a una prosa demasiado pareja: "
            + ", ".join(signals)
            if lang == "es" else
            "several regularity metrics point to unusually uniform prose: "
            + ", ".join(signals)
        ),
        suggestion=(
            "mezcla longitudes, evita repetir la misma construcción y aterriza una idea con un detalle concreto"
            if lang == "es" else
            "vary sentence lengths, avoid repeating the same construction, and ground one idea in a concrete detail"
        ),
    )]


def _check_narrator_distance(sentences: list[str], lang: str) -> list[StructuralFinding]:
    """Detect lecturer-from-a-distance phrasing only in a cluster."""
    if lang == "es":
        patterns = [
            r"\bnadie\s+(?:diseñó|decidió|planeó|pensó)\b",
            r"\beste\s+\w+\s+ocurre\s+porque\b",
            r"\bla\s+gente\s+(?:tiende|suele)\s+a\b",
            r"\blas?\s+personas\s+(?:tienden|suelen)\s+a\b",
        ]
        message = "narrador distante: generaliza sobre la gente en vez de nombrar al actor"
        suggestion = "di quién actuó o qué caso concreto sostiene la afirmación"
    else:
        patterns = [
            r"\bnobody\s+(?:designed|decided|planned|thought)\b",
            r"\bthis\s+\w+\s+happens\s+because\b",
            r"\bpeople\s+(?:tend|tends)\s+to\b",
            r"\bpeople\s+usually\b",
        ]
        message = "distant narrator: it generalizes about people instead of naming the actor"
        suggestion = "name who acted or give the concrete case supporting the claim"
    matched = {index for index, sentence in enumerate(sentences) if any(re.search(pattern, sentence, re.I) for pattern in patterns)}
    if len(matched) < 2:
        return []
    return [StructuralFinding(
        line=0,
        kind="narrator-distance",
        severity=2,
        message=f"{len(matched)} señales: {message}" if lang == "es" else f"{len(matched)} signals: {message}",
        suggestion=suggestion,
    )]


def _check_lazy_extremes(text: str, lang: str) -> list[StructuralFinding]:
    """Flag stacked absolutes, not a single ordinary 'always' or 'nunca'."""
    if lang == "es":
        terms = ["siempre", "nunca", "todos", "todas", "nadie", "ningún", "ninguna", "jamás"]
        message = "absolutos acumulados: autoridad sin evidencia concreta"
        suggestion = "cambia los absolutos por una frecuencia, un grupo o un caso verificable"
    else:
        terms = ["always", "never", "everyone", "nobody", "no one", "every"]
        message = "stacked absolutes: authority without concrete evidence"
        suggestion = "replace absolutes with a frequency, a group, or a verifiable case"
    rx = re.compile(r"\b(?:" + "|".join(re.escape(term) for term in terms) + r")\b", re.I)
    matches = [m.group(0).lower() for m in rx.finditer(text)]
    if len(matches) < 4 or len(set(matches)) < 3:
        return []
    return [StructuralFinding(
        line=0,
        kind="lazy-extremes",
        severity=1,
        message=f"{len(matches)} {message}",
        suggestion=suggestion,
    )]


# ---- humanizer v2.9.1 + stop-slop gaps (2026-08) ----
# Curated lists, deliberately shorter than stop-slop's absolutist ban:
# the tell is density, not a single occurrence.

_AI_ADVERBS_EN = [
    "literally", "genuinely", "honestly", "simply", "actually", "truly",
    "fundamentally", "inherently", "inevitably", "interestingly",
    "importantly", "crucially",
]
_AI_ADVERBS_ES = [
    "verdaderamente", "fundamentalmente", "genuinamente", "inherentemente",
    "inevitablemente", "crucialmente", "interesantemente",
]
_CORPORATE_HYPHENATED = [
    "third-party", "cross-functional", "client-facing", "data-driven",
    "decision-making", "well-known", "high-quality", "real-time",
    "long-term", "end-to-end", "cutting-edge", "state-of-the-art",
]
_TAILING_NEGATIONS = [
    "no guessing", "no wasted motion", "no questions asked",
    "no exceptions", "no regrets", "no fuss", "no drama",
    "no second-guessing", "no excuses",
]
_EMOJI_RX = re.compile(r"[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F]")


def _check_synthetic_academic_texture(text: str, lang: str) -> list[StructuralFinding]:
    """Catch cleaned-up AI academic Spanish: abstract, smooth, correct, unanchored."""
    if lang != "es":
        return []
    words = _word_count(text)
    if words < 80:
        return []

    abstraction_hits = len(_SYNTHETIC_ACADEMIC_ES.findall(text))
    weak_verbs = len(_WEAK_ABSTRACT_VERBS_ES.findall(text))
    density = abstraction_hits / max(words, 1)
    if abstraction_hits < 12 or weak_verbs < 4 or density < 0.08:
        return []

    return [StructuralFinding(
        line=0,
        kind="synthetic-academic",
        severity=2,
        message=(
            f"textura académica sintética: {abstraction_hits} abstracciones y "
            f"{weak_verbs} verbos débiles en {words} palabras"
        ),
        suggestion=(
            "baja la abstracción: agrega casos, decisiones, nombres, datos o una postura con filo"
        ),
    )]


def _check_low_specificity(text: str, lang: str) -> list[StructuralFinding]:
    """Flag long, polished abstraction with almost no concrete anchors."""
    words = _word_count(text)
    if words < 80:
        return []
    anchors = len(_CONCRETE_ANCHORS.findall(text))
    abstraction_hits = len(_SYNTHETIC_ACADEMIC_ES.findall(text)) if lang == "es" else 0
    if anchors <= 1 and abstraction_hits >= 10:
        return [StructuralFinding(
            line=0,
            kind="low-specificity",
            severity=2,
            message=(
                f"baja especificidad: {anchors} anclas concretas frente a "
                f"{abstraction_hits} abstracciones"
                if lang == "es" else
                f"low specificity: {anchors} concrete anchors"
            ),
            suggestion=(
                "agrega evidencia verificable: nombres, fechas, cifras, escenas o ejemplos no genéricos"
                if lang == "es" else
                "add verifiable evidence: names, dates, numbers, scenes, or non-generic examples"
            ),
        )]
    return []


def _check_vague_sentence_stack(sentences: list[str], lang: str) -> list[StructuralFinding]:
    """Look at whole sentences: repeated abstract claim shape, not isolated words."""
    if lang != "es" or len(sentences) < 3:
        return []
    vague = 0
    for s in sentences:
        words = _word_count(s)
        if words < 8:
            continue
        abstract_terms = len(_SYNTHETIC_ACADEMIC_ES.findall(s))
        weak_verbs = len(_WEAK_ABSTRACT_VERBS_ES.findall(s))
        anchors = len(_CONCRETE_ANCHORS.findall(s))
        if abstract_terms >= 3 and weak_verbs >= 1 and anchors == 0:
            vague += 1
    if vague >= 3:
        return [StructuralFinding(
            line=0,
            kind="vague-sentence-stack",
            severity=2,
            message=f"{vague} frases completas hacen afirmaciones abstractas sin anclas concretas",
            suggestion="aterriza esas frases: agrega un caso, una cita, una fecha, un actor o una consecuencia verificable por cada afirmación abstracta",
        )]
    return []


# --- LLM-essay scaffolding: meta-announce + enumeration + dramatic close ---
_ESSAY_META_ANNOUNCE = re.compile(
    r"(?i)\b(el\s+presente\s+(ensayo|trabajo|texto|artículo|análisis|capítulo)|"
    r"este\s+(ensayo|trabajo|texto|artículo|análisis|capítulo)\s+(recorre|aborda|revisa|examina|propone|sostiene|argumenta|explora))\b"
)
_ESSAY_ENUMERATION = re.compile(
    r"(?i)\b(tres|cuatro|cinco|seis)\s+(ejes|principios|pilares|aspectos|dimensiones|razones|elementos|factores|cuestiones|puntos|niveles|caminos|vías|claves)\b"
)
_ESSAY_FIRST_SECOND = re.compile(
    r"(?i)\bprimero,\b.{1,400}\bsegundo,\b", re.DOTALL,
)
_ESSAY_FOLLOWING_AUTHOR = re.compile(
    r"(?i)\bsiguiendo\s+a\s+[A-ZÁÉÍÓÚÑ]\w+"
)
_ESSAY_DRAMATIC_CLOSE = re.compile(
    r"(?i)\b(ese|este|el|aquel)\s+(debate|tema|asunto|problema|dilema|paradoja)\s+(sigue|permanece|continúa|queda)\s+(muy\s+)?(abierto|vigente|sin\s+resolverse|en\s+pie)\b|"
    r"\blo\s+que\s+(enseña|muestra|deja\s+ver|revela|sugiere|indica|importa|recuerda)\b.{1,40}\bes\s+que\b"
)


def _check_essay_scaffolding(text: str, lang: str) -> list[StructuralFinding]:
    """Detect the unmistakable LLM essay shape:
    meta-announce + numbered scaffold + impersonal voice + dramatic close.
    When 3+ of these coexist, the text is almost certainly LLM."""
    if lang != "es":
        return []
    signals = []
    if _ESSAY_META_ANNOUNCE.search(text):
        signals.append("meta-anuncio del ensayo")
    if _ESSAY_ENUMERATION.search(text):
        signals.append("enumeración numerada")
    if _ESSAY_FIRST_SECOND.search(text):
        signals.append("estructura primero/segundo")
    if _ESSAY_FOLLOWING_AUTHOR.search(text):
        signals.append("'siguiendo a X'")
    if _ESSAY_DRAMATIC_CLOSE.search(text):
        signals.append("cierre dramático pop-essay")
    if len(signals) < 3:
        return []
    return [StructuralFinding(
        line=0,
        kind="essay-scaffolding",
        severity=3,
        message=f"andamiaje completo de ensayo IA: {', '.join(signals)}",
        suggestion="rompe el molde: empieza con un dato, una cita, una escena o una tensión concreta; evita anunciar primero el plan del ensayo",
    )]


def _check_negative_parallelism_density(sentences: list[str], lang: str) -> list[StructuralFinding]:
    """Wikipedia: LLMs overuse 'Not X, but Y' negative parallelisms."""
    if lang == "es":
        rx = re.compile(
            r"(?i)(\bno (solo|sólo|únicamente|meramente|simplemente)\b.{1,100}\bsino\b"
            r"|\ba pesar de (estos|los|sus|estas) (desafíos|retos|dificultades|obstáculos)\b"
            r"|\bno (es|son)\b.{1,80}\bsino\b)",
        )
        msg = "densidad alta de paralelismos negativos — patrón IA (Wikipedia)"
        suggestion = "afirma la idea positiva directa sin la negación previa"
    else:
        rx = re.compile(
            r"(?i)(\bnot (only|just|merely|simply|solely)\b.{1,100}\bbut (also|rather|instead)?\b"
            r"|\bdespite (these|its|the|this) (challenges|difficulties|obstacles|limitations)\b"
            r"|\bnot (just|merely|simply) .{1,80}\bit'?s\b)",
        )
        msg = "high density of negative parallelisms — Wikipedia-confirmed AI pattern"
        suggestion = "assert the positive idea directly without the negation preamble"
    hits = sum(1 for s in sentences if rx.search(s))
    if hits >= 2:
        sev = 3 if hits >= 3 else 2
        return [StructuralFinding(
            line=0, kind="negative-parallelism", severity=sev,
            message=f"{hits} casos: {msg}", suggestion=suggestion,
        )]
    return []


def _check_challenges_template(text: str, lang: str) -> list[StructuralFinding]:
    """Wikipedia: 'Despite X, Y faces challenges' formulaic AI essay structure."""
    if lang == "es":
        rx = re.compile(
            r"(?i)(a pesar de|no obstante).{0,60}(desafíos|retos|dificultades)"
            r".{0,120}(continúa|sigue|permanece|avanza|prospera)",
            re.DOTALL,
        )
        header_rx = re.compile(
            r"(?im)^(#{1,4}\s+)?(desafíos?\s+y\s+(perspectivas|futuro|oportunidades)"
            r"|perspectivas?\s+futuras?|retos?\s+y\s+(oportunidades|futuro))",
        )
        msg = "fórmula 'a pesar de los desafíos' — plantilla IA (Wikipedia)"
        suggestion = "di lo que funciona y lo que no sin la fórmula positiva al final"
    else:
        rx = re.compile(
            r"(?i)(despite|however).{0,60}(challenges|difficulties|obstacles)"
            r".{0,120}(continues?|remains?|thrives?|evolves?|advances?)",
            re.DOTALL,
        )
        header_rx = re.compile(
            r"(?im)^(#{1,4}\s+)?(challenges\s+and\s+(future|legacy|opportunities|prospects)"
            r"|future\s+(directions?|outlook|prospects?))",
        )
        msg = "'Despite challenges' formula — Wikipedia AI essay template"
        suggestion = "state what works and what doesn't without the optimistic formula"
    signals = []
    if rx.search(text):
        signals.append("negativa→positiva" if lang == "es" else "negative→positive")
    if header_rx.search(text):
        signals.append("encabezado tipo ensayo" if lang == "es" else "essay-style section header")
    if signals:
        sev = 3 if len(signals) >= 2 else 2
        return [StructuralFinding(
            line=0, kind="challenges-template", severity=sev,
            message=f"{msg}: {', '.join(signals)}", suggestion=suggestion,
        )]
    return []


def _check_media_notability_padding(text: str, lang: str) -> list[StructuralFinding]:
    """Wikipedia: LLMs assert notability via media coverage lists instead of content."""
    if lang == "es":
        rx = re.compile(
            r"(?i)(ha sido (perfilad[oa]|cubierto|mencionad[oa]) en.{0,40}(medios|prensa)"
            r"|presencia (activa|destacada|fuerte) en (redes sociales|línea|internet)"
            r"|cobertura (nacional|internacional|mediática))",
        )
        msg = "relleno de notabilidad mediática — patrón IA (Wikipedia)"
        suggestion = "cita la fuente directa; no anuncies que fue cubierto"
    else:
        rx = re.compile(
            r"(?i)((has been|was) (profiled|featured|covered) in.{0,40}(media|outlets)"
            r"|maintains? an active (social media|online|digital) presence"
            r"|(national|international) (coverage|media|press))",
        )
        msg = "media notability padding — Wikipedia AI pattern"
        suggestion = "cite the source directly; don't announce that coverage happened"
    hits = len(rx.findall(text))
    if hits >= 2:
        sev = 3 if hits >= 3 else 2
        return [StructuralFinding(
            line=0, kind="media-notability", severity=sev,
            message=f"{hits} {'patrones' if lang == 'es' else 'patterns'}: {msg}",
            suggestion=suggestion,
        )]
    return []


def _check_ai_artifact_markup(text: str, lang: str) -> list[StructuralFinding]:
    """Wikipedia: Detect ChatGPT/Gemini/Grok/Perplexity citation artifacts in text."""
    artifacts = [
        (r":?contentReference\[oaicite:\d+\]", "contentReference[oaicite:N]"),
        (r"oai_citation:\d+", "oai_citation:N"),
        (r"【\d+†", "【N† (DeepSeek)"),
        (r"turn0(?:search|image|news|file)\d+", "turn0searchN (ChatGPT)"),
        (r"\[attached_file:\d+\]", "[attached_file:N]"),
        (r"\[cite:\s*\d+[,\s\d]*\]", "[cite:N] (Gemini)"),
        (r"<grok.?card", "<grok_card (Grok)"),
        (r"grok_render_citation_card_json", "grok_render_citation_card_json"),
        (r":::writing\{variant", ":::writing{variant"),
        (r'\{"attribution":\{"attributableIndex"', '{"attribution"} (ChatGPT)'),
    ]
    found = [label for rx, label in artifacts if re.search(rx, text)]
    if found:
        return [StructuralFinding(
            line=0, kind="ai-artifact-markup", severity=3,
            message=(
                f"artefacto de chatbot IA en texto: {', '.join(found)}"
                if lang == "es" else
                f"AI chatbot artifact in text: {', '.join(found)}"
            ),
            suggestion=(
                "reemplaza con citas reales o elimina el artefacto"
                if lang == "es" else
                "replace with proper citations or delete the artifact"
            ),
        )]
    return []


def _check_rule_of_three_density(sentences: list[str], lang: str) -> list[StructuralFinding]:
    """Wikipedia: LLMs overuse the rule of three — flag when it appears in many sentences."""
    pattern = re.compile(
        r"\b\w[\w'-]+,\s+\w[\w'-]+,\s+(?:and|or|y|e|o|ni)\s+\w[\w'-]+\b",
        re.IGNORECASE,
    )
    triples = sum(1 for s in sentences if pattern.search(s))
    if triples >= 4:
        sev = 3 if triples >= 6 else 2
        return [StructuralFinding(
            line=0, kind="rule-of-three",  severity=sev,
            message=(
                f"{triples} oraciones con regla de tres — abuso IA (Wikipedia)"
                if lang == "es" else
                f"{triples} sentences with rule of three — Wikipedia AI overuse"
            ),
            suggestion=(
                "rompe el patrón: usa dos items o cuatro, no siempre tres"
                if lang == "es" else
                "break the pattern: use two or four items, not always three"
            ),
        )]
    return []


def _sentence_score(sentence: str, lang: str, role: str) -> tuple[float, list[str]]:
    reasons: list[str] = []
    score = 0.0
    abstract_terms = len(_SYNTHETIC_ACADEMIC_ES.findall(sentence)) if lang == "es" else 0
    weak_verbs = len(_WEAK_ABSTRACT_VERBS_ES.findall(sentence)) if lang == "es" else 0
    anchors = len(_CONCRETE_ANCHORS.findall(sentence))
    words = max(_word_count(sentence), 1)
    if abstract_terms >= 3 and weak_verbs >= 1 and anchors == 0:
        score += 0.28
        reasons.append("frase abstracta sin anclaje concreto")
    if abstract_terms / words >= 0.18 and words >= 10:
        score += 0.18
        reasons.append("alta densidad de abstracciones")
    if role == "cierre" and re.search(r"\b(de este modo|en conclusión|en síntesis|en resumen|finalmente)\b", sentence, re.I):
        score += 0.16
        reasons.append("cierre formulario")
    return min(1.0, score), reasons


# ---- Deep Technical Analysis (June 2026) structural signals ----

def _check_semicolon_ratio(text: str, lang: str) -> list[StructuralFinding]:
    """Machine text overuses semicolons (lexical cohesion crutch)."""
    if lang == "es":
        return []  # semicolons are rare in Spanish, not a reliable signal
    sentences = split_sentences(text)
    if len(sentences) < 5:
        return []
    period_count = text.count(".")
    semicolon_count = text.count(";")
    if period_count == 0:
        return []
    ratio = semicolon_count / max(period_count, 1)
    # Human EN: ~0.02-0.06 semicolons per period. Machine: >0.15
    if ratio > 0.15:
        return [StructuralFinding(
            line=0,
            kind="semicolon_overuse",
            severity=2,
            message=f"semicolon-per-period ratio high ({ratio:.2f}) — lexical cohesion crutch typical of machine text",
            suggestion="replace semicolons with periods or restructuring",
        )]
    return []


def _check_nominalization_density(text: str, lang: str) -> list[StructuralFinding]:
    """Flag high nominalization density (nominalized verbs replace active verbs).

    Spanish calibration: -ción/-sión/-miento/-dad endings.
    Machine ES: 12-18 per 1000 words. Human ES: 5-10."""
    words = [w for w in text.split() if re.match(r'[\wáéíóúüñÁÉÍÓÚÜÑ]', w)]
    total_words = len(words)
    if total_words < 50:
        return []
    if lang == "es":
        nominalizations = [w for w in words if re.search(r'ción|siones|mientos?|dades?|bilidad', w, re.I)]
        density = len(nominalizations) / (total_words / 1000)
        if density > 16:
            return [StructuralFinding(
                line=0,
                kind="nominalization_density",
                severity=2,
                message=f"densidad de nominalizaciones alta ({density:.0f}/1K palabras) — IA: 12-18, humano: 5-10",
                suggestion="sustituye nominalizaciones en -ción/-miento con verbos activos",
            )]
        return []
    else:
        nominalizations = [w for w in words if re.search(r'tion|ment|ness|ity|ance|ence', w, re.I)]
        density = len(nominalizations) / (total_words / 1000)
        if density > 14:
            return [StructuralFinding(
                line=0,
                kind="nominalization_density",
                severity=2,
                message=f"nominalization density high ({density:.0f}/1K words) — machine: 10-16, human: 4-8",
                suggestion="replace -tion/-ment/-ness nouns with active verbs",
            )]
        return []


_IMPERSONAL_SE_ES = re.compile(
    r"\bse\s+(?:puede|pueden|debe|deben|observa|observan|considera|consideran|"
    r"recomienda|sugiere|espera|requiere|requieren|necesita|busca|trata|plantea|"
    r"propone|destaca|evidencia|aprecia|establece|identifica|identificaron|"
    r"analiza|analizan|presenta|presentan|concluye|entiende|define|logra|"
    r"obtiene|obtuvieron|realiza|realizan|realizó|llevó\s+a\s+cabo)\b",
    re.I,
)


def _check_impersonal_se_stacking(text: str, lang: str) -> list[StructuralFinding]:
    """Three or more close co-occurrences of impersonal 'se' within 200 chars
    indicate passive-voice stacking typical of machine-generated Spanish."""
    if lang != "es":
        return []
    # Reflexive narrative verbs ("se sentó", "se apagó") are not impersonal.
    positions = [m.start() for m in re.finditer(_IMPERSONAL_SE_ES, text)]
    if len(positions) < 3:
        return []
    # check if any 3 positions fall within 200 chars of each other
    for i in range(len(positions) - 2):
        if positions[i + 2] - positions[i] <= 200:
            return [StructuralFinding(
                line=0,
                kind="impersonal_se",
                severity=2,
                message="apilamiento de 'se' impersonal: alta densidad de pasiva refleja típica de texto IA",
                suggestion="convierte algunas oraciones pasivas a voz activa",
            )]
    return []


def _check_storyscope_discourse(text: str, lang: str) -> list[StructuralFinding]:
    """StoryScope-inspired discourse signals.

    This is not a narrative classifier. It adds small, auditable proxies for
    StoryScope's product lesson: AI prose often over-explains its theme and
    resolves conflicts too neatly. These are editorial cues, not forensic proof.
    """
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if _word_count(p) >= 15]
    if len(paragraphs) < 4:
        return []

    if lang == "es":
        theme_rx = re.compile(
            r"\b(tema|temas|moral|moraleja|lecci[oó]n|enseñanza|significado|"
            r"sentido profundo|reflexi[oó]n|comprendi[oó]|comprender|aprendi[oó]|"
            r"aprendizaje|verdad profunda|prop[oó]sito|humanidad|esperanza|redenci[oó]n)\b",
            re.I,
        )
        narrator_moral_rx = re.compile(
            r"\b(la historia (?:nos )?(?:enseña|recuerda|muestra)|"
            r"esto (?:nos )?(?:enseña|recuerda|muestra)|"
            r"al final,? (?:comprendi[oó]|aprendi[oó])|en (?:el )?fondo|m[aá]s all[aá] de)\b",
            re.I,
        )
        tidy_close_rx = re.compile(
            r"\b(al final|finalmente|en [uú]ltima instancia|en definitiva|desde ese momento|"
            r"para siempre|comprendi[oó] que|aprendi[oó] que|lo que realmente importaba|"
            r"un nuevo comienzo)\b",
            re.I,
        )
    else:
        theme_rx = re.compile(
            r"\b(theme|themes|moral|lesson|meaning|deeper meaning|reflection|realized|"
            r"understood|learned|truth|purpose|humanity|hope|redemption)\b",
            re.I,
        )
        narrator_moral_rx = re.compile(
            r"\b(the story (?:teaches|reminds|shows)|this (?:teaches|reminds|shows) us|"
            r"in the end,? (?:he|she|they|i) (?:realized|understood|learned)|deep down|beyond the)\b",
            re.I,
        )
        tidy_close_rx = re.compile(
            r"\b(in the end|ultimately|finally|from that day forward|forever changed|"
            r"realized that|learned that|what truly mattered|new beginning)\b",
            re.I,
        )

    findings: list[StructuralFinding] = []
    words = max(1, _word_count(text))
    theme_hits = len(theme_rx.findall(text)) + len(narrator_moral_rx.findall(text)) * 2
    theme_density = theme_hits / (words / 1000)
    if theme_hits >= 5 and theme_density >= 8:
        findings.append(StructuralFinding(
            line=0,
            kind="discourse-overexplained-theme",
            severity=3 if theme_hits >= 9 else 2,
            message=(
                f"el texto explica su tema demasiadas veces ({theme_hits} marcas) — "
                "StoryScope: la IA suele moralizar y cerrar el sentido"
                if lang == "es" else
                f"the text explains its theme too often ({theme_hits} marks) — "
                "StoryScope: AI tends to moralize and close meaning down"
            ),
            suggestion=(
                "borra una explicación del tema y reemplázala por una escena, un gesto, una contradicción o un detalle que deje inferir la idea"
                if lang == "es" else
                "delete one explanation of the theme and replace it with a scene, gesture, contradiction, or detail that lets the idea be inferred"
            ),
        ))

    tidy_close_hits = len(tidy_close_rx.findall(paragraphs[-1]))
    if tidy_close_hits >= 2:
        findings.append(StructuralFinding(
            line=0,
            kind="discourse-tidy-resolution",
            severity=2,
            message=(
                f"cierre demasiado ordenado ({tidy_close_hits} marcas) — resolución de IA muy prolija"
                if lang == "es" else
                f"overly tidy ending ({tidy_close_hits} marks) — AI-style neat resolution"
            ),
            suggestion=(
                "quita la frase que explica la lección y termina con una consecuencia concreta o una duda que no quede totalmente resuelta"
                if lang == "es" else
                "remove the sentence explaining the lesson and end with a concrete consequence or a question that stays partly unresolved"
            ),
        ))
    return findings


# ---- humanizer v2.9.1 §26/§29/§31/§33 + stop-slop adverb/drama gaps (2026-08) ----


def _check_staccato_runs(sentences: list[str], lang: str) -> list[StructuralFinding]:
    """humanizer §31 / stop-slop dramatic fragmentation.

    3+ consecutive very short sentences (≤5 words) read as manufactured
    punchlines. One clipped sentence is human; a run is engineered.
    """
    if len(sentences) < 4:
        return []
    run = 0
    max_run = 0
    for s in sentences:
        if len(s.split()) <= 5:
            run += 1
            max_run = max(max_run, run)
        else:
            run = 0
    if max_run < 3:
        return []
    return [StructuralFinding(
        line=0,
        kind="staccato-runs",
        severity=2,
        message=(
            f"{max_run} oraciones cortas seguidas (≤5 palabras) — drama staccato fabricado"
            if lang == "es" else
            f"{max_run} consecutive very short sentences (≤5 words) — manufactured staccato drama"
        ),
        suggestion=(
            "funde los fragmentos en una sola oración o varía la longitud; una frase enfática basta"
            if lang == "es" else
            "merge the fragments into one sentence or vary the length; one emphatic sentence is enough"
        ),
    )]


# ---- Pangram per-10k-word rates ----
# Human vs AI occurrences per 10,000 words measured by Pangram
# (pangram.com/signs-of-ai-writing, English corpus). Display context only:
# the index already scores these signals through its own findings.
PANGRAM_BASELINES = {
    "markdown": (8, 90),
    "ai_phrases": (3, 30),
    "em_dashes": (2, 17),
    "bullets": (3, 28),
    "triads": (5, 19),
    "not_just": (1, 3),
    "unicode": (28, 71),
}
_MARKDOWN_RX = re.compile(r"\*\*[^*\n]+\*\*|(?<![*\w])\*[^*\s][^*\n]*\*(?![*\w])|^#{1,6}\s", re.M)
_TRIAD_RX = re.compile(r"\b\w[\w'-]+,\s+\w[\w'-]+,?\s+(?:and|or|y|e|o|ni)\s+\w[\w'-]+\b", re.I)
_NOT_JUST_RX = re.compile(
    r"\bnot (?:only|just|merely|simply)\b.{1,100}?\bbut\b|\bno (?:solo|sólo|solamente|únicamente|simplemente)\b.{1,100}?\bsino\b", re.I,
)
# Typographic symbols and invisible characters people rarely type by hand.
_UNUSUAL_UNICODE_RX = re.compile("[\u200b-\u200f\u202a-\u202e\u2060-\u2064\ufeff\u00a0\u2009\u202f≈→←↔⇒✓✔✗★•≥≤×]")


def _pangram_rates(text: str, lexical_hits: int) -> dict[str, dict[str, float]]:
    words = _word_count(text)
    if words < 50:
        return {}
    narration = "\n".join(ln for ln in text.splitlines() if not ln.lstrip().startswith(("—", "–")))
    counts = {
        "markdown": len(_MARKDOWN_RX.findall(text)),
        "ai_phrases": lexical_hits,
        "em_dashes": narration.count("—"),
        "bullets": sum(1 for ln in text.splitlines() if re.match(r"\s*(?:[-*•]|\d+[.)])\s+\S", ln)),
        "triads": len(_TRIAD_RX.findall(text)),
        "not_just": len(_NOT_JUST_RX.findall(text)),
        "unicode": len(_UNUSUAL_UNICODE_RX.findall(text)),
    }
    out = {}
    for key, count in counts.items():
        human, ai = PANGRAM_BASELINES[key]
        out[key] = {"count": count, "per10k": round(count * 10000 / words, 1), "human": human, "ai": ai}
    return out


_EXPANDED_RX = re.compile(r"\b(?:do not|does not|did not|is not|are not|was not|cannot|would not|will not|have not|it is|i am|you are|we are|they are)\b", re.I)
_CONTRACTION_RX = re.compile(r"\b\w+(?:n't|'re|'s|'m|'ll|'ve|'d|n’t|’re|’s|’m|’ll|’ve|’d)\b", re.I)


def _check_contraction_deficit(text: str, lang: str) -> list[StructuralFinding]:
    """Modern English prose mixes contractions in; default AI register avoids them.

    A single "is not" means nothing, so this is a ratio over the whole text.
    """
    if lang != "en" or _word_count(text) < 250:
        return []
    expanded = len(_EXPANDED_RX.findall(text))
    contracted = len(_CONTRACTION_RX.findall(text))
    if expanded < 6 or contracted > expanded * 0.15:
        return []
    return [StructuralFinding(
        line=0, kind="contraction-deficit", severity=1,
        message=f"{expanded} expanded forms (do not, it is…) and {contracted} contractions — uniformly formal register",
        suggestion="use the contractions you would say aloud, unless the genre is formal on purpose",
        count=expanded,
    )]


_LISTICLE_ITEM_RX = re.compile(r"^\s*(?:#{1,4}\s*)?\d{1,2}[.)]\s+\S[^\n]{2,70}[^.!?:;,\s]\s*$", re.M)
_LISTICLE_TITLE_RX = re.compile(
    r"\b\d{1,2} (?:consejos|claves|pasos|formas|maneras|razones|ideas|trucos|tips|errores|tips|ways|steps|reasons|ideas|tricks|mistakes|secrets|lessons)\b", re.I,
)
_CLOSING_HEADING_RX = re.compile(
    r"^\s*(?:#{1,4}\s*)?(?:conclusión|conclusiones|en resumen|reflexión final|palabras finales|bonus|extra|"
    r"conclusion|final thoughts|in summary|key takeaways|the bottom line|bottom line|wrapping up|bonus tip)\s*:?\s*$", re.I | re.M,
)
# Unnumbered blog headings: a short capitalized line alone between blank lines.
_BARE_HEADING_RX = re.compile(r"(?:^|\n\s*\n)([A-ZÁÉÍÓÚÑ¿][^\n.!?:;,]{2,60})\n\s*\n(?=\S)")


def _check_listicle_scaffold(text: str, lang: str) -> list[StructuralFinding]:
    """Blog-post template: numbered tip headings, a number in the title, a 'Final Thoughts' heading."""
    items = list(_LISTICLE_ITEM_RX.finditer(text))
    if len(items) < 4 and _CLOSING_HEADING_RX.search(text):
        # Headings without numbers count only when the post also ends on a stock heading.
        bare = [m for m in _BARE_HEADING_RX.finditer(text) if len(m.group(1).split()) <= 8][1:]
        if len(bare) >= 4:
            items = bare
    if len(items) < 4:
        return []
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    # Numbered title, a stock closing heading, or a cheering last line ("Happy running!").
    extras = (bool(_LISTICLE_TITLE_RX.search(lines[0])) + bool(_CLOSING_HEADING_RX.search(text))
              + (lines[-1].endswith("!") and len(items) >= 6))
    es = lang == "es"
    return [StructuralFinding(
        line=_line_of(text, items[0].start(items[0].re.groups)), kind="listicle-scaffold", severity=3 if extras else 2,
        message=(f"{len(items)} subtítulos numerados{' con número en el título y cierre «Conclusión»' if extras == 2 else ''}: plantilla de post de blog IA («{items[0].group(items[0].re.groups).strip()[:50]}»)"
                 if es else f"{len(items)} numbered tip headings{' plus a numbered title and a closing heading' if extras == 2 else ''}: AI blog-post template («{items[0].group(items[0].re.groups).strip()[:50]}»)"),
        suggestion=("quédate con los tres consejos que de verdad usas y cuéntalos con un caso propio" if es
                    else "keep the three tips you actually use and tell them through your own case"),
        count=len(items),
    )]


# Chatbot templates leave fill-in slots: "[Your Name]", "[Nombre completo]", "atento/a".
_PLACEHOLDER_RX = re.compile(r"\[(?:[A-ZÁÉÍÓÚÑ][\w'’ÁÉÍÓÚÑáéíóúñ.,:/-]*(?: [\w'’ÁÉÍÓÚÑáéíóúñ.,:/()-]+){0,12})\](?![(\[:])")
_GENDER_SLASH_RX = re.compile(r"\b\w{3,}[oe]/a\b")


def _check_template_placeholders(text: str, lang: str) -> list[StructuralFinding]:
    slots = [m for m in _PLACEHOLDER_RX.finditer(text) if not re.match(r"\[\d+\]", m.group(0))]
    slashes = _GENDER_SLASH_RX.findall(text)
    if len(slots) < 2:
        return []
    first = slots[0]
    es = lang == "es"
    return [StructuralFinding(
        line=_line_of(text, first.start()), kind="template-placeholders", severity=3,
        message=(f"{len(slots)} huecos de plantilla sin llenar{f' y {len(slashes)} formas «o/a»' if slashes else ''} («{first.group(0)[:50]}»)"
                 if es else f"{len(slots)} unfilled template slots («{first.group(0)[:50]}»)"),
        suggestion=("rellena o borra cada hueco: una plantilla de chatbot se reconoce por ellos" if es
                    else "fill in or delete every slot: chatbot templates are recognizable by them"),
        count=len(slots),
    )]


# Pangram: 60-70% of names in ChatGPT/Claude stories are Emily or Sarah.
# One name proves nothing; two defaults in one short text is the pattern.
_DEFAULT_NAMES = {
    "en": r"Emily|Sarah|Elara|Lyra|Clara|Eleanor|Elias|Evelyn|Maya|Mira|Kael|Seraphina|Thorne|Margaret",
    "es": r"Elena|Clara|Lucía|Sofía|Elara|Lyra|Mateo|Valeria|Isabel|Tomás|Gabriel|Martina",
}


def _check_default_names(text: str, lang: str) -> list[StructuralFinding]:
    if lang not in _DEFAULT_NAMES:
        return []
    matches = list(re.finditer(r"\b(" + _DEFAULT_NAMES[lang] + r")\b", text))
    names = sorted({m.group(1) for m in matches})
    if len(names) < 2:
        return []
    es = lang == "es"
    return [StructuralFinding(
        line=_line_of(text, matches[0].start()), kind="default-names", severity=1,
        message=(f"nombres frecuentes en ficción generada: {', '.join(names)} («{matches[0].group(1)}»)" if es
                 else f"names common in generated fiction: {', '.join(names)} («{matches[0].group(1)}»)"),
        suggestion=("elige nombres que digan algo del lugar, la época o la familia" if es
                    else "choose names that say something about place, era or family"),
        count=len(names),
    )]


# ---- narrative fiction tells ----
# Generated short fiction rarely uses essay tics; it repeats a different kit:
# "No es que X. Es que Y", anaphoric fragment ladders, "como si" similes,
# aphorisms and one-line punchline paragraphs. Each is ordinary once; the
# finding needs a cluster and always reports where the first instance is.

_NARRATIVE_RX = {
    "es": {
        "pivot": re.compile(
            r"\bno\s+(?:es|era|fue)\s+que\b[^.!?\n]{1,140}[.!?]\s+(?:es|era|fue)\s+que\b"
            r"|\bno\s+(?:era|es)\s+(?:un|una|el|la)\s+\w+[.!?]\s+(?:era|es)\s+(?:un|una|el|la)\b"
            r"|\bno\s+se\s+trata\s+de\b[^.!?\n]{1,140}[.!?;]\s+se\s+trata\s+de\b",
            re.I,
        ),
        "inline": re.compile(
            r"\b(?P<w>\w{2,})\b[^.!?,;\n]{1,40},\s+(?P=w)\b[^.!?,;\n]{1,40},\s+(?:y\s+)?(?P=w)\b", re.I,
        ),
        "ladder": re.compile(
            r"\b\w+,\s+luego\s+[^,.;\n]{1,25},\s+luego\b|\b(?:luego|después)\s+(?:el|la)\s+(?:segund[oa]|tercer[oa])\b", re.I,
        ),
        "simile": re.compile(r"\bcomo\s+(?:si|quien|cuando)\b|\bde\s+quien\s+\w+", re.I),
        "aphorism": re.compile(
            r"\bhay\s+\w+\s+que\s+uno\b"
            r"|\b(?P<w>\w{4,})\b[^.!?\n]{0,40}\bnunca\s+es\s+(?:un\s+|una\s+)?(?P=w)\b"
            r"|\bcon\s+una\s+(?:claridad|certeza|lucidez|calma|precisi[oó]n|ternura|urgencia|nitidez)\s+que\b",
            re.I,
        ),
    },
    "en": {
        "pivot": re.compile(
            r"\b(?:it['’]?s|it\s+is|it\s+was|this\s+is)\s+not\s+that\b[^.!?\n]{1,140}[.!?]\s+(?:it['’]?s|it\s+is|it\s+was)\s+that\b"
            r"|\bit\s+(?:wasn['’]?t|isn['’]?t)\s+(?:a|an|the)\s+\w+[.!?]\s+it\s+(?:was|is)\s+(?:a|an|the)\b"
            r"|\bit\s+(?:isn['’]?t|is\s+not|wasn['’]?t)\s+about\b[^.!?\n]{1,140}[.!?;]\s+it['’]?s\s+about\b",
            re.I,
        ),
        "inline": re.compile(
            r"\b(?P<w>\w{2,})\b[^.!?,;\n]{1,40},\s+(?P=w)\b[^.!?,;\n]{1,40},\s+(?:and\s+)?(?P=w)\b", re.I,
        ),
        "ladder": re.compile(
            r"\b\w+,\s+then\s+[^,.;\n]{1,25},\s+then\b|\bthen\s+(?:the\s+)?(?:second|third|two|three)\b[.,]", re.I,
        ),
        "simile": re.compile(r"\bas\s+(?:if|though)\b|\blike\s+someone\b|\bthe\s+way\s+someone\b", re.I),
        "aphorism": re.compile(
            r"\bthere\s+are\s+\w+\s+(?:that|which)\s+(?:you|one)\b"
            r"|\b(?P<w>\w{4,})\b[^.!?\n]{0,40}\bis\s+never\s+(?:just\s+)?(?P=w)\b"
            r"|\bwith\s+a\s+(?:clarity|certainty|calm|precision|tenderness|urgency)\s+that\b",
            re.I,
        ),
    },
}
# Articles, pronouns and glue words repeat naturally at sentence starts.
_ANAPHORA_IGNORE = {
    "el", "la", "los", "las", "un", "una", "de", "en", "y", "e", "o", "a", "yo", "él", "ella", "me", "mi", "se", "lo", "le",
    "the", "an", "and", "of", "in", "to", "i", "he", "she", "it", "they", "we", "my", "his", "her",
}
NARRATIVE_KINDS = {
    "narrative-pivot", "narrative-cadence", "narrative-simile",
    "narrative-aphorism", "punchline-paragraphs", "narrative-closing-image",
}


def _line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, max(pos, 0)) + 1


def _lead_word(sentence: str) -> str:
    words = re.findall(r"[^\W\d_]+", sentence.lower())
    while words and words[0] in ("y", "e", "pero", "and", "but"):
        words = words[1:]
    return words[0] if words else ""


def _check_narrative_tics(text: str, sentences: list[str], lang: str) -> list[StructuralFinding]:
    if lang not in _NARRATIVE_RX or _word_count(text) < 120:
        return []
    rx = _NARRATIVE_RX[lang]
    es = lang == "es"
    out: list[StructuralFinding] = []

    def spans(pattern):
        return [(m.start(), m.group(0)) for m in pattern.finditer(text)]

    def found(kind, matches, sev, msg, sug):
        pos, first = matches[0]
        sample = re.sub(r"\s+", " ", first).strip()[:70]
        out.append(StructuralFinding(
            line=_line_of(text, pos), kind=kind, severity=sev,
            message=f"{len(matches)} {('caso' if es else 'case') + ('s' if len(matches) > 1 else '')}: {msg} («{sample}»)",
            suggestion=sug, count=len(matches),
        ))

    pivots = spans(rx["pivot"])
    if pivots:
        found("narrative-pivot", pivots, 2,
              "giro «no es que… es que» que fabrica una revelación" if es else
              "“it's not that… it's that” pivot staging a reveal",
              "di la revelación directamente o muéstrala en un hecho" if es else
              "state the reveal directly or show it through an event")

    # Ladders: "Por las rendijas. Por los espejos. Por las cucharas."
    cadence = [(m.start(), m.group(0)) for m in rx["inline"].finditer(text)
               if m.group("w").lower() not in _ANAPHORA_IGNORE]
    cadence += spans(rx["ladder"])
    run_start, run = 0, 1
    for i in range(1, len(sentences) + 1):
        same = i < len(sentences) and _lead_word(sentences[i]) == _lead_word(sentences[i - 1])
        word = _lead_word(sentences[i - 1])
        if same and word and word not in _ANAPHORA_IGNORE:
            run += 1
            continue
        if run >= 3:
            pos = text.find(sentences[run_start])
            if pos >= 0:
                cadence.append((pos, " ".join(sentences[run_start:i])))
        run_start, run = i, 1
    cadence.sort()
    # Lyrical prose uses anaphora too (Bécquer's "ora… ora…"); the tell is density.
    if len(cadence) >= 3 and len(cadence) / (_word_count(text) / 1000) >= 2.5:
        found("narrative-cadence", cadence, 2,
              "anáforas y gradaciones en serie (repite la misma entrada o «luego… luego»)" if es else
              "serial anaphora and ladders (same opening, “then… then”)",
              "conserva la serie que más importe y escribe las demás como una sola oración" if es else
              "keep the one series that matters and fold the others into a single sentence")

    similes = spans(rx["simile"])
    if len(similes) >= 4 and len(similes) / (_word_count(text) / 1000) >= 3:
        found("narrative-simile", similes, 1,
              "comparaciones «como si / como quien» acumuladas" if es else "stacked “as if / like someone” similes",
              "deja la comparación más precisa y cambia las otras por un detalle observable" if es else
              "keep the sharpest comparison and turn the rest into an observable detail")

    aphorisms = spans(rx["aphorism"])
    if len(aphorisms) >= 2:
        found("narrative-aphorism", aphorisms, 2,
              "aforismos de narrador («hay voces que uno…», «X nunca es X»)" if es else
              "narrator aphorisms (“there are things that you…”, “X is never X”)",
              "cambia la sentencia general por lo que el personaje percibe en ese momento" if es else
              "replace the general maxim with what the character perceives right then")

    # Generated stories end on a far-off image: "Afuera, por fin, los perros…".
    closing_rx = (
        r"^(?:y\s+)?(?:afuera|allá afuera|fuera|a lo lejos|en algún lugar|desde algún lugar|arriba|desde entonces)\b"
        r"|\bpor primera vez en (?:\w+ )?(?:años|décadas|siglos)\b|\b(?:débil|tenue),? pero inconfundible\b"
        if es else
        r"^(?:and\s+)?(?:from\s+)?(?:outside|somewhere|far away|in the distance|above|ever since)\b"
        r"|\bfor the first time in (?:\w+ )?(?:years|decades|centuries)\b|\bfaint but unmistakable\b"
    )
    blocks = [(m.start(), m.group(0).strip()) for m in re.finditer(r"[^\n]+(?:\n(?!\s*\n)[^\n]+)*", text) if m.group(0).strip()]
    tail = [b for b in blocks[-2:] if re.search(closing_rx, b[1], re.I | re.M)] if len(blocks) >= 6 else []
    if tail:
        pos, last = tail[-1]
        out.append(StructuralFinding(
            line=_line_of(text, pos), kind="narrative-closing-image", severity=2,
            message=(f"cierre con imagen lejana o «por primera vez en años», remate típico de relato generado («{last[:60]}»)"
                     if es else f"ending on a distant image or “for the first time in years”, a stock generated-story close (“{last[:60]}”)"),
            suggestion=("termina en la última acción que importa, sin el plano general de afuera" if es
                        else "end on the last action that matters, without the wide shot outside"),
        ))

    # One-sentence paragraphs used as drumbeats, excluding dialogue and headings.
    paragraphs = [(m.start(), m.group(0).strip()) for m in re.finditer(r"[^\n]+(?:\n(?!\s*\n)[^\n]+)*", text)]
    # Titles have no closing punctuation; dialogue paragraphs follow their own rhythm.
    paragraphs = [(p, s) for p, s in paragraphs
                  if re.search(r"[.!?…»”\"]$", s) and not s.startswith(("#", "**", "—", "–", "-", '"', "“", "«", "'"))]
    punch = [(p, s) for p, s in paragraphs if len(split_sentences(s)) == 1 and _word_count(s) <= 8]
    if len(paragraphs) >= 10 and len(punch) >= 5 and len(punch) / len(paragraphs) >= 0.25:
        first_pos, first_text = punch[0]
        out.append(StructuralFinding(
            line=_line_of(text, first_pos), kind="punchline-paragraphs", severity=2,
            message=(f"{len(punch)} de {len(paragraphs)} párrafos son una sola frase corta, como remate («{first_text[:60]}»)"
                     if es else
                     f"{len(punch)} of {len(paragraphs)} paragraphs are a single short punchline (“{first_text[:60]}”)"),
            suggestion=("deja aislada solo la frase que cambia la escena; integra las demás a su párrafo" if es else
                        "isolate only the line that turns the scene; fold the others into their paragraph"),
            count=len(punch),
        ))
    return out


def _check_hyphenated_pairs(text: str, lang: str) -> list[StructuralFinding]:
    """humanizer §26: uniform corporate hyphenation (EN only).

    Humans hyphenate inconsistently; AI hyphenates a fixed set with perfect
    consistency. The tell is density in one text, not any single compound.
    """
    if lang != "en":
        return []
    words = _word_count(text)
    if words < 20:
        return []
    rx = re.compile(r"\b(" + "|".join(_CORPORATE_HYPHENATED) + r")\b", re.I)
    hits = len(rx.findall(text))
    if hits < 5:
        return []
    return [StructuralFinding(
        line=0,
        kind="hyphenated-pairs",
        severity=2,
        message=f"{hits} compuestos corporativos con guion — hipenación uniforme típica de IA",
        suggestion="suelta los guiones en posición predicativa o escribe el concepto directo",
    )]


def _check_adverb_density(text: str, lang: str) -> list[StructuralFinding]:
    """stop-slop adverbs: curated AI-favored adverbs, density-gated (EN/ES).

    stop-slop bans all adverbs; aismell only flags a curated list when it
    stacks — a single 'actually' is ordinary English, five are a texture.
    """
    words = _word_count(text)
    if words < 12:
        return []
    if lang == "es":
        rx = re.compile(r"\b(" + "|".join(_AI_ADVERBS_ES) + r")\b", re.I)
        threshold = 4
    else:
        rx = re.compile(r"\b(" + "|".join(_AI_ADVERBS_EN) + r")\b", re.I)
        threshold = 5
    hits = len(rx.findall(text))
    if hits < threshold:
        return []
    return [StructuralFinding(
        line=0,
        kind="adverb-density",
        severity=2,
        message=(
            f"{hits} adverbios de relleno apilados — textura típica de IA"
            if lang == "es" else
            f"{hits} stacked filler adverbs — typical AI texture"
        ),
        suggestion=(
            "borra la mayoría; deja el adverbio solo cuando cambia el significado"
            if lang == "es" else
            "cut most of them; keep an adverb only when it changes the meaning"
        ),
    )]


def _check_fragmented_headers(text: str, lang: str) -> list[StructuralFinding]:
    """humanizer §29: heading followed by a one-line restatement.

    A generic warm-up sentence after a heading ('Speed matters.' after
    '## Performance') pads the prose without adding information.
    """
    lines = [ln.strip() for ln in text.splitlines()]
    out: list[StructuralFinding] = []
    n = len(lines)
    for i in range(n - 2):
        if not re.match(r"^#{1,4}\s+\S", lines[i]):
            continue
        # next non-empty line after the heading
        j = i + 1
        while j < n and not lines[j]:
            j += 1
        if j >= n:
            continue
        nxt = lines[j]
        nxt_words = len(nxt.split())
        if 2 <= nxt_words <= 8:
            k = j + 1
            while k < n and not lines[k]:
                k += 1
            following = lines[k] if k < n else ""
            if len(following.split()) > nxt_words + 4:
                out.append(StructuralFinding(
                    line=i + 1,
                    kind="fragmented-headers",
                    severity=1,
                    message=(
                        f"título seguido de una línea de relleno ({nxt_words} palabras) que repite el rótulo"
                        if lang == "es" else
                        f"heading followed by a one-line filler ({nxt_words} words) restating the label"
                    ),
                    suggestion=(
                        "borra la frase de calentamiento y deja que el contenido arranque directo"
                        if lang == "es" else
                        "delete the warm-up line and let the content start directly"
                    ),
                ))
    return out


def _check_emoji_headers(text: str, lang: str) -> list[StructuralFinding]:
    """humanizer §18: emojis decorating heading/bullet labels.

    Emojis inside prose are fine; a line that STARTS with an emoji as a
    bullet/heading decoration is AI list formatting.
    """
    count = 0
    for ln in text.splitlines():
        s = ln.strip()
        if not s:
            continue
        if _EMOJI_RX.match(s) and re.search(r"\S{2,}", s[1:]):
            count += 1
    if count < 2:
        return []
    return [StructuralFinding(
        line=0,
        kind="emoji-headers",
        severity=1,
        message=(
            f"{count} líneas decoradas con emoji — formato de lista IA"
            if lang == "es" else
            f"{count} emoji-decorated lines — AI list formatting"
        ),
        suggestion=(
            "quita los emojis de títulos y viñetas; deja que el texto diga lo importante"
            if lang == "es" else
            "remove emojis from headings and bullets; let the text carry the meaning"
        ),
    )]


def _check_tailing_negation(text: str, lang: str) -> list[StructuralFinding]:
    """humanizer §9: clipped 'no X' fragments tacked onto a sentence (EN).

    'The options come from the selected item, no guessing.' — a real clause
    should follow the comma; the fragment is an AI rhythm tick.
    """
    if lang != "en":
        return []
    rx = re.compile(r"\b(" + "|".join(_TAILING_NEGATIONS) + r")\b", re.I)
    hits = len(rx.findall(text))
    if hits < 2:
        return []
    return [StructuralFinding(
        line=0,
        kind="tailing-negation",
        severity=2,
        message=f"{hits} negaciones colgadas al final de frase — muletilla rítmica de IA",
        suggestion="convierte el fragmento en una cláusula real o elimínalo",
    )]


def _score_sections(sentences: list[str], lang: str) -> list[SectionScore]:
    if not sentences:
        return []
    n = len(sentences)
    first_end = max(1, round(n * 0.25))
    last_start = min(n - 1, max(first_end, round(n * 0.75))) if n >= 3 else n
    buckets = [
        ("apertura", sentences[:first_end]),
        ("cuerpo", sentences[first_end:last_start]),
        ("cierre", sentences[last_start:]),
    ]
    out: list[SectionScore] = []
    for name, chunk in buckets:
        if not chunk:
            out.append(SectionScore(name=name, score=0.0, sentences=0, reasons=["sin texto"] ))
            continue
        vals: list[float] = []
        reasons: list[str] = []
        for s in chunk:
            val, rs = _sentence_score(s, lang, name)
            vals.append(val)
            reasons.extend(rs)
        score = min(1.0, sum(vals) / max(len(vals), 1))
        if reasons:
            # Keep stable, non-noisy summary reasons.
            uniq = []
            for r in reasons:
                if r not in uniq:
                    uniq.append(r)
            reasons = uniq[:3]
        else:
            reasons = ["sin señales fuertes"]
        out.append(SectionScore(name=name, score=score, sentences=len(chunk), reasons=reasons))
    return out


def load_canary_samples(path: str | Path | None = None) -> list[dict]:
    """Load local regression samples used to keep the detector honest."""
    if path is None:
        path = Path(__file__).resolve().parent.parent / "tests" / "samples" / "canary.json"
    p = Path(path)
    if not p.exists():
        return []
    return json.loads(p.read_text(encoding="utf-8"))


# ---------- local segment snapshots ----------

def _segment_confidence(report: Report, lang: str) -> str:
    """Confidence in the local signal, not confidence of authorship."""
    findings = report.total_findings
    if findings >= 3 and report.score >= 0.35:
        return "alta" if lang == "es" else "high"
    if findings:
        if report.severity_label in ("moderado", "moderate"):
            return "media" if lang == "es" else "medium"
        return "baja" if lang == "es" else "low"
    return "baja" if lang == "es" else "low"


def _score_segments(
    sentences: list[str],
    lang: str,
    strict: bool,
    era: str,
) -> list[SegmentScore]:
    """Analyze contiguous windows without changing the document-level score.

    Three sentences is the minimum useful window. Six keeps the result useful
    on mobile; a final short tail is merged into the previous window.
    """
    if len(sentences) < 3:
        return []
    window = 6
    starts = list(range(0, len(sentences), window))
    if len(starts) > 1 and len(sentences) - starts[-1] < 3:
        starts.pop()
    segments: list[SegmentScore] = []
    for index, start in enumerate(starts, start=1):
        end = len(sentences) if index == len(starts) else min(len(sentences), start + window)
        segment_text = " ".join(sentences[start:end]).strip()
        local, _ = analyze(
            segment_text,
            lang=lang,
            strict=strict,
            era=era,
            include_segments=False,
        )
        segments.append(SegmentScore(
            index=index,
            start_sentence=start + 1,
            end_sentence=end,
            sentences=end - start,
            score=local.score,
            label=local.severity_label,
            confidence=_segment_confidence(local, lang),
            findings=local.total_findings,
            text=segment_text,
        ))
    return segments


# ---------- main analyze ----------

def analyze(
    text: str,
    lang: str | None = None,
    strict: bool = False,
    era: str = "auto",
    include_segments: bool = True,
) -> tuple[Report, str]:
    """Analyze text. Returns (report, lang_used).

    era: "auto" | "pre-llm" | "post-llm" | "unknown".
    Explicit era values are unverified user context, not scoring evidence.
    """
    lang = lang or detect_lang(text)
    patterns = load_patterns(lang)

    lines = text.splitlines()
    authorial = _authorial_lines(lines)
    authorial_by_line = dict(authorial)
    authorial_text = "\n".join(authorial_by_line.get(i, "") for i in range(1, len(lines) + 1))
    sentences = split_sentences(authorial_text)
    report = Report(sentences=len(sentences))
    report.stats = _text_stats(authorial_text, sentences)

    min_severity = 2 if strict else 1

    # phrase / regex hits, line-anchored
    for i, line in authorial:
        for p in patterns:
            if p.severity < min_severity:
                continue
            for m in p.compile().finditer(line):
                if _match_is_quoted_example(line, m.start(), m.end()):
                    continue
                report.hits.append(Hit(
                    line=i,
                    col=m.start(),
                    end=m.end(),
                    text=line,
                    matched=m.group(0),
                    pattern=p,
                ))

    # Deduplicate overlapping hits per line: several pattern families fire on
    # the same span ("not just X but also Y" trips en.not_just, en.not_but_direct
    # and en.not_x_but_y_direct). One phrase = one finding. Keep the highest
    # severity; on ties, the first match wins.
    report.hits.sort(key=lambda h: (h.line, h.col, -(h.end - h.col), -h.pattern.severity))
    deduped: list[Hit] = []
    for h in report.hits:
        if deduped and deduped[-1].line == h.line and h.col < deduped[-1].end and h.end > deduped[-1].col:
            prev = deduped[-1]
            prev_len = prev.end - prev.col
            cur_len = h.end - h.col
            if (h.pattern.severity, cur_len) > (prev.pattern.severity, prev_len):
                deduped[-1] = h
            continue
        deduped.append(h)
    report.hits = deduped

    # structural checks
    if not strict:
        report.structural.extend(_check_em_dashes(authorial_text, authorial_text.splitlines(), lang))
        report.structural.extend(_check_list_density(authorial_text))
        report.structural.extend(_check_ellipses(authorial_text, lang))
        report.structural.extend(_check_section_headers(authorial_text, lang))
        report.structural.extend(_check_emphasis_overload(authorial_text, lang))
        report.structural.extend(_check_tricolon(sentences))
        report.structural.extend(_check_rhetorical_qa(sentences, lang))
        report.structural.extend(_check_binary_reframes(authorial_text, lang))
        report.structural.extend(_check_negative_listing(authorial_text, lang))
        report.structural.extend(_check_false_agency(authorial_text, lang))
        report.structural.extend(_check_passive_voice(authorial_text, lang))
        report.structural.extend(_check_wh_starters(sentences, lang))
        report.structural.extend(_check_paragraph_connectors(authorial_text, lang))
        report.structural.extend(_check_paragraph_symmetry(authorial_text, lang))
        report.structural.extend(_check_synthetic_academic_texture(authorial_text, lang))
        report.structural.extend(_check_low_specificity(authorial_text, lang))
        report.structural.extend(_check_vague_sentence_stack(sentences, lang))
        report.structural.extend(_check_essay_scaffolding(authorial_text, lang))
        # Wikipedia-sourced checks
        report.structural.extend(_check_negative_parallelism_density(sentences, lang))
        report.structural.extend(_check_challenges_template(authorial_text, lang))
        report.structural.extend(_check_media_notability_padding(authorial_text, lang))
        report.structural.extend(_check_ai_artifact_markup(authorial_text, lang))
        report.structural.extend(_check_rule_of_three_density(sentences, lang))
    report.structural.extend(_check_rhythm(sentences, lang))
    if not strict:
        report.structural.extend(_check_semicolon_ratio(authorial_text, lang))
        report.structural.extend(_check_nominalization_density(authorial_text, lang))
        report.structural.extend(_check_impersonal_se_stacking(authorial_text, lang))
        report.structural.extend(_check_storyscope_discourse(authorial_text, lang))
        # humanizer v2.9.1 + stop-slop gaps (2026-08)
        report.structural.extend(_check_staccato_runs(sentences, lang))
        report.structural.extend(_check_narrative_tics(authorial_text, sentences, lang))
        report.structural.extend(_check_template_placeholders(authorial_text, lang))
        report.structural.extend(_check_listicle_scaffold(authorial_text, lang))
        report.structural.extend(_check_contraction_deficit(authorial_text, lang))
        report.structural.extend(_check_default_names(authorial_text, lang))
        report.structural.extend(_check_hyphenated_pairs(authorial_text, lang))
        report.structural.extend(_check_adverb_density(authorial_text, lang))
        report.structural.extend(_check_fragmented_headers(authorial_text, lang))
        report.structural.extend(_check_emoji_headers(authorial_text, lang))
        report.structural.extend(_check_tailing_negation(authorial_text, lang))
        report.structural.extend(_check_statistical_uniformity(report.stats, lang))
        report.structural.extend(_check_narrator_distance(sentences, lang))
        report.structural.extend(_check_lazy_extremes(authorial_text, lang))
    report.sections = _score_sections(sentences, lang)

    # score — evidence-aware combiner.
    # It is an index of AI-smell evidence, NOT a probability that the author used AI.
    structural_kinds = {f.kind for f in report.structural}
    severe_structural = sum(1 for f in report.structural if f.severity >= 3)

    # Dimension 1: lexical hits. Repetition matters, but it must saturate:
    # 15 comments inside a 50-page thesis cannot mean "94% AI" by itself.
    sev3_hits = sum(1 for h in report.hits if h.pattern.severity >= 3)
    sev2_hits = sum(1 for h in report.hits if h.pattern.severity == 2)
    sev1_hits = sum(1 for h in report.hits if h.pattern.severity <= 1)
    distinct_sev3_ids = len({h.pattern.id for h in report.hits if h.pattern.severity >= 3})
    distinct_ids = len({h.pattern.id for h in report.hits})
    lex_d = min(0.72, distinct_sev3_ids * 0.12 + distinct_ids * 0.025 + sev3_hits * 0.025 + sev2_hits * 0.012)
    # Pangram's measure is a rate: AI phrases appear ~3 per 10k words in human
    # text and ~30 in AI text. Grouped rules hide repetition from the
    # distinct-id count, so a dense text also scores by phrases per 10k words.
    phrase_rate = (sev3_hits + 0.7 * sev2_hits + 0.3 * sev1_hits) * 10000 / max(_word_count(authorial_text), 1)
    if len(report.hits) >= 3:
        lex_d = max(lex_d, min(0.55, max(0.0, phrase_rate - 6) / 100))

    # Dimension 2: structural macro-signals (essay scaffold, low specificity, symmetry, etc.)
    macro_kinds = {
        "essay-scaffolding", "synthetic-academic", "low-specificity",
        "vague-sentence-stack", "paragraph-connectors", "paragraph-symmetry",
        "rhetorical-qa", "binary-reframe", "negative-listing", "false-agency",
        "passive-voice", "wh-starters", "discourse-overexplained-theme",
        "discourse-tidy-resolution", "listicle-scaffold",
    }
    macro_present = macro_kinds & structural_kinds
    macro_d = min(0.70, 0.18 * len(macro_present) + 0.08 * severe_structural)

    # Dimension 3: rhythm/format. These are weak alone; they should not dominate long papers.
    rhythm_kinds = {"em-dash", "ellipses", "section-headers", "emphasis-overload", "tricolon", "rhythm"}
    rhythm_d = min(0.32, 0.10 * len(rhythm_kinds & structural_kinds))

    # Dimension 4: soundshuman-style statistics. Two agreeing metrics are
    # required; a single low TTR or flat cadence is not evidence by itself.
    if "statistical-uniformity" in structural_kinds:
        statistical_signals = sum((
            float(report.stats["burstiness"]) < 0.30,
            float(report.stats["type_token_ratio"]) < 0.48,
            float(report.stats["trigram_repetition"]) > 0.035,
        ))
    else:
        statistical_signals = 0
    statistical_d = min(0.18, 0.06 * statistical_signals)

    # Dimension 5: weak editorial-distance cues. These explain why a passage
    # feels generic, but they are deliberately capped and never decide alone.
    editorial_weak_d = min(
        0.12,
        (0.08 if "narrator-distance" in structural_kinds else 0.0)
        + (0.04 if "lazy-extremes" in structural_kinds else 0.0)
        + (0.05 if "default-names" in structural_kinds else 0.0),
    )

    # A digit/pronoun regex cannot establish an absence of names, places or
    # concrete actors. Retain the public component key, not the unsupported penalty.
    anchor_d = 0.0

    # Dimension 5: Wikipedia-sourced signals (negative parallelism, challenges template,
    # media notability padding, chatbot artifact markup, rule-of-three overuse).
    # These are strong independent signals: each alone is moderately suspicious,
    # but two or more together are nearly definitive.
    wiki_kinds = {
        "negative-parallelism", "challenges-template",
        "media-notability", "ai-artifact-markup", "rule-of-three",
    }
    wiki_present = wiki_kinds & structural_kinds
    # ai-artifact-markup is a near-certain signal on its own
    wiki_d = 0.0
    if "ai-artifact-markup" in structural_kinds:
        wiki_d = 0.80  # chatbot markup is near-certain AI
    elif "template-placeholders" in structural_kinds:
        wiki_d = 0.60  # unfilled chatbot slots; a human form letter can have them too
    elif wiki_present:
        wiki_d = min(0.55, 0.18 * len(wiki_present))

    # Dimension 7: narrative fiction kit. Staccato only counts alongside
    # another narrative tell: clipped sentences alone are a human style too.
    narrative_present = NARRATIVE_KINDS & structural_kinds
    if narrative_present and "staccato-runs" in structural_kinds:
        narrative_present = narrative_present | {"staccato-runs"}
    narrative_d = min(0.66, 0.13 * len(narrative_present))

    # Combine: 1 - prod(1 - d_i). Reacts when independent dimensions agree.
    dims = [lex_d, macro_d, rhythm_d, statistical_d, editorial_weak_d, anchor_d, wiki_d, narrative_d]
    combined = 1.0
    for d in dims:
        combined *= (1.0 - d)
    combined = 1.0 - combined

    # Backstop floors for genuinely compound signals.
    if "essay-scaffolding" in structural_kinds and "synthetic-academic" in structural_kinds:
        combined = max(combined, 0.52)
    elif "essay-scaffolding" in structural_kinds:
        combined = max(combined, 0.42)
    elif {"synthetic-academic", "low-specificity"} <= structural_kinds:
        combined = max(combined, 0.35)
    elif "synthetic-academic" in structural_kinds:
        combined = max(combined, 0.25)
    elif "binary-reframe" in structural_kinds and distinct_sev3_ids >= 1 and len(report.hits) >= 4:
        combined = max(combined, 0.55)
    elif severe_structural >= 2:
        combined = max(combined, 0.30)
    # Wikipedia-signal backstops
    if "ai-artifact-markup" in structural_kinds:
        combined = max(combined, 0.85)  # chatbot markup is near-certain
    elif len(wiki_present) >= 3:
        combined = max(combined, 0.60)
    elif "challenges-template" in structural_kinds and "negative-parallelism" in structural_kinds:
        combined = max(combined, 0.50)

    # Short-text density backstop: if a short text (4-12 sentences) has
    # many distinct high-severity hits, the dimensional combine can underweight
    # them because each dimension is individually mild. But 5+ distinct
    # signals with at least 3 moderate-or-higher in 6 sentences is suspicious.
    if 4 <= report.sentences <= 12:
        distinct_mod_plus = len({h.pattern.id for h in report.hits if h.pattern.severity >= 2})
        if distinct_mod_plus >= 3 and len(report.hits) >= 5:
            combined = max(combined, 0.60)

    # Short demo-style AI answers can be dense without many paragraph-level
    # structures. If nearly every sentence is marked and there are several
    # high-severity lexical cues, do not leave the visible example in the
    # moderate band.
    sentence_density = min(1.0, len(report.hits) / max(report.sentences, 1))
    if 4 <= report.sentences < 30 and sentence_density >= 0.70 and sev3_hits >= 2 and len(report.hits) >= 5:
        combined = max(combined, 0.68)

    # Academic dampener: long academic texts naturally contain abstraction,
    # formal transitions, citations, and repeated section shapes.
    if report.sentences >= 150 and {"synthetic-academic", "low-specificity"} <= structural_kinds:
        academic_expected = {"synthetic-academic", "low-specificity", "vague-sentence-stack",
                             "paragraph-symmetry", "essay-scaffolding", "paragraph-connectors"}
        non_academic_kinds = structural_kinds - academic_expected
        # Wikipedia-sourced signals and ai-artifact-markup are NOT academic — don't dampen if present
        wiki_override = non_academic_kinds & (wiki_kinds | {"ai-artifact-markup"})
        if not wiki_override and (not non_academic_kinds or non_academic_kinds <= {"rhythm", "tricolon"}):
            combined *= 0.55

    # Long-document density cap. Sparse findings in a thesis should read as
    # "revise these passages", not as a conviction.
    weighted_findings = (
        sev3_hits * 1.3 + sev2_hits * 0.8 + sev1_hits * 0.35 +
        sum((1.2 if f.severity >= 3 else 0.75 if f.severity == 2 else 0.35)
            * (f.count if f.kind in NARRATIVE_KINDS else 1) for f in report.structural)
    )
    evidence_density = weighted_findings / max(report.sentences, 1)
    evidence_cap = 1.0
    if report.sentences >= 150:
        evidence_cap = 0.24 if evidence_density < 0.035 else 0.34 if evidence_density < 0.10 else 0.42 if evidence_density < 0.13 else 1.0
        combined = min(combined, evidence_cap)
    elif report.sentences >= 60:
        if evidence_density < 0.05:
            combined = min(combined, 0.30)
        elif evidence_density < 0.09:
            combined = min(combined, 0.42)
    elif report.sentences >= 30 and evidence_density < 0.08:
        combined = min(combined, 0.50)

    # Length-aware credibility cap: a handful of hits in a 3-sentence text
    # cannot justify 80%. Short texts need proportionally more evidence to
    # score high — the verdict on 3 sentences is "puede ser" at most, never
    # "suena a IA" with confidence.
    short_cap = min(1.0, 0.40 + 0.045 * report.sentences)
    combined = min(combined, short_cap)

    # Keep the public fields without inferring publication dates from citations
    # or letting a declared date erase editorial issues in the prose.
    era_detected, era_year = detect_era(text)
    report.era = era_detected if era == "auto" else era
    report.era_max_year = era_year
    if report.era == "pre-llm":
        report.notes.append(
            "Época anterior a los LLM indicada por el usuario; el análisis no verifica "
            "la fecha ni la autoría y conserva las observaciones editoriales."
            if lang == "es" else
            "Pre-LLM era supplied by the user; this analysis does not verify the date "
            "or authorship and retains editorial findings."
        )

    # Academic-register dampener: formal academic prose is full of connectors
    # and impersonal voice. If the text has real citations and most hits are
    # connector-class, cap the score — the connector tics are genre markers.
    citation_hits = _CITATION_RE_ACADEMIC.findall(authorial_text)
    if len(citation_hits) >= 2 and report.hits:
        connector_hits = [
            h for h in report.hits
            if any(f in h.pattern.id for f in _CONNECTOR_FAMILIES)
        ]
        non_connector_sev3 = [
            h for h in report.hits
            if h.pattern.severity >= 3 and h not in connector_hits
        ]
        if connector_hits and len(connector_hits) / len(report.hits) >= 0.5 and len(non_connector_sev3) < 2:
            combined = min(combined, 0.45)
            report.notes.append(
                "Registro académico con citas: los conectores formales ('en este sentido', "
                "'no obstante', 'en primer lugar') son del género, no de la IA."
            )

    report.score_components = {
        "lexical": round(lex_d, 4),
        "discourse": round(macro_d, 4),
        "rhythm_format": round(rhythm_d, 4),
        "statistical": round(statistical_d, 4),
        "editorial_distance": round(editorial_weak_d, 4),
        "anchor_starvation": round(anchor_d, 4),
        "chatbot_artifacts": round(wiki_d, 4),
        "narrative": round(narrative_d, 4),
        "combined": round(combined, 4),
    }
    report.score = min(1.0, combined)

    words = max(_word_count(authorial_text), 1)
    report.features = {
        **{"rule_" + k: v for k, v in report.score_components.items()},
        "hits3": 100.0 * sev3_hits / words,
        "hits2": 100.0 * sev2_hits / words,
        "hits1": 100.0 * sev1_hits / words,
        "hit_ids": float(distinct_ids),
        "structural": 100.0 * len(report.structural) / max(report.sentences, 1),
        "structural_kinds": float(len(structural_kinds)),
        "log_words": math.log(words),
        **_style_features(authorial_text, sentences, lang),
    }

    # The trained combiner reads every feature above (rule dimensions included)
    # and replaces the hand-tuned blend; the short-text cap still applies because
    # a few sentences cannot carry a strong conclusion.
    styled = _style_model(report.features, lang)
    if styled:
        p, report.style_reasons = styled
        report.score_components["style_model"] = round(p, 4)
        # The model was trained on 120-2,500 word texts. Below that it fades into
        # the rule index; above ~150 sentences the findings-density caps still
        # bound it, so a long thesis is judged on located evidence.
        trust = max(0.0, min(1.0, (words - 60) / 120))
        blended = trust * p + (1 - trust) * combined
        report.score = min(blended, short_cap, evidence_cap if report.sentences >= 150 else 1.0)
        report.context = _context(report.features, lang)
        report.human_exceed = _human_exceed(report.score, lang, report.context)
    es = lang == "es"
    exceed = report.human_exceed
    if exceed is not None:
        # Both conditions: rare among human texts of the same kind AND a real index.
        # About 3% of human reference texts reach "alto", 10% "moderado".
        high = exceed <= 0.03 and report.score >= 0.6
        mid = exceed <= 0.10 and report.score >= 0.3
        low = report.score >= 0.10 or bool(report.hits or report.structural)
    else:
        high, mid, low = report.score >= 0.6, report.score >= 0.3, report.score > 0
    report.severity_label = (("alto" if es else "high") if high else ("moderado" if es else "moderate") if mid
                             else ("bajo" if es else "low") if low else ("limpio" if es else "clean"))

    report.rates = _pangram_rates(authorial_text, len(report.hits))

    if include_segments:
        report.segments = _score_segments(sentences, lang, strict, era)

    return report, lang
