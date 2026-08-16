import json

from workers import Response, WorkerEntrypoint

from analyzer import analyze_for_rewrite


def response(payload, status=200):
    return Response(
        json.dumps(payload, ensure_ascii=False),
        status=status,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "Cache-Control": "no-store",
        },
    )


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        url = request.url
        if request.method == "OPTIONS":
            return Response(None, status=204, headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type",
            })
        if url.endswith("/health") and request.method == "GET":
            return response({"ok": True, "engine": "aismell-core"})
        if not url.endswith("/analyze") or request.method != "POST":
            return response({"error": "not-found"}, 404)
        try:
            body = await request.json()
            raw_text = body.get("text") if isinstance(body, dict) else ""
            text = raw_text if isinstance(raw_text, str) else ""
            return response(analyze_for_rewrite(text))
        except ValueError as error:
            return response({"error": str(error)}, 400)
        except Exception as error:
            print(f"aismell analyzer failed: {type(error).__name__}: {error}")
            return response({"error": "analyze-unavailable"}, 503)
