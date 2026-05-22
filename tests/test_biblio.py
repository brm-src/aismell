"""Smoke tests for bibliography heuristics."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import aismell.biblio as biblio
from aismell.biblio import find_references, score_apa_reference, verify_citation, verify_citation_semantic_scholar


def test_apa_reference_score_catches_missing_core_parts():
    refs = find_references("Pérez, J. (2021). Evaluación formativa en escuelas rurales.")
    assert refs
    score = score_apa_reference(refs[0])
    assert score.status == "suspicious"
    assert any("fuente" in issue for issue in score.issues)


def test_apa_reference_score_accepts_richer_reference():
    refs = find_references(
        "Pérez, J. (2021). Evaluación formativa en escuelas rurales. Revista Chilena de Educación, 12(2), 45-63."
    )
    assert refs
    score = score_apa_reference(refs[0])
    assert score.status == "plausible"
    assert score.score >= 0.7


def test_citation_without_doi_can_exist_via_openalex():
    refs = find_references("Freire, P. (1970). Pedagogy of the oppressed. Continuum.")
    ref = refs[0]

    def fake_fetch_json(url, timeout=8.0):
        if "api.crossref.org" in url:
            return {"message": {"items": []}}
        if "api.openalex.org" in url:
            return {"results": [{"display_name": "Pedagogy of the oppressed", "publication_year": 1970}]}
        return None

    old = biblio._fetch_json
    biblio._fetch_json = fake_fetch_json
    try:
        res = verify_citation(ref)
    finally:
        biblio._fetch_json = old
    assert res.status == "exists"
    assert "OpenAlex" in res.detail


def test_isbn_verifies_with_openlibrary():
    def fake_fetch_json(url, timeout=8.0):
        assert "openlibrary.org/isbn" in url
        return {"title": "Pedagogy of the Oppressed"}

    old = biblio._fetch_json
    biblio._fetch_json = fake_fetch_json
    try:
        refs = find_references("ISBN 978-0-8264-1276-8")
        res = biblio.verify_isbn(refs[0].identifier)
    finally:
        biblio._fetch_json = old
    assert res.status == "exists"


def test_citation_without_doi_can_exist_via_semantic_scholar():
    refs = find_references("Freire, P. (1970). Pedagogy of the oppressed. Continuum.")
    ref = refs[0]

    def fake_fetch_json(url, timeout=8.0):
        assert "semanticscholar.org" in url
        return {"data": [{"title": "Pedagogy of the oppressed", "year": 1970}]}

    old = biblio._fetch_json
    biblio._fetch_json = fake_fetch_json
    try:
        res = verify_citation_semantic_scholar(ref)
    finally:
        biblio._fetch_json = old
    assert res.status == "exists"
    assert "Semantic Scholar" in res.detail


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
    print("\nbiblio tests passed")
