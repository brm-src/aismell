"""Build labelled samples and features. Run: /usr/bin/python featurize.py  -> data/features.jsonl"""
import glob, json, re, sys
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, "/home/brm/Developer/aismell")
sys.path.insert(0, "/home/brm/.hermes/cache/scratch/aismell")
S = Path("/home/brm/.hermes/cache/scratch/aismell")
D = S / "ml" / "data"

PREAMBLE = re.compile(r"^\s*(claro|por supuesto|aquí tienes|aqui tienes|a continuación|sure|certainly|here is|here's|of course|absolutely)\b[^\n]*\n+(?:\s*[-*_]{3,}\s*\n+)?", re.I)
TRAILER = re.compile(r"\n+\s*(?:[-*_]{3,}\s*\n+)?(?:¿te gustaría|¿quieres que|espero que (?:te|esta)|would you like|let me know if|i hope this|feel free to)[^\n]*\s*$", re.I)


def body(t):
    t = PREAMBLE.sub("", t.strip())
    return TRAILER.sub("", t).strip()


def demark(t):
    t = re.sub(r"\*\*|__", "", t)
    t = re.sub(r"(?m)^#{1,6}\s*", "", t)
    return re.sub(r"(?m)^\s*[-*•]\s+", "", t)


def chunks(t, size=500):
    paras, out, cur = [p for p in re.split(r"\n\s*\n", t) if p.strip()], [], []
    for p in paras:
        cur.append(p)
        if sum(len(x.split()) for x in cur) >= size:
            out.append("\n\n".join(cur)); cur = []
    if cur and sum(len(x.split()) for x in cur) >= 150:
        out.append("\n\n".join(cur))
    return out


def lang_of(name):
    return "es" if re.search(r"(^|/)(es_|q_)", name) else "en"


samples = []  # dict(text, lang, label, group, src)


def add(text, lang, label, group, src):
    if 120 <= len(text.split()) <= 2500:
        samples.append({"text": text, "lang": lang, "label": label, "group": group, "src": src})


# ---- AI ----
for d in ("blind", "heldout", "final", "final2", "ml/data/claude_es", "ml/data/claude_en"):
    for f in sorted(glob.glob(str(S / d / "*.txt"))):
        lang = "es" if "claude_es" in d else "en" if "claude_en" in d else lang_of(Path(f).name)
        add(body(Path(f).read_text()), lang, 1, "claude", d + "/" + Path(f).name)
add((S / "luna.txt").read_text(), "es", 1, "claude", "luna")
add((S / "ai_en_lighthouse.txt").read_text(), "en", 1, "claude", "lighthouse")
for line in open(D / "gen.jsonl"):
    r = json.loads(line)
    add(body(r["text"]), r["lang"], 1, r["model"].split("/")[-1].replace("gem:", ""), "gen-" + r["genre"])
if (D / "raid.json").exists():
    for r in json.load(open(D / "raid.json")):
        add(r["text"], "en", 0 if r["model"] == "human" else 1, "raid-" + r["model"] if r["model"] != "human" else "raid-human-" + r["domain"], "raid-" + r["domain"])
for r in json.load(open(D / "human_web.json")):
    if r["src"] == "mc4":
        add(r["text"], r["lang"], 0, "mc4-" + r["lang"], "mc4")
    else:
        add(r["text"], "es", r.get("label", 0), "hvsia-ai" if r.get("label") else "hvsia-wiki", r["src"])

for r in json.load(open(D / "human_es2.json")):
    for c in (chunks(r["text"]) if len(r["text"].split()) > 900 else [r["text"]])[:2]:
        add(c, "es", 0, r["src"], r["src"])

for r in json.load(open(D / "human_en2.json")):
    add(r["text"], "en", 0, r["src"], r["src"])

# ---- human literature / web ----
def clean_wiki(p):
    t = p.read_text(encoding="utf-8")
    t = re.sub(r"\{\{[^}]*\}\}", "", t, flags=re.S)
    t = re.sub(r"<[^>]+>", "", t)
    t = re.sub(r"'{2,}", "", t)
    t = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", t)
    return "\n".join(l for l in t.splitlines() if not l.startswith("Categoría:")).strip()


