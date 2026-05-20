"""aismell CLI."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .core import analyze
from .render import render


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="aismell",
        description="Sniff AI-smell in your text. ES/EN.",
    )
    parser.add_argument(
        "path",
        nargs="?",
        help="file to analyze (defaults to stdin)",
    )
    parser.add_argument(
        "--lang",
        choices=["es", "en", "auto"],
        default="auto",
        help="language (default: auto-detect)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="show only high-confidence findings (severity ≥ 2)",
    )
    parser.add_argument(
        "--score-only",
        action="store_true",
        help="print only the smell score (0-100)",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="disable ANSI colors",
    )
    parser.add_argument(
        "--docx-out",
        metavar="PATH",
        help="instead of printing, read input as .docx and write a marked-up copy with yellow highlights + review comments to PATH",
    )
    args = parser.parse_args(argv)

    if args.docx_out:
        # Bypass stdin/text path; the input must be a real .docx file.
        if not args.path:
            print("aismell: --docx-out requires an input .docx path", file=sys.stderr)
            return 2
        from .docx import annotate_docx

        try:
            result = annotate_docx(
                in_path=Path(args.path),
                out_path=Path(args.docx_out),
                lang=None if args.lang == "auto" else args.lang,
                strict=args.strict,
            )
        except FileNotFoundError as exc:
            print(f"aismell: {exc}", file=sys.stderr)
            return 2
        except ValueError as exc:
            print(f"aismell: {exc}", file=sys.stderr)
            return 2
        pct = int(result.score * 100)
        print(
            f"{result.output_path}  •  {result.sentences} sentences  •  "
            f"smell: {pct}% ({result.severity_label})  •  "
            f"{result.findings} comments added",
            file=sys.stderr,
        )
        return 1 if result.findings else 0

    if args.no_color:
        # rebind module flag
        from . import render as r
        r._USE_COLOR = False

    if args.path:
        try:
            text = Path(args.path).read_text(encoding="utf-8")
        except FileNotFoundError:
            print(f"aismell: not found: {args.path}", file=sys.stderr)
            return 2
        path_label = args.path
    else:
        if sys.stdin.isatty():
            print("aismell: pipe text in or pass a file. -h for help.", file=sys.stderr)
            return 2
        text = sys.stdin.read()
        path_label = "<stdin>"

    if not text.strip():
        print("aismell: empty input", file=sys.stderr)
        return 2

    lang = None if args.lang == "auto" else args.lang
    report, lang_used = analyze(text, lang=lang, strict=args.strict)

    if args.score_only:
        print(int(report.score * 100))
        return 0

    print(render(path_label, report, lang_used), end="")

    # exit code: 0 clean, 1 findings (useful for CI / pre-commit)
    return 1 if report.total_findings else 0


if __name__ == "__main__":
    sys.exit(main())
