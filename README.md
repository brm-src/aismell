# aismell

<p align="center">
  <a href="https://www.ko-fi.com/brmcl"><img src="https://ko-fi.com/img/githubbutton_sm.svg" alt="Support me on Ko-fi" /></a>
</p>

> Sniff AI-smell in your text. Bilingual ES/EN. CLI. Offline. Opinionated.

🇪🇸 [Léeme en español](README.es.md) · 🌐 [Try it in your browser](https://brm-src.github.io/aismell/)

![demo](demo.gif)

```
text.md  •  47 sentences  •  smell: 31% (moderate)

Line-by-line findings
  🔴 L4   It's not just about productivity—it's about transformation.
        AI's signature negative parallelism [en.not_just]
        → state the positive idea directly

  🔴 L12  ...let's delve into the complexities of...
        the most flagged AI word of 2024 [en.delve]
        → use "explore", "look at", or just dig in
```

## What it actually does

`aismell` reads your text and points out lines that smell like a language model wrote them. No false promise of "fooling GPTZero." Your blog post, email, PR description, or essay either sounds like *you* or sounds like an LLM — this tool just helps you spot which.

It runs offline, uses regex + heuristics (no API calls by default), and works on Spanish and English text.

## Why another one of these

Most "AI text humanizers" are scams. They reshuffle synonyms or insert typos to bypass detectors. That game is dishonest and useless.

`aismell` is the opposite:
- **Analysis does not rewrite for you.** It tells you what reads like AI, line by line. (The web has a separate "strip marks" action that can rewrite if you explicitly use it; the CLI doesn't.)
- **It is auditable.** Every pattern lives in a YAML file you can read and contribute to.
- **It is local by default.** Editorial analysis and Unicode cleanup run in your browser without sending your text. Bibliography lookup is opt-in and sends only parsed references to public catalogues. Only an explicitly enabled rewrite sends the full text to aismell on Cloudflare Workers AI. The application adds no persistent text storage; that is not a guarantee about third-party infrastructure.
- **It does not promise to fool detectors.** It promises to make your text feel less like autopilot.

The honest framing is editorial, not adversarial. Use it before publishing.

## Web: strip marks

[aismell.me](https://aismell.me) has a **"strip marks"** action next to the normal analysis:

- **Cleans Unicode locally**, using the same implementation as the service. Preserves meaningful emoji joiners and script characters by default.
- **Rewrites only after consent**: open the panel, enable rewrite, then select “Send and rewrite”. The limit is 3,000 characters. The original is never replaced automatically.
- A rewrite uses Cloudflare Workers AI and can alter facts, names or citations despite its instructions. Compare both versions before using it.
- Bibliography and experimental paragraph-similarity review are off by default. Similarity downloads a large local model; it does not modify the editorial index.
- Findings link to the exact source span for editing; editing invalidates the old report. Word uploads retain commented downloads.

## Install

**pipx (recommended, any OS):**
```bash
pipx install aismell
pipx inject aismell pymupdf       # optional: enable PDF annotation
```

**Arch (AUR):**
```bash
yay -S aismell                    # once published
# or from this repo:
git clone https://github.com/brm-src/aismell.git
cd aismell/packaging && makepkg -si
```

**From source, no install:**
```bash
git clone https://github.com/brm-src/aismell.git
cd aismell
./bin/aismell --help
# requires: PyYAML (pacman -S python-yaml, apt install python3-yaml, etc.)
```

Requires Python 3.9+. PyMuPDF is optional, only for `.pdf` annotation.

## Use

```bash
# analyze a file (auto-detects language)
aismell post.md

# pipe stdin
cat draft.txt | aismell

# annotate a Word .docx — yellow highlights + sidebar comments
aismell mi-tesis.docx --out mi-tesis-marcado.docx

# annotate a PDF — yellow highlights + sticky-note comments
aismell paper.pdf --out paper-marcado.pdf

# no arguments? opens a native file picker (if you have a desktop)
aismell

# only show high-confidence findings
aismell --strict post.md

# get a single number 0-100 (great for CI / pre-commit)
aismell --score-only post.md

# force language
aismell --lang es post.md

# disable color
aismell --no-color post.md
```

## Conservative Python helper

The package also exposes a small offline helper for high-confidence cleanup. It does not call an LLM or send text anywhere:

```python
from aismell.quickclean import clean

result = clean("It is important to note that the report is ready.")
print(result.text)
print(result.changes)
```

Use this helper when privacy matters more than a broad rewrite. The Omarchy plugin's `clean` and `improve` actions are separate online flows documented in [ai quick clean](https://github.com/brm-src/ai-quick-clean).

## What it catches

Three layers of detection.

**1. Phrase patterns.** Things AI writes when it coasts: `vale la pena destacar`, `delve into`, `stands as a testament`, `hope this helps`. The rules now cover 130+ English patterns and 180+ Spanish patterns, including formal connectors and bloated abstract nouns.

**2. Structure patterns.** Tells beyond word choice: split binary reframes, false agency, evasive passive voice, negative listing, copula avoidance, generic conclusions, sycophantic openers.

**3. Rhythm, shape, and discourse.** Sentence-length variance, em-dash density, list ratio, rule-of-three frequency, **paragraph-length symmetry** (LLMs produce paragraphs of suspiciously similar length), **opening-connector density** (Pangram research shows multiple paragraphs starting with explicit connectors is the single strongest AI tell), and StoryScope-inspired cues such as over-explained themes and too-neat narrative closure.

Scores are a heuristic editorial index from 0 to 100, not a percentage of generated text or a probability of authorship. Higher values prioritize review; the web uses the same index as the CLI without a second classifier or invented confidence. Mentioned dates do not establish document provenance. No independent accuracy benchmark is claimed.

## What it does *not* do

- Does not call an LLM (a future `--rewrite` flag may do so, opt-in). The web's "strip marks" action does use a model when you enable rewrite.
- Does not rewrite your text for you in the CLI. The web's "strip marks" action can rewrite, only when you explicitly use it.
- Does not claim to be a forensic AI detector. False positives are fine — humans use these phrases too. The point is making them visible so you can decide.

## Patterns are data

Every detection rule lives in `patterns/es.yaml` or `patterns/en.yaml`. Format:

```yaml
- id: en.delve
  kind: phrase            # phrase | regex
  severity: 3             # editorial priority: 1 (low) | 2 (medium) | 3 (high)
  pattern: delve into
  message: the most flagged AI word of 2024
  suggestion: use "explore", "look at", or just dig in
```

Add a pattern, open a PR. No code changes needed for new rules. Run `bash docs/sync.sh` to update every web/Worker copy. Rules are cached per process; restart after editing them, or call `load_patterns.cache_clear()` in a long-lived Python embedding.

## Roadmap

- [ ] More patterns (always)
- [ ] `--rewrite` flag with optional LLM backend (offline by default stays default)
- [ ] Plain-text output mode for `grep`-style piping
- [ ] Pre-commit hook config
- [ ] `--diff` mode that shows before/after suggestions

## Related

This project is built on top of the patterns documented in [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing), [blader/humanizer](https://github.com/blader/humanizer), and [hardikpandya/stop-slop](https://github.com/hardikpandya/stop-slop). The bloat lexicon and structural checks are informed by [Pangram Labs research](https://arxiv.org/abs/2402.14873) (2024-2025), the [DAMAGE paper on AI humanizers](https://arxiv.org/html/2501.03437v1), and [EditLens](https://arxiv.org/abs/2510.03154). See [docs/research.md](docs/research.md) for the full breakdown.

All sources MIT-compatible, and so is this.

## License

MIT. See [LICENSE](LICENSE).
