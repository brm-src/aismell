"""Train per-language logistic combiners with grouped cross-validation.
uv run --with numpy --with scikit-learn python train.py  -> metrics + model.json"""
import json, sys
from collections import defaultdict
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold

rows = [json.loads(l) for l in open("data/features.jsonl")]
C = float(sys.argv[1]) if len(sys.argv) > 1 else 0.3


def tpr_at(y, p, fpr):
    thr = np.quantile(p[y == 0], 1 - fpr)
    return float((p[y == 1] > thr).mean()), float(thr)


model = {}
for lang in ("es", "en"):
    R = [r for r in rows if r["lang"] == lang]
    keys = sorted(R[0]["f"])
    X = np.array([[r["f"].get(k, 0.0) for k in keys] for r in R])
    y = np.array([r["label"] for r in R])
    # AI: hold out whole generators. Human: split within each source (deployment
    # sees the same genres), so the score answers "does it catch an unseen model?".
    g = np.array([r["group"] if r["label"] else f'{r["group"]}#{i % 8}' for i, r in enumerate(R)])
    src_g = np.array([r["group"] for r in R])
    rule = X[:, keys.index("rule_combined")]
    mu, sd = X.mean(0), X.std(0)
    sd[sd < 1e-6] = 1.0  # constant feature (e.g. contractions in Spanish): neutral, never a division by zero
    Z = (X - mu) / sd
    oof = np.zeros(len(y))
    # Leave whole generators / human sources out: scores on unseen sources only.
    for tr, te in GroupKFold(n_splits=min(8, len(set(g)))).split(Z, y, g):
        m = LogisticRegression(C=C, class_weight="balanced", max_iter=4000).fit(Z[tr], y[tr])
        oof[te] = m.predict_proba(Z[te])[:, 1]
    oof_src = np.zeros(len(y))
    for tr, te in GroupKFold(n_splits=min(8, len(set(src_g)))).split(Z, y, src_g):
        m = LogisticRegression(C=C, class_weight="balanced", max_iter=4000).fit(Z[tr], y[tr])
        oof_src[te] = m.predict_proba(Z[te])[:, 1]
    print(f"\n== {lang}: n={len(y)} ai={y.sum()} human={(y == 0).sum()} groups={len(set(g))}")
    for name, p in (("rules only", rule), ("combiner", oof), ("comb-srcout", oof_src)):
        t1, _ = tpr_at(y, p, 0.01); t5, _ = tpr_at(y, p, 0.05)
        print(f"  {name:11s} AUC {roc_auc_score(y, p):.3f}  TPR@1%FPR {t1:.2f}  TPR@5%FPR {t5:.2f}")
    per = defaultdict(list)
    for gi, yi, pi, ri in zip(src_g, y, oof, rule):
        per[gi].append((yi, pi, ri))
    for gi, v in sorted(per.items()):
        print(f"    {gi:28s} n={len(v):4d} label={v[0][0]} combiner_mean={np.mean([x[1] for x in v]):.2f} rules_mean={np.mean([x[2] for x in v]):.2f}")
    m = LogisticRegression(C=C, class_weight="balanced", max_iter=4000).fit(Z, y)
    coef = m.coef_[0]
    order = np.argsort(-np.abs(coef))[:15]
    print("  top weights:", ", ".join(f"{keys[i]}={coef[i]:+.2f}" for i in order))
    # Thresholds from out-of-fold human scores: what a human text rarely exceeds.
    hum = np.sort(oof[y == 0])
    # Context: which kind of text is this? Trained on every text with a known
    # genre; the human reference for the index is then the same genre.
    gen_lbl = np.array([r.get("genre") or "" for r in R])
    known = gen_lbl != ""
    gm_oof = np.empty(len(y), dtype=object)
    for tr, te in GroupKFold(n_splits=8).split(Z[known], gen_lbl[known], g[known]):
        gm = LogisticRegression(C=0.3, max_iter=4000).fit(Z[known][tr], gen_lbl[known][tr])
        gm_oof[np.where(known)[0][te]] = gm.predict(Z[known][te])
    acc = float((gm_oof[known] == gen_lbl[known]).mean())
    print(f"  genre accuracy (unseen sources) {acc:.2f}")
    gm = LogisticRegression(C=0.3, max_iter=4000).fit(Z[known], gen_lbl[known])
    by_genre = {}
    for gname in gm.classes_:
        hg = np.sort(oof[(y == 0) & (gen_lbl == gname)])
        ag = oof[(y == 1) & (gen_lbl == gname)]
        if len(hg) >= 60:
            by_genre[gname] = [[round(float(np.quantile(hg, q)), 4), round(q, 3)] for q in np.linspace(0, 1, 41)]
            t1 = np.quantile(hg, 0.95)
            print(f"    {gname:9s} humans={len(hg):4d} ai={len(ag):4d} ai_above_95pct_humans={(ag > t1).mean():.2f}")
    model[lang] = {
        "genre": {"classes": gm.classes_.tolist(), "coef": gm.coef_.round(5).tolist(), "intercept": gm.intercept_.round(5).tolist()},
        "human_cdf_by_genre": by_genre,
        "keys": keys, "mean": mu.round(6).tolist(), "scale": sd.round(6).tolist(),
        "coef": coef.round(5).tolist(), "intercept": round(float(m.intercept_[0]), 5),
        "human_cdf": [[round(float(np.quantile(hum, q)), 4), round(q, 3)] for q in np.linspace(0, 1, 41)],
        "ai_recall_at": {str(q): round(float((oof[y == 1] > np.quantile(hum, q)).mean()), 3) for q in (0.9, 0.95, 0.99)},
        "n": {"human": int((y == 0).sum()), "ai": int(y.sum())},
    }
json.dump(model, open("model.json", "w"))
if "--write" in sys.argv:
    import re
    core = "/home/brm/Developer/aismell/aismell/core.py"
    src = open(core).read()
    body = "_STYLE_MODEL: dict = {\n" + "".join(f'    "{k}": {json.dumps(v)},\n' for k, v in model.items()) + "}\n"
    src = re.sub(r"(# BEGIN STYLE MODEL[^\n]*\n).*?(# END STYLE MODEL)", lambda m: m.group(1) + body + m.group(2), src, flags=re.S)
    open(core, "w").write(src)
    print("wrote model into core.py")
