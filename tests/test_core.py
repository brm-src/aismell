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


def test_storyscope_discourse_signals_catch_overexplained_theme():
    text = (
        "La puerta quedó abierta toda la noche y nadie quiso decir quién había salido primero. "
        "La escena mostraba una tensión pequeña, casi doméstica, entre el miedo y la costumbre.\n\n"
        "El tema de la historia era la esperanza, pero también la lección de aprender a confiar. "
        "En el fondo, esto nos recuerda que la humanidad necesita un propósito compartido.\n\n"
        "Cada personaje comprendió una verdad profunda sobre el significado de sus actos. "
        "La moraleja apareció cuando dejaron de buscar redención fuera de sí mismos.\n\n"
        "Al final, aprendió que lo que realmente importaba era la esperanza. "
        "Desde ese momento comenzó un nuevo comienzo para todos."
    )
    report, _ = analyze(text, lang="es")
    kinds = {f.kind for f in report.structural}
    assert "discourse-overexplained-theme" in kinds
    assert "discourse-tidy-resolution" in kinds


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
    assert "lista negativa" not in comment
    assert "Prueba a decir primero la tesis central." in comment
    assert "Qué cambiar" not in comment


def test_docx_hit_comments_sound_like_editorial_notes_in_both_languages():
    from aismell.core import Hit, Pattern
    from aismell.docx import _format_hit_comment

    pattern = Pattern(
        id="es.cabe_mencionar",
        kind="phrase",
        severity=3,
        pattern="cabe mencionar",
        message="unused",
        suggestion="menciónalo sin anunciarlo",
    )
    hit = Hit(line=1, col=0, end=14, text="Cabe mencionar esto.", matched="Cabe mencionar", pattern=pattern)
    es_comment = _format_hit_comment(hit, "es")
    en_pattern = Pattern(
        id="en.it_is_worth_noting",
        kind="phrase",
        severity=3,
        pattern="it is worth noting",
        message="unused",
        suggestion="just note it",
    )
    en_hit = Hit(line=1, col=0, end=18, text="It is worth noting this.", matched="It is worth noting", pattern=en_pattern)
    en_comment = _format_hit_comment(en_hit, "en")
    assert es_comment == "«Cabe mencionar» pertenece a una fórmula muy gastada de ese registro. Menciónalo sin anunciarlo."
    assert en_comment == "“It is worth noting” can make the writing feel generic. Just note it."
    assert "Hallazgo:" not in es_comment
    assert "What to change:" not in en_comment


def test_example_ai_copy_scores_high_not_moderate():
    text = (
        "En el mundo actual, la inteligencia artificial se ha convertido en una herramienta fundamental "
        "para abordar los desafíos del siglo XXI. Desde la salud hasta la educación, sus aplicaciones "
        "son prácticamente ilimitadas y prometen transformar profundamente la forma en que vivimos y trabajamos. "
        "Es fundamental comprender que la IA no es solo una tecnología, sino un cambio de paradigma que requiere "
        "una reflexión ética profunda. Diversos expertos coinciden en que su desarrollo debe guiarse por principios "
        "sólidos de transparencia, equidad y responsabilidad. En conclusión, el futuro de la inteligencia artificial "
        "dependerá de nuestra capacidad colectiva para equilibrar innovación y regulación. Solo a través de un diálogo "
        "abierto y multidisciplinar podremos garantizar que esta tecnología beneficie a toda la humanidad."
    )
    report, _ = analyze(text, lang="es")
    assert report.sentences >= 4
    assert len(report.hits) >= 5
    assert report.score >= 0.60
    assert report.severity_label == "alto"


# ===================== humanizer v2.9.1 + stop-slop gaps (2026-08) =====================

def test_humanizer_speculative_gap_fill_en():
    text = (
        "Information about her early life is not publicly available, suggesting she "
        "maintains a low profile and keeps personal details private. "
        "It is believed that she likely grew up in a middle-class household."
    )
    report, _ = analyze(text, lang="en")
    ids = {h.pattern.id for h in report.hits}
    assert "en.gapfill_not_public" in ids
    assert "en.gapfill_low_profile" in ids
    assert "en.gapfill_it_is_believed" in ids


