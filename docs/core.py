"""aismell core detector — sniffs AI-smell line by line."""

from __future__ import annotations

import json
import re
import statistics
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

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


@dataclass
class SectionScore:
    name: str             # apertura | cuerpo | cierre
    score: float
    sentences: int
    reasons: list[str] = field(default_factory=list)


@dataclass
class Report:
    sentences: int
    hits: list[Hit] = field(default_factory=list)
    structural: list[StructuralFinding] = field(default_factory=list)
    sections: list[SectionScore] = field(default_factory=list)
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


def _check_ellipses(text: str, lang: str) -> list[StructuralFinding]:
    """Google Doc AI-isms: repeated ellipses used for fake drama."""
    count = text.count("...") + text.count("…")
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
    """Google Doc AI-isms: labeled sections in otherwise prose-like text."""
    headers = 0
    for ln in text.splitlines():
        s = ln.strip()
        if re.match(r"^#{1,4}\s+\S", s):
            headers += 1
        elif re.match(r"^(understanding|overview|key takeaways|the problem|the solution|moving forward|conclusion|summary)\b", s, re.I):
            headers += 1
        elif re.match(r"^(contexto|introducción|desarrollo|conclusión|resumen|puntos clave|el problema|la solución)\b", s, re.I):
            headers += 1
    if headers < 3:
        return []
    return [StructuralFinding(
        line=0,
        kind="section-headers",
        severity=2,
        message=(
            f"{headers} encabezados de sección — formato de respuesta IA"
            if lang == "es" else
            f"{headers} section headers — AI answer formatting"
        ),
        suggestion=(
            "si es prosa, deja que los párrafos hagan el trabajo"
            if lang == "es" else
            "if this is prose, let paragraphs do the work"
        ),
    )]


def _check_emphasis_overload(text: str, lang: str) -> list[StructuralFinding]:
    """Google Doc AI-isms: excessive markdown emphasis."""
    bold = len(re.findall(r"\*\*[^*]+\*\*", text))
    ital = len(re.findall(r"(?<!\*)\*[^*\n]+\*(?!\*)", text))
    total = bold + ital
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


_PARAGRAPH_CONNECTORS_ES = re.compile(
    r"^(además|adicionalmente|por otra parte|por otro lado|en consecuencia|"
    r"asimismo|posteriormente|en primer lugar|en segundo lugar|finalmente|"
    r"en conclusión|en resumen)[,\s]",
    re.IGNORECASE | re.MULTILINE,
)
_PARAGRAPH_CONNECTORS_EN = re.compile(
    r"^(furthermore|moreover|additionally|consequently|hence|"
    r"subsequently|firstly|secondly|finally|in conclusion|"
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
    if hits >= 2:
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
            severity=3,
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
        severity=3,
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
            suggestion="revisa frase por frase: cada afirmación debería tener un caso, dato, cita o decisión concreta",
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
        report.structural.extend(_check_ellipses(text, lang))
        report.structural.extend(_check_section_headers(text, lang))
        report.structural.extend(_check_emphasis_overload(text, lang))
        report.structural.extend(_check_tricolon(sentences))
        report.structural.extend(_check_rhetorical_qa(sentences, lang))
        report.structural.extend(_check_paragraph_connectors(text, lang))
        report.structural.extend(_check_paragraph_symmetry(text, lang))
        report.structural.extend(_check_synthetic_academic_texture(text, lang))
        report.structural.extend(_check_low_specificity(text, lang))
        report.structural.extend(_check_vague_sentence_stack(sentences, lang))
    report.structural.extend(_check_rhythm(sentences))
    report.sections = _score_sections(sentences, lang)

    # score
    weight = sum(h.pattern.severity for h in report.hits)
    weight += sum(f.severity for f in report.structural)
    # Normalize local matches against sentence count, but do not let long uploads
    # dilute strong whole-text structural signals into a fake-clean score.
    normalized_score = weight / max(len(sentences), 1) / 3.0
    structural_kinds = {f.kind for f in report.structural}
    severe_structural = sum(1 for f in report.structural if f.severity >= 3)
    structural_floor = 0.0
    if {"synthetic-academic", "low-specificity"} <= structural_kinds:
        structural_floor = 0.35
    elif "synthetic-academic" in structural_kinds:
        structural_floor = 0.28
    elif severe_structural >= 2:
        structural_floor = 0.30
    elif len(report.structural) >= 3:
        structural_floor = 0.22
    report.score = min(1.0, max(normalized_score, structural_floor))

    if report.score >= 0.6:
        report.severity_label = "alto" if lang == "es" else "high"
    elif report.score >= 0.3:
        report.severity_label = "moderado" if lang == "es" else "moderate"
    elif report.score > 0:
        report.severity_label = "bajo" if lang == "es" else "low"
    else:
        report.severity_label = "limpio" if lang == "es" else "clean"

    return report, lang
