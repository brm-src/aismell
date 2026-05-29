"""aismell core detector — sniffs AI-smell line by line."""

from __future__ import annotations

import json
import re
import statistics
from dataclasses import dataclass, field
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
    """Skip inline examples like *"delve into"* or `hope this helps`.

    This keeps documentation of slop from being scored as slop.
    """
    return _inside_spans(line, start, end, [
        ("`", "`"),
        ('"', '"'),
        ("“", "”"),
        ("*", "*"),
    ])


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
        label_prefix = re.match(r"^(?:[-*•]\s+|\d+\.\s+)?", stripped)
        label_start = label_prefix.end() if label_prefix else 0
        for match in emphasis_rx.finditer(stripped):
            content = (match.group(1) or match.group(2) or "").strip()
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
        suggestion = "di qué era, sin runway de negaciones"
    else:
        pattern = r"\bnot\s+(a|an|the)?\b[^.!?]{1,120}[.!?]\s*\bnot\s+(a|an|the)?\b[^.!?]{1,120}[.!?]\s*\b(a|an|the|it\s+was)\b"
        msg = "negative listing before the point — AI dramatic buildup"
        suggestion = "state what it is, without the runway"
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
        suggestion = "nombra quién decide, lee, cambia o arregla"
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
        suggestion = "name who decides, reads, changes, or fixes it"
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
        suggestion = "pon a la persona o equipo como sujeto"
    else:
        patterns = [
            r"\bmistakes\s+were\s+made\b",
            r"\bthe\s+decision\s+was\s+reached\b",
            r"\bthe\s+product\s+was\s+created\b",
            r"\bit\s+is\s+believed\s+that\b",
        ]
        msg = "evasively passive voice — hides who did what"
        suggestion = "put the person or team in the subject slot"
    hits = sum(1 for p in patterns if re.search(p, text, re.IGNORECASE))
    if hits >= 1:
        sev = 3 if hits >= 2 else 2
        return [StructuralFinding(line=0, kind="passive-voice", severity=sev, message=f"{hits} casos: {msg}", suggestion=suggestion)]
    return []


def _check_wh_starters(sentences: list[str], lang: str) -> list[StructuralFinding]:
    if lang == "es":
        rx = re.compile(r"^(qu[eé]|por\s+qu[eé]|c[oó]mo|cu[aá]ndo|d[oó]nde)\b", re.IGNORECASE)
        msg = "arranques interrogativos repetidos — molde de explicación IA"
        suggestion = "abre con sujetos y acciones, no con pregunta-retórica en cadena"
    else:
        rx = re.compile(r"^(what|why|how|when|where|which|who)\b", re.IGNORECASE)
        msg = "repeated Wh- starters — AI explainer template"
        suggestion = "lead with subjects and actions, not stacked rhetorical prompts"
    hits = sum(1 for s in sentences if rx.search(s.strip()))
    if hits >= 2:
        return [StructuralFinding(line=0, kind="wh-starters", severity=2, message=f"{hits} casos: {msg}", suggestion=suggestion)]
    return []


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
        suggestion="rompe el molde: empieza por una escena, dato o pregunta concreta y deja caer la estructura formal",
    )]


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
    authorial = _authorial_lines(lines)
    authorial_text = "\n".join(line for _, line in authorial)
    sentences = split_sentences(authorial_text)
    report = Report(sentences=len(sentences))

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

    # structural checks
    if not strict:
        report.structural.extend(_check_em_dashes(authorial_text, [line for _, line in authorial]))
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
    report.structural.extend(_check_rhythm(sentences))
    report.sections = _score_sections(sentences, lang)

    # score — multi-dimensional combiner instead of flat weight/sentences
    structural_kinds = {f.kind for f in report.structural}
    severe_structural = sum(1 for f in report.structural if f.severity >= 3)

    # Dimension 1: lexical hits — saturating, not diluted by length.
    sev3_hits = sum(1 for h in report.hits if h.pattern.severity >= 3)
    sev2_hits = sum(1 for h in report.hits if h.pattern.severity == 2)
    distinct_sev3_ids = len({h.pattern.id for h in report.hits if h.pattern.severity >= 3})
    # Distinct sev-3 patterns matter more than 10 hits of the same one.
    lex_d = min(1.0, distinct_sev3_ids * 0.18 + sev3_hits * 0.04 + sev2_hits * 0.02)

    # Dimension 2: structural macro-signals (essay-scaffolding, synthetic-academic, etc.)
    macro_kinds = {
        "essay-scaffolding", "synthetic-academic", "low-specificity",
        "vague-sentence-stack", "paragraph-connectors", "paragraph-symmetry",
        "rhetorical-qa", "binary-reframe", "negative-listing", "false-agency",
        "passive-voice", "wh-starters",
    }
    macro_present = macro_kinds & structural_kinds
    macro_d = min(1.0, 0.30 * len(macro_present) + 0.10 * severe_structural)

    # Dimension 3: rhythm/format (em-dash, ellipses, headers, emphasis, tricolon, rhythm).
    rhythm_kinds = {
        "em-dash", "ellipses", "section-headers", "emphasis-overload",
        "tricolon", "rhythm",
    }
    rhythm_d = min(1.0, 0.18 * len(rhythm_kinds & structural_kinds))

    # Dimension 4: anchor density — only fires with strong evidence,
    # because the anchor regex is narrow (digits/dates/some pronouns) and
    # would otherwise punish prose-heavy human writing.
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    anchor_starved = 0
    for p in paragraphs:
        if _word_count(p) >= 40 and len(_CONCRETE_ANCHORS.findall(p)) == 0:
            anchor_starved += 1
    anchor_d = 0.0
    if len(paragraphs) >= 3 and anchor_starved >= 3:
        ratio = anchor_starved / len(paragraphs)
        if ratio >= 0.7:
            anchor_d = 0.45
        elif ratio >= 0.5:
            anchor_d = 0.30

    # Combine: 1 - prod(1 - d_i). Reacts strongly when multiple dimensions signal.
    dims = [lex_d, macro_d, rhythm_d, anchor_d]
    combined = 1.0
    for d in dims:
        combined *= (1.0 - d)
    combined = 1.0 - combined

    # Backstop floors for the strongest single signals.
    if "essay-scaffolding" in structural_kinds and "synthetic-academic" in structural_kinds:
        combined = max(combined, 0.70)
    elif "essay-scaffolding" in structural_kinds:
        combined = max(combined, 0.55)
    elif {"synthetic-academic", "low-specificity"} <= structural_kinds:
        combined = max(combined, 0.50)
    elif "synthetic-academic" in structural_kinds:
        combined = max(combined, 0.40)
    elif "binary-reframe" in structural_kinds and distinct_sev3_ids >= 1 and len(report.hits) >= 4:
        combined = max(combined, 0.60)
    elif severe_structural >= 2:
        combined = max(combined, 0.35)

    report.score = min(1.0, combined)

    if report.score >= 0.6:
        report.severity_label = "alto" if lang == "es" else "high"
    elif report.score >= 0.3:
        report.severity_label = "moderado" if lang == "es" else "moderate"
    elif report.score > 0:
        report.severity_label = "bajo" if lang == "es" else "low"
    else:
        report.severity_label = "limpio" if lang == "es" else "clean"

    return report, lang
