# aismell rewrite worker

Public endpoint used by the `aismell quick clean` Omarchy plugin.

- `GET /health` — service/version probe.
- `POST /rewrite` — accepts `{ "text": "..." }` up to 3,000 characters and returns `{ "text": "...", "changes": ["..."] }`.

The Worker uses Cloudflare Workers AI with `@cf/meta/llama-4-scout-17b-16e-instruct`. The application has no persistent storage and replies with `Cache-Control: no-store`; the text is nevertheless sent to Cloudflare for inference. The model instruction requires preservation of facts, names, dates, URLs, citations, quotations, code, lists, language, and register.

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
