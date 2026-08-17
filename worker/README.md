# aismell rewrite worker

Public endpoints used by the `aismell quick clean` and `ai bibliography check` Omarchy plugins.

- `GET /health` — service/version probe.
- `POST /rewrite` — accepts `{ "text": "...", "mode": "clean" | "improve" }` up to 3,000 characters and returns `{ "text": "...", "changes": ["..."] }`.
- `POST /bibliography` — accepts a bibliography up to 12,000 characters, indexes its fields, queries Crossref and OpenAlex for up to 12 entries, and returns structural checks, catalog matches, duplicate identifiers, consistency warnings, and aismell signals from the first 3,000 characters.

For entries with a DOI, the Worker performs an exact DOI lookup. For entries without a DOI, it queries both catalogs with title + author + year and ranks returned records using normalized title overlap, author overlap, and year agreement. A low score is `not-found`; the service never upgrades a weak result to a match.

`clean` is conservative. `improve` makes a more visible humanizing edit while preserving facts, names, dates, URLs, citations, quotations, code, lists, language, and register.

The Worker uses Cloudflare Workers AI with `@cf/meta/llama-4-scout-17b-16e-instruct`. The application has no persistent storage and replies with `Cache-Control: no-store`, `X-Content-Type-Options: nosniff`, and `Referrer-Policy: no-referrer`; the text is nevertheless sent to Cloudflare for inference. The model instruction requires preservation of facts, names, dates, URLs, citations, quotations, code, lists, language, and register.

The current Workers AI free allocation is 10,000 Neurons/day. This model is not one of Cloudflare's models that requires Workers Paid billing. If that free allocation is exhausted, the endpoint returns `503` instead of silently falling back or charging another provider.

## Checks

```bash
node --test worker/test/rewrite.test.js
node --check worker/src/index.js
```

## Deploy

```bash
set -a && source ~/.config/wrangler/.env && set +a
npx wrangler deploy -c worker/wrangler.toml
```
