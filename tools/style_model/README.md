# Style model (trained combiner)

`aismell/core.py` embeds a per-language logistic model between the
`BEGIN/END STYLE MODEL` markers. It reads the explainable features in
`report.features` (rule dimensions + length-normalized stylometry) and returns
the index, the kind of text (story, academic, informative, personal/opinion)
and the share of human reference texts of that kind that reach the index.

Rebuild (data is not committed; scripts fetch it):

1. `fetch_raid.py` (RAID, MIT), `fetch_human.py` (mC4 2019-20, HVSIA),
   `fetch_es2.py` (Spanish stories, news, SciELO), `gen.py` (fresh AI text via
   free models only), plus human/AI files referenced in `featurize.py`.
2. `python featurize.py` → `data/features.jsonl`
3. `python train.py 0.1 --write` (numpy + scikit-learn) prints grouped
   cross-validation (unseen generators) and writes the model into core.py.

Evaluation holds out whole AI generators; human texts are split within source.
Paragraph layout, capitalization slips and spacing typos are excluded as
features: they depend on how text was pasted or scraped, not on authorship.