def test_humanizer_speculative_gap_fill_es():
    text = (
        "La información sobre su vida temprana no es información pública, lo que sugiere "
        "que mantiene un perfil bajo y resguarda su vida privada. "
        "Se cree que probablemente creció en un hogar de clase media."
    )
    report, _ = analyze(text, lang="es")
    ids = {h.pattern.id for h in report.hits}
    assert "es.gapfill_info_publica" in ids
    assert "es.gapfill_perfil_bajo" in ids
    assert "es.gapfill_se_cree" in ids


def test_humanizer_weasel_attributions_en():
    text = (
        "Experts argue that the policy is ineffective. "
        "Industry reports suggest adoption is slowing. "
        "Observers have cited several sources."
    )
    report, _ = analyze(text, lang="en")
    ids = {h.pattern.id for h in report.hits}
    assert "en.weasel_experts" in ids
    assert "en.weasel_industry" in ids
    assert "en.weasel_observers" in ids


def test_humanizer_weasel_attributions_es():
    text = (
        "Los expertos afirman que la política es ineficaz. "
        "Informes de la industria sugieren que la adopción se desacelera. "
        "Algunos críticos señalan que falta evidencia."
    )
    report, _ = analyze(text, lang="es")
    ids = {h.pattern.id for h in report.hits}
    assert "es.weasel_expertos" in ids
    assert "es.weasel_informes" in ids
    assert "es.weasel_criticos" in ids


def test_humanizer_ing_tackon_en():
    text = (
        "The temple uses blue, green and gold, symbolizing the local landscape, "
        "reflecting the community's bond with the land, ensuring a lasting legacy."
    )
    report, _ = analyze(text, lang="en")
    ids = {h.pattern.id for h in report.hits}
    assert "en.ing_tackon" in ids


def test_humanizer_gerundio_colgado_es():
    text = (
        "El templo usa azul, verde y oro, simbolizando el paisaje local, "
        "reflejando el vínculo de la comunidad con la tierra, asegurando un legado duradero."
    )
    report, _ = analyze(text, lang="es")
    ids = {h.pattern.id for h in report.hits}
    assert "es.gerundio_colgado" in ids


def test_humanizer_aphorism_formulas_en():
    text = (
        "Symmetry is the language of trust. "
        "Attention is the currency of leadership. "
        "Consistency is the architecture of reliability."
    )
    report, _ = analyze(text, lang="en")
    ids = {h.pattern.id for h in report.hits}
    assert "en.aphorism_language_of" in ids
    assert "en.aphorism_currency_of" in ids
    assert "en.aphorism_architecture_of" in ids


def test_humanizer_aphorism_formulas_es():
    text = (
        "La simetría es el lenguaje de la confianza. "
        "La atención es la moneda del liderazgo."
    )
    report, _ = analyze(text, lang="es")
    ids = {h.pattern.id for h in report.hits}
    assert "es.aphorism_lenguaje_de" in ids
    assert "es.aphorism_moneda_de" in ids


def test_humanizer_conversational_openers_en():
    text = (
        "The thing is, we keep postponing the decision. "
        "Let's be honest: nobody reads the report. "
        "Real talk, this needs a different owner."
    )
    report, _ = analyze(text, lang="en")
    ids = {h.pattern.id for h in report.hits}
    assert "en.opener_the_thing_is" in ids
    assert "en.opener_lets_be_honest" in ids
    assert "en.opener_real_talk" in ids


def test_humanizer_conversational_openers_es():
    text = (
        "La cosa es que seguimos postergando la decisión. "
        "Seamos honestos: nadie lee el informe. "
        "Hablemos claro, esto necesita otro responsable."
    )
    report, _ = analyze(text, lang="es")
    ids = {h.pattern.id for h in report.hits}
    assert "es.opener_la_cosa_es" in ids
    assert "es.opener_seamos_honestos" in ids
    assert "es.opener_hablemos_claro" in ids


def test_humanizer_persuasive_authority_en():
    text = (
        "The real question is whether teams can adapt. "
        "What really matters is organizational readiness. "
        "The deeper issue is trust, the heart of the matter."
    )
    report, _ = analyze(text, lang="en")
    ids = {h.pattern.id for h in report.hits}
    assert "en.authority_real_question" in ids
    assert "en.authority_what_really_matters" in ids
    assert "en.authority_deeper_issue" in ids


