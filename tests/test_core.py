"""Smoke tests for aismell core."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aismell.core import analyze, detect_lang, load_canary_samples, split_sentences


def test_detects_spanish():
    text = "Vale la pena destacar que esto es importante para el futuro."
    assert detect_lang(text) == "es"


def test_detects_english():
    text = "It is worth noting that this delves into the complexities."
    assert detect_lang(text) == "en"


def test_clean_text_low_score():
    text = (
        "Ayer me senté a escribir y no salió nada. "
        "Tres horas mirando la pantalla. "
        "El problema no era el tema."
    )
    report, lang = analyze(text)
    assert lang == "es"
    assert report.score < 0.2


def test_dirty_text_high_score():
    text = (
        "Vale la pena destacar que esto se erige como un testimonio. "
        "En última instancia, el futuro se ve brillante. "
        "Tiempos emocionantes nos esperan."
    )
    report, _ = analyze(text)
    assert report.score >= 0.5
    assert report.total_findings >= 3


def test_strict_filters_low_severity():
    text = "Por otro lado, esto es importante."
    report_normal, _ = analyze(text, strict=False)
    report_strict, _ = analyze(text, strict=True)
    assert len(report_strict.hits) <= len(report_normal.hits)


def test_em_dash_structural():
    text = "Esto — y eso — y aquello — son ejemplos."
    report, _ = analyze(text, lang="es")
    assert any(f.kind == "em-dash" for f in report.structural)


def test_english_delve_caught():
    text = "Let's delve into the complexities of this tapestry."
    report, lang = analyze(text, lang="en")
    assert lang == "en"
    ids = [h.pattern.id for h in report.hits]
    assert "en.delve" in ids
    assert "en.tapestry" in ids


def test_split_sentences():
    text = "Una. Dos. ¿Tres? ¡Cuatro!"
    assert len(split_sentences(text)) == 4


def test_paragraph_connectors_caught():
    text = (
        "Primer párrafo de prueba con suficiente contenido para no ser filtrado.\n\n"
        "Además, segundo párrafo abre con conector formal AI obvio detectable.\n\n"
        "Por otra parte, tercer párrafo también abre con conector explícito.\n\n"
        "En conclusión, cuarto párrafo cierra con marcador formal típico AI."
    )
    report, _ = analyze(text, lang="es")
    kinds = [f.kind for f in report.structural]
    assert "paragraph-connectors" in kinds


def test_paragraph_symmetry_caught():
    # Five paragraphs with near-identical word count
    para = "Una oración larga con muchas palabras suficientes para tener masa textual y peso evidente. " * 2
    text = "\n\n".join([para] * 5)
    report, _ = analyze(text, lang="es")
    kinds = [f.kind for f in report.structural]
    assert "paragraph-symmetry" in kinds


def test_paragraph_connectors_skipped_for_natural_text():
    """Don't false-flag normal paragraph starts."""
    text = (
        "Ayer salí a caminar. El cielo estaba raro.\n\n"
        "Me encontré con la María. Hablamos de los cabros.\n\n"
        "Volví tarde y cansado."
    )
    report, _ = analyze(text, lang="es")
    kinds = [f.kind for f in report.structural]
    assert "paragraph-connectors" not in kinds


def test_pdf_vocabulary_es():
    """New Pangram-derived ES vocab catches the obvious words."""
    text = (
        "El nuevo paradigma multifacético facilita sinergias robustas. "
        "Adicionalmente, sus capacidades sin fisuras transforman el reino digital."
    )
    report, _ = analyze(text, lang="es")
    ids = {h.pattern.id for h in report.hits}
    assert "es.paradigma" in ids
    assert "es.multifacetico" in ids
    assert "es.adicionalmente" in ids
    assert "es.sin_fisuras" in ids


def test_pdf_vocabulary_en():
    """New Pangram-derived EN vocab catches the obvious words."""
    text = (
        "The robust framework leverages seamless synergies across the realm. "
        "Furthermore, this transformative paradigm utilizes meticulous design."
    )
    report, _ = analyze(text, lang="en")
    ids = {h.pattern.id for h in report.hits}
    assert "en.framework_robust" in ids
    assert "en.seamless" in ids
    assert "en.realm" in ids
    assert "en.transformative" in ids
    assert "en.utilize" in ids


