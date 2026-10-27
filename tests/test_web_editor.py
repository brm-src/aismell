"""Browser regressions. Uses the installed Playwright, no npm build required.

Run: python -m pytest tests/test_web_editor.py -q
The first boot downloads Pyodide; analysis itself must not send text out.
"""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

import pytest

playwright = pytest.importorskip("playwright.sync_api")


@pytest.fixture(scope="module")
def page():
    docs = Path(__file__).resolve().parents[1] / "docs"
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(SimpleHTTPRequestHandler, directory=str(docs)))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox"])
        tab = browser.new_page(locale="es-CL", viewport={"width": 1280, "height": 900})
        tab.goto(f"http://127.0.0.1:{server.server_port}")
        tab.wait_for_function("analyzeFn !== null", timeout=120000)
        yield tab
        browser.close()
    server.shutdown()
    server.server_close()
    thread.join()


def test_editorial_verdict_uses_the_engine_score_not_an_authorship_guess(page):
    result = page.evaluate("""() => {
        const report = {score: 0.17, sentences: 8, hits: [], structural: [], notes: []};
        const verdict = computeVerdict(report);
        return {score: verdict.heur, html: renderVerdict(report)};
    }""")
    assert result["score"] == 0.17
    assert "seguridad del detector" not in result["html"]
    assert "autoría" in result["html"]


def test_many_segments_fit_in_results_on_desktop_and_mobile(page):
    for width in (1280, 390, 320):
        page.set_viewport_size({"width": width, "height": 900})
        dimensions = page.evaluate("""() => {
            const segments = Array.from({length: 284}, (_, i) => ({
                index: i + 1, start_sentence: i + 1, end_sentence: i + 1,
                findings: i < 87 ? 1 : 0, score: 0.2, label: 'bajo', text: 'Texto.'
            }));
            document.getElementById('findings').innerHTML = `<section class="result-details">${renderSegments({segments})}</section>`;
            document.getElementById('resultPanel').hidden = false;
            document.querySelector('.segments-more').open = true;
            const strip = document.querySelector('.heat-strip');
            const panel = document.querySelector('.segments-more');
            return {count: strip.children.length, cards: panel.querySelectorAll('.segment-card').length,
                    summary: panel.querySelector('summary').innerText, strip: strip.getBoundingClientRect().width,
                    scroll: strip.scrollWidth, panel: panel.getBoundingClientRect().width,
                    document: document.documentElement.scrollWidth};
        }""")
        assert dimensions['count'] == 284
        assert dimensions['cards'] == 87
        assert '87 de 284 con hallazgos' in dimensions['summary']
        assert dimensions['scroll'] <= dimensions['strip'] + 1, dimensions
        assert dimensions['strip'] <= dimensions['panel'], dimensions
        assert dimensions['document'] <= width, dimensions
    page.set_viewport_size({"width": 1280, "height": 900})


def test_external_services_are_opt_in_and_rewrite_needs_a_separate_action(page):
    assert page.locator('#biblioSel').count() == 1
    assert not page.locator('#biblioSel').is_checked()
    assert not page.locator('#semanticSel').is_checked()
    assert not page.locator('#stripRewrite').is_checked()
    requests = []
    page.on('request', lambda r: requests.append(r.url))
    page.locator('#input').fill('Es importante destacar el resultado. DOI: 10.1000/private-test')
    page.locator('#analyzeBtn').click()
    page.wait_for_function("!document.getElementById('analyzeBtn').disabled")
    assert not any('crossref.org' in url or 'huggingface.co' in url or 'strip-marks' in url for url in requests)
    page.locator('#stripBtn').click()
    assert page.locator('#stripPanel').is_visible()
    assert not any('strip-marks' in url for url in requests)


def test_escaping_covers_attribute_quotes(page):
    assert page.evaluate('escapeHtml(\'" onfocus="alert(1)\')') == '&quot; onfocus=&quot;alert(1)'


