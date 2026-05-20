# Research notes — what aismell is built on

aismell does not aim to fool AI detectors, and does not claim to. This document explains the academic and empirical research that shaped its detection strategy, and the deliberate ethical line the project draws.

## The detection arms race in 2025-2026

Two pieces of research changed the landscape:

**Pangram Labs (2024-2025).** First-generation detectors (DetectGPT, GPTZero v1, Turnitin v1) relied on **perplexity** (token predictability) and **burstiness** (sentence-length variance). Both are correlational, both are brittle, and both produce systematic false positives against ESL writers and neurodivergent students. Pangram replaced them with a transformer-based classifier trained via **synthetic mirror prompting**: for every human document, an LLM is asked to reverse-engineer the prompt that *would have* produced it, and then generate a synthetic twin. The classifier learns to distinguish the original from its mirror, which forces it to find the latent geometry of AI cognition rather than surface patterns. Reported FPR: 0.00% on ELLIPSE (ESL students), 0.09% on ICNALE (Asian university students), >90% accuracy against commercial humanizers.

**DAMAGE study (Pangram, 2025).** Audited 19 commercial AI humanizers (Undetectable AI, Phrasly, StealthWriter, GPTInf, etc.). Categorized them in three tiers — L1 preserves fluency, L2 hurts it, L3 produces word-salad. Pangram's classifier remains >90% accurate against L1 humanizers. Conclusion: post-processing AI text with another AI to "humanize" it just adds another detectable layer.

**EditLens (2025).** A regression head trained to estimate *how much* of a document was AI-edited, not just whether. F1 of 0.947 on binary classification, 0.904 on ternary (human / AI / hybrid). On the BEEMO corpus (AI text intensively edited by humans), 88.9% of documents showed a detection score that *correlated with the amount of human intervention*, proving that algorithmic editing leaves a measurable statistical residue. On ArgRewrite V.2 (human edited by humans), the score was 0.012 — i.e., the model does not confuse human editing with AI editing.

## Why this matters for `aismell`

The PDF that seeded this project framed all of the above as a *humanization arms race*: how to write prompts that evade Pangram. We deliberately chose the opposite framing.

We use the same research, but in reverse:

| What the research shows           | What `aismell` does with it                                      |
| --------------------------------- | ---------------------------------------------------------------- |
| LLMs overuse a specific lexicon   | Patterns flag those words so you remove them                     |
| LLMs produce symmetric paragraphs | Structural check warns about paragraph-length symmetry           |
| LLMs use formal connectors        | Structural check warns when 2+ paragraphs open with a connector  |
| Burstiness is too low in AI       | Sentence-length CV is reported, not artificially raised          |
| RLHF causes "semantic bloat"      | The bloat list is encoded as patterns the user can read & remove |

We do not ship a `--humanize` mode and we will not. The honest framing is editorial: make the user see what reads as AI so they can decide whether it sounds like them.

## What the research warns against

Three things `aismell` deliberately does NOT do:

1. **No automated rewrite.** EditLens shows that LLM rewriting leaves a residue. If we rewrite for you with another model, we ship the same residue you started with. The user must rewrite manually, in their voice.
2. **No detector-evasion claims.** Pangram explicitly trained against humanizers. Promising "evasion" is dishonest. We promise *legibility*: your text will read less like autopilot.
3. **No false-positive panic.** AI detectors *systematically* misclassify ESL writers, neurodivergent writers, and rigid technical genres (legal, medical). The same lexical and structural patterns we flag are sometimes legitimate. `aismell` flags, never fails. The user decides.

## The Pangram lexicon

The PDF documents a "semantic bloat" taxonomy that recurs across LLMs trained with RLHF. Selected entries (with our pattern IDs):

**Verbs:** delve (`en.delve`), embark (`en.embark`), navigate (`en.navigate`), augment (`en.augment`), facilitate (`en.facilitate`), underscore (`en.underscores`), utilize (`en.utilize`), optimize (`en.optimize`), glean (`en.glean`).

**Abstract nouns:** tapestry (`en.tapestry`), testament (`en.testament`), landscape (`en.evolving_landscape`), realm (`en.realm`), nuance (`en.nuance`), synergy (`en.synergy`), paradigm (`en.paradigm`), framework + modifier (`en.framework_robust`).

**Modifiers:** vibrant (`en.vibrant`), bustling (`en.bustling`), multifaceted (`en.multifaceted`), meticulous (`en.meticulous`), pivotal (`en.pivotal`), robust (`en.robust`), seamless (`en.seamless`), transformative (`en.transformative`), paramount (`en.paramount`).

**Connectors:** Furthermore, Moreover, Additionally, Consequently, Hence, Nonetheless, Subsequently, Firstly. Each of these has both a paragraph-start regex (severity 2) and contributes to the structural `paragraph-connectors` check (severity 3).

The Spanish set mirrors the same taxonomy: profundizar, embarcarse, navegar las complejidades, paradigma, reino, sinergia, vibrante, multifacético, meticuloso, robusto, sin fisuras, transformador, además, adicionalmente, en consecuencia, en primer lugar.

## What the research suggests we add next

In rough priority order:

- [ ] **Knowledge-cutoff disclaimers in ES** — phrases like *"según la información disponible"*, *"hasta donde alcanza mi conocimiento"*. Already partially covered.
- [ ] **Negative parallelism in long form** — the *"It's not just X, it's Y"* construction generalizes to *"More than X, this is about Y"* and longer variants we don't catch yet.
- [ ] **List-of-three with internal parallelism** — already a structural check, but the heuristic is shallow.
- [ ] **Em-dash + clause structure** — current check counts em-dashes; doesn't yet check whether they bracket parallel clauses (a stronger AI tell than density alone).
- [ ] **Topic openings** — flag introductions that begin by stating what the document will do (*"This essay will explore…"*) instead of doing it.

## Sources

The detection-side research:

- Pangram Labs (2024). *Technical Report on the Pangram AI-Generated Text Classifier.* arXiv:2402.14873. https://arxiv.org/abs/2402.14873
- Pangram Labs (2025). *DAMAGE: Detecting Adversarially Modified AI Generated Text.* arXiv:2501.03437. https://arxiv.org/html/2501.03437v1
- Krishna et al. (2025). *EditLens: Quantifying the Extent of AI Editing in Text.* arXiv:2510.03154. https://arxiv.org/abs/2510.03154

The lexical taxonomy:

- Wikipedia: WikiProject AI Cleanup. *Signs of AI writing.* https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing
- Siqi Chen / @blader. *humanizer.* https://github.com/blader/humanizer
- Margaret Efron. *Words and phrases that make it obvious you used ChatGPT.* https://medium.com/learning-data/words-and-phrases-that-make-it-obvious-you-used-chatgpt-2ba374033ac6
- Walter Writes AI. *Most common ChatGPT words to avoid in 2026.* https://walterwrites.ai/most-common-chatgpt-words-to-avoid/

The sociotechnical critique (read these before trusting any AI detector for academic discipline):

- *AI Writing Detection in Higher Education: Population-Differentiated False Positives, Statistical Convergence, and the Sociology of Algorithmic Classification.* https://www.researchgate.net/publication/404271810
- *Students are deliberately writing worse to avoid AI detection flags.* r/Professors discussion, 2025.