def test_synthetic_academic_spanish_not_missed_when_cliches_are_cleaned():
    """Canary for Memphis-style false negatives: AI text without obvious clichés."""
    text = (
        "La transformación educativa contemporánea requiere comprender la evaluación como un proceso "
        "integral orientado al fortalecimiento de trayectorias formativas diversas. "
        "La incorporación de metodologías activas permite articular dimensiones pedagógicas, institucionales "
        "y culturales que favorecen una experiencia de aprendizaje pertinente. "
        "Esta perspectiva reconoce la complejidad de los contextos escolares y promueve condiciones para "
        "desarrollar capacidades reflexivas en los estudiantes. "
        "La gestión curricular, entendida como práctica colaborativa, contribuye a generar coherencia entre "
        "objetivos, estrategias y evidencias de logro. "
        "Asimismo, la retroalimentación sistemática posibilita identificar avances, ajustar decisiones y "
        "consolidar procesos de mejora continua. "
        "De este modo, la evaluación se configura como una herramienta relevante para orientar aprendizajes "
        "significativos y fortalecer la calidad educativa."
    )
    report, _ = analyze(text, lang="es")
    kinds = {f.kind for f in report.structural}
    assert report.score >= 0.35
    assert "synthetic-academic" in kinds
    assert "low-specificity" in kinds


def test_long_synthetic_academic_spanish_does_not_dilute_to_clean():
    """Long uploads should not hide strong structural AI-smell by adding sentences."""
    synthetic_block = (
        "La transformación educativa contemporánea requiere comprender la evaluación como un proceso "
        "integral orientado al fortalecimiento de trayectorias formativas diversas. "
        "La incorporación de metodologías activas permite articular dimensiones pedagógicas, institucionales "
        "y culturales que favorecen una experiencia de aprendizaje pertinente. "
        "Esta perspectiva reconoce la complejidad de los contextos escolares y promueve condiciones para "
        "desarrollar capacidades reflexivas en los estudiantes. "
        "La gestión curricular contribuye a generar coherencia entre objetivos, estrategias y evidencias de logro. "
    )
    filler = "El apartado mantiene una exposición formal y correcta sin incorporar casos verificables. "
    text = (synthetic_block + filler) * 8
    report, _ = analyze(text, lang="es")
    kinds = {f.kind for f in report.structural}
    assert "synthetic-academic" in kinds
    assert report.sentences >= 30
    assert report.score >= 0.35


def test_report_includes_section_scores():
    text = (
        "Ayer revisé tres cuadernos del 4B en Valparaíso. Dos tenían correcciones reales. "
        "La transformación educativa contemporánea requiere comprender la evaluación como un proceso "
        "integral orientado al fortalecimiento de trayectorias formativas diversas. "
        "La incorporación de metodologías activas permite articular dimensiones pedagógicas, institucionales "
        "y culturales que favorecen una experiencia de aprendizaje pertinente. "
        "De este modo, la evaluación se configura como una herramienta relevante para orientar aprendizajes "
        "significativos y fortalecer la calidad educativa."
    )
    report, _ = analyze(text, lang="es")
    assert [s.name for s in report.sections] == ["apertura", "cuerpo", "cierre"]
    assert report.sections[-1].score >= report.sections[0].score
    assert any("cierre" in s.reasons[0] or s.name == "cierre" for s in report.sections)


def test_canary_dataset_loaded_and_thresholds_hold():
    samples = load_canary_samples()
    assert samples, "canary dataset should not be empty"
    by_name = {s["id"]: s for s in samples}
    assert "es_ai_academic_cleaned" in by_name
    for sample in samples:
        report, _ = analyze(sample["text"], lang=sample.get("lang") or "es")
        assert report.score >= sample["min_score"], sample["id"]
        if "max_score" in sample:
            assert report.score <= sample["max_score"], sample["id"]