def test_findings_locate_the_exact_unicode_span_and_edits_invalidate_results(page):
    text = 'Texto anterior.\n😀 Cabe destacar que llegó el informe. Hay datos para revisarlo.'
    page.locator('#input').fill(text)
    page.locator('#analyzeBtn').click()
    page.wait_for_function("!document.getElementById('analyzeBtn').disabled")
    link = page.locator('[data-source-line="2"]').first
    assert link.count() == 1
    link.click()
    selected = page.evaluate("input.value.slice(input.selectionStart, input.selectionEnd)")
    assert selected.lower() == 'cabe destacar'
    assert page.locator('.match').first.inner_text().lower() == 'cabe destacar'
    page.locator('#input').fill('Ahora el texto cambió.')
    assert page.locator('#resultPanel').is_hidden()


def test_keyboard_shortcut_does_not_start_a_second_run(page):
    page.locator('#input').fill('Cabe destacar que falta revisar los resultados.')
    count = page.evaluate("""async () => {
        const original = analyzeFn;
        let calls = 0;
        analyzeFn = (...args) => { calls++; return original(...args); };
        try {
            const first = analyze();
            const second = analyze();
            await Promise.all([first, second]);
            return calls;
        } finally { analyzeFn = original; }
    }""")
    assert count == 1


def test_long_analysis_keeps_scanner_and_event_loop_responsive(page):
    page.set_viewport_size({"width": 390, "height": 844})
    result = page.evaluate("""async () => {
        input.value = ('Cabe destacar que este informe presenta datos importantes. ' +
            'El equipo revisó los resultados antes de continuar.\\n').repeat(300);
        let ticks = 0, visible = false;
        const timer = setInterval(() => {
            ticks++;
            const scan = document.getElementById('scanning');
            const rect = scan.getBoundingClientRect();
            visible ||= !scan.hidden && rect.top < innerHeight && rect.bottom > 0;
        }, 50);
        await analyze();
        clearInterval(timer);
        return {ticks, visible, rendered: !document.getElementById('resultPanel').hidden};
    }""")
    page.set_viewport_size({"width": 1280, "height": 900})
    assert result['visible'] and result['ticks'] >= 3 and result['rendered'], result


def test_bibliography_never_calls_failed_checks_verified(page):
    result = page.evaluate("""() => {
        const ref = {raw: 'Reference', title: 'Reference', line: 1};
        return buildBiblioReportHtml([{ref, res: {status: 'error'}}], I18N.es);
    }""")
    assert 'todas las citas verificadas' not in result
    assert 'incompleta' in result.lower()
    assert not page.evaluate("titleSimilar('Art', 'Artificial intelligence')")
    assert page.evaluate("titleSimilar('Educación y participación ciudadana', 'Educacion y participacion ciudadana')")


def test_bibliography_does_not_render_unsafe_links(page):
    html = page.evaluate("""() => renderBiblioRow(
        {title: 'A title', raw: 'A title', kind: 'citation'},
        {status: 'exists', url: 'javascript:alert(1)'}
    )""")
    assert 'javascript:' not in html


def test_native_dialog_traps_and_restores_focus(page):
    page.locator('#aboutBtn').click()
    assert page.evaluate("document.querySelector('#aboutModal').matches(':modal')")
    page.keyboard.press('Escape')
    assert page.locator('#aboutModal').is_hidden()
    assert page.locator('#aboutBtn').evaluate('(el) => el === document.activeElement')


def test_unicode_cleanup_is_local_and_preserves_original(page):
    original = 'Hola\u200b mundo 👩\u200d💻'
    page.locator('#input').fill(original)
    page.locator('#stripRewrite').uncheck()
    page.locator('#stripBtn').click()
    requests = []
    page.on('request', lambda request: requests.append(request.url))
    page.locator('#stripRunBtn').click()
    page.wait_for_selector('#stripOutput')
    assert page.locator('#stripOutput').input_value() == 'Hola mundo 👩\u200d💻'
    assert page.locator('#input').input_value() == original
    assert not any('strip-marks' in url for url in requests)