def test_humanizer_persuasive_authority_es():
    text = (
        "La verdadera pregunta es si los equipos pueden adaptarse. "
        "Lo que realmente importa es la disposición organizacional. "
        "El verdadero asunto es la confianza, el meollo del asunto."
    )
    report, _ = analyze(text, lang="es")
    ids = {h.pattern.id for h in report.hits}
    assert "es.authority_verdadera_pregunta" in ids
    assert "es.authority_realmente_importa" in ids
    assert "es.authority_meollo" in ids


def test_humanizer_signposting_en():
    text = (
        "Let's explore how caching works. "
        "Here's what you need to know before you start. "
        "Without further ado, here is the plan."
    )
    report, _ = analyze(text, lang="en")
    ids = {h.pattern.id for h in report.hits}
    assert "en.signpost_lets_explore" in ids
    assert "en.signpost_heres_what_you_need" in ids
    assert "en.signpost_without_ado" in ids


def test_humanizer_signposting_es():
    text = (
        "Vamos a explorar cómo funciona el caché. "
        "Esto es lo que necesitas saber antes de empezar. "
        "Sin más preámbulo, este es el plan."
    )
    report, _ = analyze(text, lang="es")
    ids = {h.pattern.id for h in report.hits}
    assert "es.signpost_vamos_a_explorar" in ids
    assert "es.signpost_lo_que_necesitas" in ids
    assert "es.signpost_sin_preambulo" in ids


def test_stop_slop_meta_joiners_en():
    text = (
        "In this essay, I argue that habits matter. "
        "As we'll see, the evidence supports this. "
        "Let me walk you through the data. "
        "The rest of this essay explains the method."
    )
    report, _ = analyze(text, lang="en")
    ids = {h.pattern.id for h in report.hits}
    assert "en.metajoiner_in_essay" in ids
    assert "en.metajoiner_as_we_see" in ids
    assert "en.metajoiner_walk_through" in ids
    assert "en.metajoiner_rest_of_essay" in ids


def test_stop_slop_meta_joiners_es():
    text = (
        "En este ensayo sostengo que los hábitos importan. "
        "Como veremos, la evidencia lo respalda. "
        "Déjame guiarte por los datos. "
        "El resto de este ensayo explica el método."
    )
    report, _ = analyze(text, lang="es")
    ids = {h.pattern.id for h in report.hits}
    assert "es.metajoiner_en_ensayo" in ids
    assert "es.metajoiner_como_veremos" in ids
    assert "es.metajoiner_dejame_guiar" in ids
    assert "es.metajoiner_resto_ensayo" in ids


def test_stop_slop_feature_not_bug_en_es():
    en_report, _ = analyze("That quirk is a feature, not a bug.", lang="en")
    assert "en.feature_not_bug" in {h.pattern.id for h in en_report.hits}
    es_report, _ = analyze("Ese detalle es una característica, no un error.", lang="es")
    assert "es.feature_not_bug" in {h.pattern.id for h in es_report.hits}


def test_stop_slop_vague_declaratives_en_es():
    en_report, _ = analyze(
        "The stakes are high. The implications are significant. The consequences are real.",
        lang="en",
    )
    ids = {h.pattern.id for h in en_report.hits}
    assert "en.vague_stakes" in ids
    assert "en.vague_implications" in ids

    es_report, _ = analyze(
        "Las apuestas son altas. Las implicancias son significativas. Las consecuencias son reales.",
        lang="es",
    )
    ids = {h.pattern.id for h in es_report.hits}
    assert "es.vague_apuestas" in ids
    assert "es.vague_implicancias" in ids