def test_sentence_level_vague_claims_flagged_as_context_not_word_only():
    text = (
        "La propuesta permite fortalecer el desarrollo integral de los estudiantes en diversos contextos. "
        "Este proceso contribuye a generar condiciones relevantes para una mejora significativa. "
        "La estrategia favorece capacidades reflexivas y articula dimensiones institucionales pertinentes."
    )
    report, _ = analyze(text, lang="es")
    kinds = {f.kind for f in report.structural}
    assert "vague-sentence-stack" in kinds


def test_stop_slop_english_canaries_catch_cleaned_ai_tells():
    text = (
        "Here's the thing: building products is hard. "
        "Not because the technology is complex. Because people are complex. "
        "Let that sink in. "
        "The complaint becomes a fix. The decision emerges after the conversation moves toward alignment. "
        "The data tells us the market rewards clarity. "
        "Mistakes were made. The decision was reached. "
        "What makes this hard is trust. Why does it matter? Because teams hide confusion. "
        "How this changes work is simple."
    )
    report, _ = analyze(text, lang="en")
    hit_ids = {h.pattern.id for h in report.hits}
    kinds = {f.kind for f in report.structural}
    assert "en.here_is_the_thing" in hit_ids
    assert "en.let_that_sink_in" in hit_ids
    assert "binary-reframe" in kinds
    assert "false-agency" in kinds
    assert "passive-voice" in kinds
    assert "wh-starters" in kinds
    assert report.score >= 0.6


def test_stop_slop_spanish_canaries_catch_cleaned_ai_tells():
    text = (
        "La verdad es que construir productos es difícil. "
        "No porque la tecnología sea compleja. Porque las personas son complejas. "
        "Que eso decante. "
        "La queja se convierte en una mejora. La decisión emerge y la conversación se mueve hacia la claridad. "
        "Los datos nos dicen que el mercado premia la confianza. "
        "Se cometieron errores. La decisión fue tomada. "
        "Qué hace esto difícil es la confianza. Por qué importa? Porque los equipos esconden confusión. "
        "Cómo cambia el trabajo es simple."
    )
    report, _ = analyze(text, lang="es")
    hit_ids = {h.pattern.id for h in report.hits}
    kinds = {f.kind for f in report.structural}
    assert "es.la_verdad_es_que" in hit_ids
    assert "es.que_eso_decante" in hit_ids
    assert "binary-reframe" in kinds
    assert "false-agency" in kinds
    assert "passive-voice" in kinds
    assert "wh-starters" in kinds
    assert report.score >= 0.6


def test_stop_slop_rhetorical_prompts_and_but_reframes():
    en_text = (
        "I'm going to be honest. What if I told you the problem was not speed? "
        "Here's what I mean. It feels like a tooling issue. It's actually a trust issue. "
        "Not a process problem. But a leadership problem. Think about it. And that's okay."
    )
    en_report, _ = analyze(en_text, lang="en")
    en_hit_ids = {h.pattern.id for h in en_report.hits}
    assert "en.going_to_be_honest" in en_hit_ids
    assert "en.what_if_i_told_you" in en_hit_ids
    assert "en.heres_what_i_mean" in en_hit_ids
    assert "en.think_about_it" in en_hit_ids
    assert "en.and_thats_okay" in en_hit_ids
    assert "binary-reframe" in {f.kind for f in en_report.structural}
    assert en_report.score >= 0.6

    es_text = (
        "Voy a ser honesto. Qué pasaría si te dijera que el problema no era la velocidad? "
        "Esto es lo que quiero decir. Parece un problema de herramientas. En realidad es un problema de confianza. "
        "No un problema de proceso. Sino de liderazgo. Piénsalo. Y eso está bien."
    )
    es_report, _ = analyze(es_text, lang="es")
    es_hit_ids = {h.pattern.id for h in es_report.hits}
    assert "es.voy_a_ser_honesto" in es_hit_ids
    assert "es.que_pasaria_si" in es_hit_ids
    assert "es.esto_es_lo_que_quiero_decir" in es_hit_ids
    assert "es.piensalo" in es_hit_ids
    assert "es.y_eso_esta_bien" in es_hit_ids
    assert "binary-reframe" in {f.kind for f in es_report.structural}
    assert es_report.score >= 0.55


