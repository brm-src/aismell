"""Behavioral canaries for YAML regex escaping (synthetic prose only)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aismell.core import analyze, load_patterns


# One natural-language match for every previously overescaped rule.
CASES = (
    ("es.sirve_como", "El edificio sirve como un testimonio del cambio."),
    ("es.cuenta_con", "El museo cuenta con una amplia colección."),
    ("es.marca_un_hito", "El acuerdo marca un hito en la región."),
    ("es.pone_de_relieve", "El informe pone de relieve el problema."),
    ("es.a_pesar_desafios", "A pesar de estos desafíos, seguimos."),
    ("es.afronta_desafios", "El equipo enfrenta múltiples desafíos."),
    ("es.futuras_direcciones", "Revisamos las perspectivas futuras."),
    ("es.cobertura_medios", "Fue cubierta por medios de comunicación."),
    ("es.presencia_digital", "El museo mantiene una activa presencia digital."),
    ("es.evidencia_concreta", "Necesitamos evidencia concreta."),
    ("es.sienta_las_bases", "El acuerdo sienta las bases para crecer."),
    ("es.huella_indeleble", "La obra deja una huella indeleble."),
    ("es.arraigado_profundamente", "El hábito está profundamente arraigado."),
    ("es.suscitado_debate", "El cambio ha suscitado debate sobre el horario."),
    ("es.contexto_mas_amplio", "El cambio se inserta en un contexto más amplio."),
    ("es.calco_darle_vida", "Queremos darle vida a la idea."),
    ("es.calco_a_la_vez_que", "Trabajamos a la vez que aprendemos."),
    ("es.en_el_ambito", "El cambio ocurre en el ámbito de la educación."),
    ("es.es_relevante", "El resultado es especialmente relevante."),
    ("es.no_es_casualidad", "No es casualidad que funcione."),
    ("es.calco_donde_la_magia", "Es aquí donde sucede la magia."),
    ("en.boasts_a", "The museum boasts a large collection."),
    ("en.features_verb", "The museum offers a collection including maps."),
    ("en.not_but_direct", "It is not a tool but a mirror of this society."),
    ("en.not_merely", "Not merely a tool, it is a mirror."),
    ("en.more_than_just", "It is more than just a tool; this changes work."),
    ("en.independent_coverage", "It was covered by local media."),
    ("en.faces_challenges", "The team faces several challenges."),
    ("en.indelible_mark", "The work left an indelible mark."),
    ("en.deeply_rooted", "The habit is deeply rooted."),
    ("en.shaped_discussions", "The work sparked debate about the schedule."),
    ("en.broader_context", "Consider the broader context."),
    ("en.key_takeaways", "These are the key takeaways."),
    ("en.turn0search", "See turn0search12 for details."),
    ("en.placeholder_date", "Published on 2026-XX-XX."),
)
PATTERNS = {p.id: p for lang in ("es", "en") for p in load_patterns(lang)}


@pytest.mark.parametrize("pattern_id,text", CASES, ids=[case[0] for case in CASES])
def test_yaml_rule_matches_prose(pattern_id, text):
    # Compile the actual loaded rule: analyze() may suppress overlapping IDs.
    pattern = PATTERNS[pattern_id]
    assert pattern.compile().search(text), pattern_id
    assert not pattern.compile().search("Ayer cerré la puerta. Yesterday I closed the door.")


@pytest.mark.parametrize("pattern_id,text", (
    ("es.sirve_como", "Sirve como ejemplo."),
    ("es.cuenta_con", "Cuenta con amplia variedad."),
    ("es.cobertura_medios", "Fue perfilada en publicaciones nacionales."),
    ("es.evidencia_concreta", "Debemos exigir ejemplos concretos."),
    ("es.futuras_direcciones", "Desafíos y oportunidades."),
    ("es.calco_donde_la_magia", "Donde la magia sucede."),
    ("en.turn0search", "contentReference[oaicite:12]"),
    ("en.turn0search", "oai_citation:12"),
    ("en.turn0search", '{"attribution":{"attributableIndex":1}}'),
    ("en.turn0search", "【12†source】"),
    ("en.turn0search", "[attached_file:12]"),
    ("en.turn0search", "[cite: 12, 13]"),
    ("en.turn0search", ':::writing{variant="email"}'),
))
def test_other_escaped_branches(pattern_id, text):
    assert PATTERNS[pattern_id].compile().search(text), pattern_id


@pytest.mark.parametrize("lang,pattern_id,text,matched", (
    ("en", "en.boasts_a", "The museum boasts a collection.", "boasts a"),
    ("en", "en.boasts_a", "The museum BOASTS\tan archive.", "BOASTS\ta"),
    ("es", "es.marca_un_hito", "El acuerdo marca un hito en la región.", "marca un hito en "),
    ("es", "es.marca_un_hito", "El acuerdo representa un hito para todos.", "representa un hito para "),
    ("es", "es.marca_un_hito", "El acuerdo constituye un hito dentro de la región.", "constituye un hito dentro de"),
))
def test_real_analysis_preserves_spans(lang, pattern_id, text, matched):
    report, _ = analyze(text, lang=lang, include_segments=False)
    hit = next((hit for hit in report.hits if hit.pattern.id == pattern_id), None)
    assert hit is not None, pattern_id
    assert hit.matched == matched
    assert text[hit.col:hit.end] == matched
    prefixed = text[:hit.col] + "x" + text[hit.col:]
    assert not PATTERNS[pattern_id].compile().search(prefixed)