def test_stop_slop_fillers_en_es():
    en_report, _ = analyze(
        "In order to succeed, due to the fact that time is short, the system has the ability to adapt.",
        lang="en",
    )
    ids = {h.pattern.id for h in en_report.hits}
    assert "en.filler_in_order_to" in ids
    assert "en.filler_due_to_fact" in ids
    assert "en.filler_has_ability" in ids

    es_report, _ = analyze(
        "Con el fin de avanzar, debido al hecho de que el tiempo escasea, el sistema tiene la capacidad de adaptarse.",
        lang="es",
    )
    ids = {h.pattern.id for h in es_report.hits}
    assert "es.filler_con_el_fin" in ids
    assert "es.filler_debido_hecho" in ids
    assert "es.filler_tiene_capacidad" in ids


def test_stop_slop_business_jargon_en():
    text = (
        "We need to lean into the change, double down on focus, "
        "and take a deep dive into the data before we circle back."
    )
    report, _ = analyze(text, lang="en")
    ids = {h.pattern.id for h in report.hits}
    assert "en.jargon_lean_into" in ids
    assert "en.jargon_double_down" in ids
    assert "en.jargon_circle_back" in ids
    # "deep dive" may surface as en.dive_in or en.jargon_deep_dive depending
    # on which pattern fires first — both mean the same jargon tic.
    assert "en.dive_in" in ids or "en.jargon_deep_dive" in ids


def test_humanizer_ai_vocab_extra_en():
    text = (
        "The proposal aims to garner support and enhance outcomes. "
        "Its enduring value shapes the technological landscape."
    )
    report, _ = analyze(text, lang="en")
    ids = {h.pattern.id for h in report.hits}
    assert "en.vocab_garner" in ids
    assert "en.vocab_enhance" in ids
    assert "en.vocab_enduring" in ids
    assert "en.vocab_landscape_of" in ids


def test_humanizer_ai_vocab_extra_es():
    text = (
        "La propuesta busca granjear apoyo y potenciar los resultados. "
        "Su valor perdurable configura el paisaje del campo."
    )
    report, _ = analyze(text, lang="es")
    ids = {h.pattern.id for h in report.hits}
    assert "es.vocab_granjear" in ids
    assert "es.vocab_potenciar" in ids
    assert "es.vocab_perdurable" in ids


def test_humanizer_promotional_extra_en():
    text = (
        "The hotel exemplifies local craft. This renowned landmark offers breathtaking views "
        "and is a must-visit stop."
    )
    report, _ = analyze(text, lang="en")
    ids = {h.pattern.id for h in report.hits}
    assert "en.promo_exemplifies" in ids
    assert "en.promo_renowned" in ids
    assert "en.promo_breathtaking" in ids
    assert "en.promo_must_visit" in ids


def test_humanizer_promotional_extra_es():
    text = (
        "El hotel ejemplifica la artesanía local. Este renombrado hito ofrece vistas deslumbrantes "
        "y es una parada imperdible."
    )
    report, _ = analyze(text, lang="es")
    ids = {h.pattern.id for h in report.hits}
    assert "es.promo_ejemplifica" in ids
    assert "es.promo_renombrado" in ids
    assert "es.promo_deslumbrante" in ids
    assert "es.promo_imperdible" in ids


def test_humanizer_collaborative_artifacts_en():
    text = (
        "Want me to expand this section? Should I continue? "
        "Would you like me to add more examples?"
    )
    report, _ = analyze(text, lang="en")
    ids = {h.pattern.id for h in report.hits}
    assert "en.chatbot_want_me_to" in ids
    assert "en.chatbot_should_i_continue" in ids
    assert "en.chatbot_would_you_like_me" in ids


# ---- structural: humanizer v2.9.1 §14/§26/§29/§31/§33 + stop-slop adverbs ----


def test_en_dash_and_spaced_em_dash_flagged():
    text = "This is a test – with en dashes – in a row. And another -- spaced -- pair."
    report, _ = analyze(text, lang="en")
    assert any(f.kind == "em-dash" for f in report.structural)


def test_staccato_runs_flagged():
    text = (
        "It had no preference. No aesthetic prior. No nostalgia. "
        "No memories at all. The old rules were gone."
    )
    report, _ = analyze(text, lang="en")
    assert any(f.kind == "staccato-runs" for f in report.structural)


def test_staccato_runs_not_flagged_for_natural_text():
    text = (
        "The market opened flat on Tuesday. Analysts pointed to the earnings report "
        "released the night before. By noon, most of the losses had been recovered."
    )
    report, _ = analyze(text, lang="en")
    assert not any(f.kind == "staccato-runs" for f in report.structural)