def test_markdown_examples_do_not_count_as_author_voice():
    text = (
        "This note explains which phrases the reviewer should avoid.\n\n"
        "> It is worth noting that we should delve into the complexities.\n\n"
        "```\nHope this helps. A rich tapestry stands as a testament to progress.\n```\n\n"
        "Avoid those phrases in drafts and replace them with plain claims."
    )
    report, _ = analyze(text, lang="en")
    hit_ids = {h.pattern.id for h in report.hits}
    assert "en.it_is_worth_noting" not in hit_ids
    assert "en.delve" not in hit_ids
    assert "en.hope_this_helps" not in hit_ids
    assert "en.testament" not in hit_ids
    assert report.score < 0.3


def test_markdown_documentation_shape_is_not_ai_format_by_itself():
    text = """# Tool name

> Short product tagline.

## Install

**pipx:**
```bash
pipx install tool
```

**From source:**
```bash
git clone https://example.invalid/tool.git
```

## Use

```bash
tool draft.md
```

## What it catches

**1. Phrase patterns.** Short explanation with concrete examples in `inline code`.

**2. Structure patterns.** Another short explanation.

**3. Rhythm and shape.** One more short explanation.

## What it does not do

- Does not rewrite for you.
- Does not call an API.

## License

MIT.
"""
    report, _ = analyze(text, lang="en")
    kinds = {f.kind for f in report.structural}
    assert "section-headers" not in kinds
    assert "emphasis-overload" not in kinds
    assert report.score < 0.3


def test_current_readmes_stay_below_moderate():
    root = Path(__file__).resolve().parent.parent
    for filename, lang in [("README.md", "en"), ("README.es.md", "es")]:
        report, _ = analyze((root / filename).read_text(encoding="utf-8"), lang=lang)
        kinds = {f.kind for f in report.structural}
        assert "section-headers" not in kinds, filename
        assert "emphasis-overload" not in kinds, filename
        assert report.score < 0.3, filename


def test_generic_ai_answer_headers_still_flagged():
    text = """# Overview

This guide explains the topic in a broad and polished way.

## Key Takeaways

The main point is that clarity matters across teams.

## The Problem

Teams need alignment across complex decisions.

## The Solution

A structured approach helps everyone move forward.
"""
    report, _ = analyze(text, lang="en")
    assert "section-headers" in {f.kind for f in report.structural}


def test_breathless_inline_emphasis_still_flagged():
    text = (
        "This is **not just faster** but **fundamentally different**. "
        "It creates *real momentum* for **every team** that wants **clarity**."
    )
    report, _ = analyze(text, lang="en")
    assert "emphasis-overload" in {f.kind for f in report.structural}


def test_long_sparse_hits_do_not_become_fake_probability():
    filler = (
        "En 2019 la escuela registró cambios en la asistencia del curso. "
        "La profesora comparó esos datos con entrevistas realizadas en marzo. "
        "El capítulo describe una decisión institucional y sus efectos observables. "
        "La evidencia aparece vinculada a fechas, actores y documentos concretos. "
    )
    marked = "Cabe mencionar que este apartado introduce una transición formal. "
    text = " ".join([filler] * 55 + [marked] * 15)
    report, _ = analyze(text, lang="es")
    assert report.sentences >= 200
    assert len(report.hits) >= 15
    assert report.score <= 0.34


def test_docx_structural_comments_use_readable_labels_not_internal_kinds():
    from aismell.core import StructuralFinding
    from aismell.docx import _format_structural_comment

    comment = _format_structural_comment(
        StructuralFinding(
            line=0,
            kind="negative-listing",
            severity=2,
            message="listado negativo antes del punto",
            suggestion="di primero la tesis central",
        ),
        "es",
    )
    assert "negative-listing" not in comment
    assert "lista negativa" in comment
    assert "Qué cambiar" in comment


if __name__ == "__main__":
    failed = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  ✓ {name}")
            except AssertionError as e:
                print(f"  ✗ {name}: {e}")
                failed += 1
            except Exception as e:
                print(f"  ✗ {name}: {type(e).__name__}: {e}")
                failed += 1
    if failed:
        print(f"\n{failed} failed")
        sys.exit(1)
    print("\nall tests passed")