def test_optional_semantics_cannot_change_the_index_or_override_strict(page):
    result = page.evaluate("""async () => {
        const original = runSemanticAnalysis;
        runSemanticAnalysis = async () => ({findings: [{kind: 'semantic-cohesion-high', severity: 1, message: 'Similarity', suggestion: 'Compare'}]});
        const report = {score: 0.17, notes: [], structural: [], lang: 'es'};
        const progress = {advance() {}, setModelProgress() {}};
        els.semanticSel.checked = true;
        els.strictSel.checked = true;
        try { await addSemanticNotes(report, 'Synthetic text', progress); return report; }
        finally { runSemanticAnalysis = original; els.semanticSel.checked = false; els.strictSel.checked = false; }
    }""")
    assert result['score'] == 0.17
    assert result['structural'] == []
    assert result['semantic'] == []


def test_paste_and_import_use_the_same_report_and_docx_download_is_valid(page, tmp_path):
    from _docx_builder import build_docx
    import zipfile
    text = 'Cabe destacar que los datos llegaron. El equipo revisó el informe.'
    page.locator('#input').fill(text)
    page.locator('#analyzeBtn').click()
    page.wait_for_function("!document.getElementById('analyzeBtn').disabled")
    expected = page.evaluate('({score: lastReport.score, hits: lastReport.hits.map(h => h.id)})')
    source = tmp_path / 'sample.md'
    source.write_text(text)
    page.locator('#fileInput').set_input_files(str(source))
    page.wait_for_function("!document.getElementById('analyzeBtn').disabled")
    assert page.evaluate('({score: lastReport.score, hits: lastReport.hits.map(h => h.id)})') == expected
    document = build_docx(tmp_path / 'sample.docx', [text])
    page.locator('#fileInput').set_input_files(str(document))
    page.wait_for_selector('#docxDownloadBtn')
    page.wait_for_function("!document.getElementById('analyzeBtn').disabled")
    assert page.evaluate('({score: lastReport.score, hits: lastReport.hits.map(h => h.id)})') == expected
    with page.expect_download() as download:
        page.locator('#docxDownloadBtn').click()
    output = tmp_path / 'commented.docx'
    download.value.save_as(output)
    with zipfile.ZipFile(output) as archive:
        assert 'word/comments.xml' in archive.namelist()
        assert 'destacar' in archive.read('word/comments.xml').decode()


def test_bibliography_can_be_cancelled_without_late_results(page):
    pending = []
    page.route('https://api.crossref.org/**', lambda route: pending.append(route))
    page.locator('#input').fill('Cabe destacar el resultado. DOI: 10.1234/cancellation-test')
    page.locator('.review-options').evaluate('(el) => el.open = true')
    page.locator('#biblioSel').check()
    page.locator('#analyzeBtn').click()
    page.wait_for_selector('#cancelBiblioBtn')
    page.locator('#cancelBiblioBtn').click()
    page.wait_for_function("!document.getElementById('analyzeBtn').disabled")
    assert page.locator('#biblioPanel').count() == 0
    assert page.locator('#resultPanel').is_visible()
    for route in pending:
        route.abort()
    page.unroute('https://api.crossref.org/**')
    page.locator('#biblioSel').uncheck()


def test_doi_lookup_reads_the_public_record_instead_of_a_shadowed_url(page):
    page.route('https://api.crossref.org/works/**', lambda route: route.fulfill(
        json={'status': 'ok', 'message': {'title': ['Public test record'], 'URL': 'https://doi.org/10.1234/public-fixture'}}
    ))
    result = page.evaluate("verifyDoiJs('10.1234/public-fixture')")
    page.unroute('https://api.crossref.org/works/**')
    assert result['status'] == 'exists'
    assert result['detail'] == 'Public test record'