def test_hyphenated_pairs_density_flagged_en():
    text = (
        "The cross-functional team delivered a high-quality, data-driven, real-time report. "
        "The decision-making process was end-to-end and well-known for being long-term."
    )
    report, _ = analyze(text, lang="en")
    assert any(f.kind == "hyphenated-pairs" for f in report.structural)


def test_hyphenated_pairs_not_flagged_es():
    text = (
        "El equipo multifuncional entregó un informe de alta calidad basado en datos en tiempo real. "
        "El proceso de toma de decisiones era conocido por ser de largo plazo."
    )
    report, _ = analyze(text, lang="es")
    assert not any(f.kind == "hyphenated-pairs" for f in report.structural)


def test_adverb_density_flagged_en():
    text = (
        "It is literally true that this genuinely matters. "
        "Honestly, this is simply the most important thing. "
        "Actually, this truly changes everything fundamentally."
    )
    report, _ = analyze(text, lang="en")
    assert any(f.kind == "adverb-density" for f in report.structural)


def test_adverb_density_flagged_es():
    text = (
        "Verdaderamente, esto es fundamentalmente importante. "
        "Genuinamente, el proceso es inherentemente complejo e inevitablemente lento."
    )
    report, _ = analyze(text, lang="es")
    assert any(f.kind == "adverb-density" for f in report.structural)


def test_adverb_density_not_flagged_for_natural_text():
    text = (
        "Ayer salí a caminar por la costanera. El viento estaba fuerte y el mar se veía gris. "
        "Volví temprano porque empezó a llover."
    )
    report, _ = analyze(text, lang="es")
    assert not any(f.kind == "adverb-density" for f in report.structural)


def test_fragmented_headers_flagged():
    text = (
        "## Performance\n\n"
        "Speed matters.\n\n"
        "When users hit a slow page, they leave immediately and never come back."
    )
    report, _ = analyze(text, lang="en")
    assert any(f.kind == "fragmented-headers" for f in report.structural)


def test_fragmented_headers_not_flagged_when_no_restatement():
    text = (
        "## Performance\n\n"
        "When users hit a slow page, they leave immediately and never come back."
    )
    report, _ = analyze(text, lang="en")
    assert not any(f.kind == "fragmented-headers" for f in report.structural)


def test_emoji_decorated_headers_flagged():
    text = (
        "🚀 **Launch Phase:** The product launches in Q3.\n"
        "💡 **Key Insight:** Users prefer simplicity.\n"
        "✅ **Next Steps:** Schedule the follow-up meeting."
    )
    report, _ = analyze(text, lang="en")
    assert any(f.kind == "emoji-headers" for f in report.structural)


def test_tailing_negation_flagged_en():
    text = (
        "The options come from the selected item, no guessing. "
        "The pipeline runs in the background, no wasted motion."
    )
    report, _ = analyze(text, lang="en")
    assert any(f.kind == "tailing-negation" for f in report.structural)


def test_humanizer_new_families_raise_score_en():
    text = (
        "Experts argue the change is overdue. The real question is whether teams can adapt. "
        "The thing is, attention is the currency of leadership, no guessing. "
        "It is believed that the stakes are high. Let's explore what really matters."
    )
    report, _ = analyze(text, lang="en")
    assert report.score >= 0.45


def test_humanizer_new_families_raise_score_es():
    text = (
        "Los expertos afirman que el cambio es urgente. La verdadera pregunta es si los equipos pueden adaptarse. "
        "La cosa es que la atención es la moneda del liderazgo. "
        "Se cree que las apuestas son altas. Vamos a explorar lo que realmente importa."
    )
    report, _ = analyze(text, lang="es")
    assert report.score >= 0.45


# ===================== scoring: overlapping hits + short-text calibration (2026-08) =====================


def test_overlapping_patterns_count_once():
    """One phrase matching 3 pattern families must produce 1 finding, not 3."""
    text = "This is not just a tool but also a mirror of the culture."
    report, _ = analyze(text, lang="en")
    overlapping = [h for h in report.hits if "not just" in h.matched.lower() or "not only" in h.matched.lower()]
    assert len(overlapping) == 1, f"expected 1 deduped hit, got {len(overlapping)}: {[h.pattern.id for h in overlapping]}"


