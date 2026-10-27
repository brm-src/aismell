// Local Python runs off the UI thread; drafts never leave the browser.
importScripts("https://cdn.jsdelivr.net/pyodide/v0.27.2/full/pyodide.js");
let pyodide;

async function boot() {
  pyodide = await loadPyodide({ indexURL: "https://cdn.jsdelivr.net/pyodide/v0.27.2/full/" });
  await pyodide.loadPackage("pyyaml");
  const sources = await loadSources();
    pyodide.FS.mkdir("/aismell");
    pyodide.FS.mkdir("/aismell/patterns");
    pyodide.FS.writeFile("/aismell/__init__.py", "");
    pyodide.FS.writeFile("/aismell/core.py", sources.core);
    pyodide.FS.writeFile("/aismell/docx.py", sources.docx);
    pyodide.FS.writeFile("/aismell/biblio.py", sources.biblio);
    pyodide.FS.writeFile("/aismell/patterns/es.yaml", sources.es);
    pyodide.FS.writeFile("/aismell/patterns/en.yaml", sources.en);

    pyodide.runPython(`
import sys
sys.path.insert(0, "/")
from aismell.core import analyze
from aismell.docx import annotate_docx
from aismell.biblio import find_references, score_apa_reference
from pathlib import Path

def run(text, lang_code, strict, era_code):
    lang = None if lang_code == "auto" else lang_code
    era = "auto" if era_code in ("auto", "") else era_code
    report, used = analyze(text, lang=lang, strict=strict, era=era)
    out = {
        "score": report.score,
        "label": report.severity_label,
        "sentences": report.sentences,
        "lang": used,
        "era": report.era,
        "era_max_year": report.era_max_year,
        "notes": report.notes,
        "stats": report.stats,
        "score_components": report.score_components,
        "rates": report.rates,
        "human_exceed": report.human_exceed,
        "context": report.context,
        "style_reasons": report.style_reasons,
        "hits": [],
        "structural": [],
        "sections": [],
        "segments": [],
    }
    for h in report.hits:
        out["hits"].append({
            "line": h.line,
            "col": h.col,
            "end": h.end,
            "text": h.text,
            "matched": h.matched,
            "id": h.pattern.id,
            "severity": h.pattern.severity,
            "message": h.pattern.message,
            "suggestion": h.pattern.suggestion,
        })
    for s in report.structural:
        out["structural"].append({
            "line": s.line,
            "kind": s.kind,
            "severity": s.severity,
            "message": s.message,
            "suggestion": s.suggestion,
            "count": s.count,
        })
    for sec in report.sections:
        out["sections"].append({
            "name": sec.name,
            "score": sec.score,
            "sentences": sec.sentences,
            "reasons": sec.reasons,
        })
    for segment in report.segments:
        out["segments"].append({
            "index": segment.index,
            "start_sentence": segment.start_sentence,
            "end_sentence": segment.end_sentence,
            "sentences": segment.sentences,
            "score": segment.score,
            "label": segment.label,
            "confidence": segment.confidence,
            "findings": segment.findings,
            "text": segment.text,
        })
    return out

def annotate_docx_bytes(input_bytes, lang_code, strict):
    src = Path("/tmp/in.docx")
    dst = Path("/tmp/out.docx")
    src.write_bytes(bytes(input_bytes))
    lang = None if lang_code == "auto" else lang_code
    result = annotate_docx(src, dst, lang=lang, strict=strict)
    data = dst.read_bytes()
    return {
        "bytes": data,
        "findings": result.findings,
        "sentences": result.sentences,
        "score": result.score,
        "label": result.severity_label,
    }

def extract_refs(text):
    refs = find_references(text)
    out = []
    for r in refs:
        apa = score_apa_reference(r) if r.kind == "citation" else None
        out.append({
            "kind": r.kind,
            "raw": r.raw,
            "line": r.line,
            "identifier": r.identifier,
            "title": r.title,
            "year": r.year,
            "author": r.author,
            "verifiable": r.verifiable,
            "apa_score": apa.score if apa else None,
            "apa_status": apa.status if apa else "",
            "apa_issues": apa.issues if apa else [],
        })
    return out

def extract_docx_text(input_bytes):
    import io, zipfile
    from xml.etree import ElementTree as ET
    W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    with zipfile.ZipFile(io.BytesIO(bytes(input_bytes))) as z:
        xml = z.read("word/document.xml")
    root = ET.fromstring(xml)
    paras = []
    for p in root.iter(W + "p"):
        paras.append("".join(t.text or "" for t in p.iter(W + "t")))
    return "\\n".join(paras)
`);
  postMessage({ type: "ready" });
}

async function loadSources() {
  // Try local relative paths first.
  const local = {
    core: "core.py",
    docx: "docx.py",
    biblio: "biblio.py",
    es: "patterns/es.yaml",
    en: "patterns/en.yaml",
  };
  const remote = {
    core: "https://raw.githubusercontent.com/brm-src/aismell/main/aismell/core.py",
    docx: "https://raw.githubusercontent.com/brm-src/aismell/main/aismell/docx.py",
    biblio: "https://raw.githubusercontent.com/brm-src/aismell/main/aismell/biblio.py",
    es:   "https://raw.githubusercontent.com/brm-src/aismell/main/aismell/patterns/es.yaml",
    en:   "https://raw.githubusercontent.com/brm-src/aismell/main/aismell/patterns/en.yaml",
  };
  const out = {};
  const keys = Object.keys(local);
  await Promise.all(keys.map(async (k) => {
    let body = null;
    try {
      const r = await fetch(local[k]);
      if (r.ok) body = await r.text();
    } catch (_) { /* try remote */ }
    if (!body) {
      const r = await fetch(remote[k]);
      if (!r.ok) throw new Error(`could not fetch ${k}`);
      body = await r.text();
    }
    out[k] = body;
  }));
  return out;
}

onmessage = async ({ data }) => {
  try {
    const fn = pyodide.globals.get(data.method);
    try {
      const value = fn(...data.args);
      if (value && typeof value.toJs === "function") {
        try { postMessage({ id: data.id, value: value.toJs({ dict_converter: Object.fromEntries }) }); }
        finally { value.destroy(); }
      } else postMessage({ id: data.id, value });
    } finally { fn.destroy(); }
  } catch (error) { postMessage({ id: data.id, error: error.message }); }
};
boot().catch(error => postMessage({ type: "error", error: error.message }));