def gut(p, start, words=3000):
    t = p.read_text(encoding="utf-8", errors="ignore").replace("\r", "")
    out, n = [], 0
    for para in t[t.find(start):].split("\n\n"):
        out.append(para); n += len(para.split())
        if n > words:
            break
    return "\n\n".join(out)


for f in sorted(glob.glob(str(S / "human/es_*.wiki"))):
    for c in chunks(clean_wiki(Path(f))):
        add(c, "es", 0, "wikisource-es", Path(f).name)
for f in sorted(glob.glob(str(S / "q_*.txt"))):
    for c in chunks(Path(f).read_text()):
        add(c, "es", 0, "wikisource-es", Path(f).name)
for name, start in [("strachey.txt", "CHAPTER I. ANTECEDENTS"), ("ohenry.txt", "THE GIFT OF THE MAGI"), ("holmes.txt", "To Sherlock Holmes she is always")]:
    for c in chunks(gut(S / "human" / name, start, 9000)):
        add(c, "en", 0, "gutenberg-en", name)
for f in ("en_telltale.txt", "en_blackcat.txt"):
    for c in chunks((S / f).read_text()):
        add(c, "en", 0, "gutenberg-en", f)
for f in sorted(glob.glob(str(S / "human/wiki_*.txt"))):
    for c in chunks(Path(f).read_text()):
        add(c, "es" if "_es_" in f else "en", 0, "wayback-wiki", Path(f).name)
for f in sorted(glob.glob(str(S / "human/nosleep_*.txt"))):
    for c in chunks(Path(f).read_text()):
        add(c, "en", 0, "nosleep", Path(f).name)
for f in glob.glob("/home/brm/Developer/aismell/tests/samples/es_human_*.txt"):
    add(Path(f).read_text(), "es", 0, "wikisource-es", Path(f).name)


FICTION = ("cuento", "story", "horror", "terror", "scifi", "fantasy", "luna", "lighthouse", "relato")
CLAUDE_NUM = {"claude_es": {"06": "fiction", "16": "fiction", "09": "academic", "01": "info", "07": "info"},
              "claude_en": {"06": "fiction", "09": "academic", "01": "info", "07": "info"}}


def genre(s):
    g, src = s["group"], s["src"].replace("+plain", "")
    if g in ("cuentos", "wikisource-es", "gutenberg-en", "nosleep"):
        return "fiction"
    if g in ("scielo-es", "raid-human-abstracts"):
        return "academic"
    if g in ("news-fn", "news-mteb", "raid-human-news", "raid-human-books", "hvsia-wiki", "wayback-wiki", "hvsia-ai"):
        return "info"
    if g in ("reddit-tldr", "yelp", "mc4-es", "mc4-en"):
        return "web"
    if src.startswith("raid-"):
        return {"raid-abstracts": "academic", "raid-books": "info", "raid-news": "info"}.get(src)
    if src.startswith("gen-"):
        k = src[4:]
        return ("fiction" if k in ("cuento", "story") else "academic" if k in ("ensayo", "essay")
                else "info" if k in ("noticia", "news", "wiki") else "web")
    for d, m in CLAUDE_NUM.items():
        if d in src:
            return m.get(Path(src).stem, "web")
    name = src.lower()
    if any(k in name for k in FICTION):
        return "fiction"
    if "ensayo" in name or "essay" in name:
        return "academic"
    if any(k in name for k in ("noticia", "press", "articulo", "article")):
        return "info"
    return "web"


def feat(s):
    from aismell.core import analyze
    return {**s, "genre": genre(s), "f": analyze(s["text"], s["lang"], include_segments=False)[0].features}


if __name__ == "__main__":
    # Markdown-free copies of AI text: users often paste without formatting.
    extra = [dict(s, text=demark(s["text"]), src=s["src"] + "+plain") for s in samples
             if s["label"] == 1 and demark(s["text"]) != s["text"]]
    allx = samples + extra
    with Pool(12) as p:
        rows = p.map(feat, allx, chunksize=8)
    with open(D / "features.jsonl", "w") as out:
        for r in rows:
            out.write(json.dumps(r, ensure_ascii=False) + "\n")
    from collections import Counter
    print(len(rows), Counter((r["lang"], r["label"]) for r in rows))
    print(Counter(r["group"] for r in rows).most_common())