def test_overlapping_patterns_count_once_es():
    text = "Esto no es solo una herramienta, sino también un espejo de la cultura."
    report, _ = analyze(text, lang="es")
    overlapping = [h for h in report.hits if "no es solo" in h.matched.lower() or "no solo" in h.matched.lower()]
    assert len(overlapping) == 1, f"expected 1 deduped hit, got {len(overlapping)}: {[h.pattern.id for h in overlapping]}"


def test_short_text_score_capped_below_high():
    """A 3-sentence text with a few hits must NOT reach 'suena a IA'."""
    text = (
        "Vale la pena destacar que esto se erige como un testimonio. "
        "En última instancia, el futuro se ve brillante. "
        "Tiempos emocionantes nos esperan."
    )
    report, _ = analyze(text, lang="es")
    assert report.score <= 0.60, f"short text score {report.score:.2f} is too high"
    assert report.severity_label != "alto", "3-sentence text must not be labeled high"


def test_very_short_text_never_high():
    """2 sentences with 2 strong hits cannot produce a confident high verdict."""
    text = "En el mundo actual, el futuro se ve brillante y el panorama es dinámico."
    report, _ = analyze(text, lang="es")
    assert report.score <= 0.60


def test_long_text_still_can_reach_high():
    """Long dense AI text must still be able to reach high — the cap only hurts short texts."""
    block = (
        "En el mundo actual, la inteligencia artificial se ha convertido en una herramienta fundamental "
        "para abordar los desafíos del siglo XXI. Desde la salud hasta la educación, sus aplicaciones "
        "son prácticamente ilimitadas y prometen transformar profundamente la forma en que vivimos y trabajamos. "
        "Es fundamental comprender que la IA no es solo una tecnología, sino un cambio de paradigma que requiere "
        "una reflexión ética profunda. Diversos expertos coinciden en que su desarrollo debe guiarse por principios "
        "sólidos de transparencia, equidad y responsabilidad. En conclusión, el futuro de la inteligencia artificial "
        "dependerá de nuestra capacidad colectiva para equilibrar innovación y regulación. "
    )
    report, _ = analyze(block * 3, lang="es")
    assert report.sentences >= 12
    assert report.score >= 0.60, f"long dense text should still hit high, got {report.score:.2f}"


def test_curated_no_ai_slop_gaps_en():
    """Import only compound no-ai-slop frames; ordinary prose stays clean."""
    text = (
        "In a nutshell, the proposal changes the filing date. "
        "Needless to say, the old date no longer applies. "
        "As you can see, the table has one row. "
        "With that in mind, the team chose Friday. "
        "In the same vein, the second office chose Friday. "
        "The bottom line is that the change is small."
    )
    report, lang = analyze(text, lang="en")
    assert lang == "en"
    ids = {hit.pattern.id for hit in report.hits}
    assert {
        "en.stop_slop_in_a_nutshell",
        "en.stop_slop_needless_to_say",
        "en.stop_slop_as_you_can_see",
        "en.stop_slop_with_that_in_mind",
        "en.stop_slop_same_vein",
        "en.stop_slop_bottom_line",
    } <= ids


def test_curated_no_ai_slop_gaps_es():
    """Spanish equivalents are editorial signals, not certainty claims."""
    text = (
        "No hace falta decirlo: la fecha anterior ya no aplica. "
        "Como puedes ver, la tabla tiene una fila. "
        "Con esto en mente, el equipo eligió el viernes. "
        "En la misma línea, la segunda oficina eligió el viernes. "
        "En el mundo acelerado de hoy, la decisión parece urgente. "
        "La conclusión es que el cambio es pequeño."
    )
    report, lang = analyze(text, lang="es")
    assert lang == "es"
    ids = {hit.pattern.id for hit in report.hits}
    assert {
        "es.stop_slop_no_hace_falta_decirlo",
        "es.stop_slop_como_puedes_ver",
        "es.stop_slop_con_esto_en_mente",
        "es.stop_slop_en_la_misma_linea",
        "es.stop_slop_mundo_acelerado",
        "es.stop_slop_la_conclusion_es",
    } <= ids


