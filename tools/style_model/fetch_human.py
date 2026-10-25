"""Human pre-LLM web text: mC4 (2019-2020 Common Crawl) es/en validation rows, plus HVSIA."""
import json, random, re, time, urllib.request
random.seed(3)

def get(u):
    for _ in range(4):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "x"}), timeout=60))
        except Exception as e:
            err = e; time.sleep(3)
    print("fail", u[-60:], err); return {}

def prose(t):
    lines = [l for l in t.split("\n") if l.strip()]
    w = len(t.split())
    if not 150 <= w <= 1500 or len(lines) < 2:
        return False
    # skip menus/catalogs: most lines should be sentences
    sent_like = sum(1 for l in lines if len(l.split()) >= 8 and re.search(r"[.!?»\"]$", l.strip()))
    return sent_like / len(lines) >= 0.6

out = []
for lang, want in (("es", 450), ("en", 250)):
    got = 0
    for off in random.sample(range(0, 150000, 100), 400):
        r = get(f"https://datasets-server.huggingface.co/rows?dataset=allenai/c4&config={lang}&split=validation&offset={off}&length=100")
        for x in r.get("rows", []):
            row = x["row"]
            if prose(row["text"]):
                out.append({"text": row["text"], "lang": lang, "src": "mc4", "url": row.get("url", "")}); got += 1
        print(lang, off, got, flush=True)
        if got >= want:
            break
for off in (0, 100):
    r = get(f"https://datasets-server.huggingface.co/rows?dataset=CarmenCL/HVSIA_AI_detection_spanish&config=default&split=train&offset={off}&length=100")
    for x in r.get("rows", []):
        row = x["row"]
        out.append({"text": row["text"], "lang": "es", "src": "hvsia-" + row["source"], "label": int(row["label"])})
json.dump(out, open("data/human_web.json", "w"), ensure_ascii=False)
print("saved", len(out))
