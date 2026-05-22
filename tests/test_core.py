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
