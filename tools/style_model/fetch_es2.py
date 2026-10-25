"""More human Spanish genres (pre-2022): stories, news, academic abstracts."""
import json, random, time, urllib.request
random.seed(5)


def rows(ds, cfg, split, off, n=100):
    for _ in range(4):
        try:
            u = f"https://datasets-server.huggingface.co/rows?dataset={ds}&config={cfg}&split={split}&offset={off}&length={n}"
            return [x["row"] for x in json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "x"}), timeout=60))["rows"]]
        except Exception:
            time.sleep(3)
    return []


out = []
def take(ds, cfg, split, total, want, fn, src):
    got = 0
    offs = range(0, max(total - 100, 1), 100)
    for off in random.sample(offs, min(60, len(offs))):
        for r in rows(ds, cfg, split, off):
            t = fn(r)
            if t and 120 <= len(t.split()):
                out.append({"text": t, "src": src}); got += 1
        print(src, got, flush=True)
        if got >= want:
            return


def cuento(r):
    try:
        y = int(str(r.get("years") or "0")[:4])
    except ValueError:
        y = 0
    return r["content"] if 0 < y < 2020 or not r.get("years") else None


take("Fernandoefg/cuentos_es", "default", "train", 6000, 220, cuento, "cuentos")
take("mariagrandury/fake_news_corpus_spanish", "default", "test", 570, 150, lambda r: r["TEXT"], "news-fn")
take("mteb/spanish_news", "default", "train", 3000, 150, lambda r: r["text"], "news-mteb")
take("eduagarcia/scielo_abstracts", "default", "train", 50000, 200,
     lambda r: r["abstract_es"] if r.get("abstract_es") and int(r.get("pub_year") or 2030) < 2022 else None, "scielo-es")
json.dump(out, open("data/human_es2.json", "w"), ensure_ascii=False)
print("saved", len(out))
