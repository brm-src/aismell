# aismell

> Sniff AI-smell in your text. Bilingual ES/EN. CLI. Offline. Opinionated.

🇪🇸 [Léeme en español](README.es.md)

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
- **It does not rewrite for you.** It tells you what reads like AI, line by line.
- **It is auditable.** Every pattern lives in a YAML file you can read and contribute to.
- **It is offline by default.** Your text never leaves your machine.
- **It does not promise to fool detectors.** It promises to make your text feel less like autopilot.

The honest framing is editorial, not adversarial. Use it before publishing.

## Install

```bash
git clone https://github.com/brm-src/aismell.git
cd aismell
pip install -e .
```

Or run without installing:
```bash
git clone https://github.com/brm-src/aismell.git
~/aismell/bin/aismell --help
```

Requires Python 3.9+ and PyYAML.

## Use

```bash
# analyze a file (auto-detects language)
aismell post.md

# pipe stdin
cat draft.txt | aismell

# only show high-confidence findings
aismell --strict post.md

# get a single number 0-100 (great for CI / pre-commit)
aismell --score-only post.md

# force language
aismell --lang es post.md

# disable color
aismell --no-color post.md
```

Exit code is `0` when clean, `1` when findings are present. Useful for git hooks.

## What it catches

Three layers of detection.

**1. Phrase patterns.** Things AI writes that humans rarely do: *"vale la pena destacar"*, *"delve into"*, *"stands as a testament"*, *"hope this helps"*. ~50 patterns shipped per language.

**2. Structure patterns.** Tells beyond word choice: negative parallelisms (*"it's not just X, it's Y"*), copula avoidance (*"serves as"* instead of *"is"*), generic conclusions (*"the future looks bright"*), sycophantic openers.

**3. Rhythm and density.** Sentence-length variance, em-dash density, list ratio, rule-of-three frequency. Calculated globally, not per-line.

Scores are normalized to a 0–100 smell percentage. Above 60 is loud AI, 30–60 is mixed, below 30 is mostly clean.

## What it does *not* do

- Does not call an LLM (a future `--rewrite` flag may do so, opt-in).
- Does not rewrite your text for you.
- Does not claim to be a forensic AI detector. False positives are fine — humans use these phrases too. The point is making them visible so you can decide.

## Patterns are data

Every detection rule lives in `patterns/es.yaml` or `patterns/en.yaml`. Format:

```yaml
- id: en.delve
  kind: phrase            # phrase | regex
  severity: 3             # 1 (suspect) | 2 (probable) | 3 (almost certain)
  pattern: delve into
  message: the most flagged AI word of 2024
  suggestion: use "explore", "look at", or just dig in
```

Add a pattern, open a PR. No code changes needed for new rules.

## Roadmap

- [ ] More patterns (always)
- [ ] `--rewrite` flag with optional LLM backend (offline by default stays default)
- [ ] Plain-text output mode for `grep`-style piping
- [ ] Pre-commit hook config
- [ ] `--diff` mode that shows before/after suggestions

## Related

This project is built on top of the patterns documented in [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) and [blader/humanizer](https://github.com/blader/humanizer). Both are MIT, and so is this.

## License

MIT. See [LICENSE](LICENSE).