def test_curated_no_ai_slop_does_not_blacklist_common_words():
    """The integration must not add isolated words such as very/really/in addition."""
    text = (
        "The very small change is really useful. In addition, it fixes the import. "
        "The team wrote a short note with the exact reason."
    )
    report, _ = analyze(text, lang="en")
    imported_ids = {hit.pattern.id for hit in report.hits if hit.pattern.id.startswith("en.stop_slop_")}
    assert imported_ids == set()


def test_curated_no_ai_slop_patterns_have_unique_ids_and_valid_yaml():
    """Both pattern files remain loadable and the imported IDs stay unique."""
    from aismell.core import load_patterns

    for lang in ("en", "es"):
        patterns = load_patterns(lang)
        ids = [pattern.id for pattern in patterns if pattern.id.startswith(f"{lang}.stop_slop_")]
        assert ids
        assert len(ids) == len(set(ids))
        for pattern in patterns:
            pattern.compile()


# ===================== era detection + academic register (2026-08) =====================


def test_pre_llm_text_capped_and_noted():
    """A formal academic text from 2016 (pre-LLM) must not reach 'alto' — and
    the report must explain why the register isn't an AI signal."""
    text = (
        "En este sentido, se trata de transitar desde un currículum de verdadera raíz democrática (Asimeng-Boahene, 2007). "
        "Se sostiene que las controversias capturan el interés de los estudiantes (Carr, 2011). "
        "En primer lugar, los sujetos críticos se forman en el diálogo. En segundo lugar, la pedagogía crítica "
        "reniega del adoctrinamiento (Sánchez y Torres, 2009). "
        "No obstante, hay docentes que resisten. Por lo tanto, la formación docente exige un debate abierto. "
        "En síntesis, la propuesta se orienta a un currículum controversial (Magendzo, 2006)."
    )
    report, _ = analyze(text, lang="es")
    assert report.era == "pre-llm", f"expected pre-llm era, got {report.era}"
    assert report.era_max_year == 2011
    assert report.score <= 0.30, f"pre-LLM text scored {report.score:.2f}"
    assert report.severity_label != "alto"
    assert any("antes del lanzamiento" in n for n in report.notes), "expected era note"


def test_pre_llm_connector_heavy_academic_capped():
    """Connector-heavy academic prose from 2016 with citations must be dampened
    by BOTH era and academic-register logic."""
    text = (
        "En este sentido, la reforma educativa enfrenta resistencias (Carr, 2011). "
        "No obstante, los docentes se forman en el diálogo (Moss, 2000). "
        "En primer lugar, se trata de un proceso complejo. En segundo lugar, exige tiempo. "
        "Por lo tanto, la política debe acompañar el cambio. En síntesis, la evidencia lo respalda (Magendzo, 2006)."
    )
    report, _ = analyze(text, lang="es")
    assert report.score <= 0.30, f"pre-LLM academic text scored {report.score:.2f}"
    assert report.era == "pre-llm"


def test_era_auto_detects_post_llm():
    """A text mentioning recent years is not era-capped."""
    text = (
        "En 2024, los modelos de lenguaje transformaron la educación (García, 2023). "
        "Los expertos afirman que el cambio es urgente. La verdadera pregunta es si los equipos pueden adaptarse. "
        "La cosa es que la atención es la moneda del liderazgo. "
        "Se cree que las apuestas son altas. Vamos a explorar lo que realmente importa."
    )
    report, _ = analyze(text, lang="es")
    assert report.era == "post-llm", f"expected post-llm, got {report.era}"
    assert report.score >= 0.45, f"post-LLM text should not be era-capped, got {report.score:.2f}"


def test_era_param_override():
    """User override: forcing pre-llm caps even when no years are in the text."""
    text = "Los expertos afirman que el cambio es urgente. La cosa es que la atención es la moneda del liderazgo."
    report, _ = analyze(text, lang="es", era="pre-llm")
    assert report.era == "pre-llm"
    assert report.score <= 0.30


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
