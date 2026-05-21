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
        help="file to analyze (defaults to stdin, or opens a file picker if available)",
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
        "--out",
        metavar="PATH",
        help="write a marked-up copy to PATH. Format auto-detected from extension: .docx, .pdf, or .md/.txt for a plain text annotated copy. Implies --docx-out / --pdf-out behavior.",
    )
    parser.add_argument(
        "--docx-out",
        metavar="PATH",
        help="(legacy) same as --out for .docx files",
    )
    parser.add_argument(
        "--no-picker",
        action="store_true",
        help="disable the GUI file picker fallback when run with no arguments",
    )
    parser.add_argument(
        "--biblio",
        action="store_true",
        help="extract bibliographic references (DOIs, arXiv ids, citations) and verify them online (CrossRef + arXiv). Network required.",
    )
    args = parser.parse_args(argv)

    # If no path given and stdin is a TTY, try the file picker.
    if not args.path and sys.stdin.isatty() and not args.no_picker:
        from .picker import pick_file
        picked = pick_file()
        if picked is not None:
            args.path = str(picked)
            # When picked, default the output next to the source.
            if not args.out and not args.docx_out:
                src = Path(args.path)
                ext = src.suffix.lower()
                if ext in (".docx", ".pdf"):
                    args.out = str(src.with_name(src.stem + "-aismell" + src.suffix))

    out_path = args.out or args.docx_out
    if out_path:
        ext = Path(out_path).suffix.lower()
        in_ext = Path(args.path).suffix.lower() if args.path else ""
        if not args.path:
            print("aismell: --out requires an input file path", file=sys.stderr)
            return 2
        if ext == ".docx" or in_ext == ".docx":
            from .docx import annotate_docx
            try:
                result = annotate_docx(
                    in_path=Path(args.path),
                    out_path=Path(out_path),
                    lang=None if args.lang == "auto" else args.lang,
                    strict=args.strict,
                )
            except (FileNotFoundError, ValueError) as exc:
                print(f"aismell: {exc}", file=sys.stderr)
                return 2
        elif ext == ".pdf" or in_ext == ".pdf":
            from .pdf import annotate_pdf
            try:
                result = annotate_pdf(
                    in_path=Path(args.path),
                    out_path=Path(out_path),
                    lang=None if args.lang == "auto" else args.lang,
                    strict=args.strict,
                )
            except RuntimeError as exc:
                print(f"aismell: {exc}", file=sys.stderr)
                return 2
            except (FileNotFoundError, ValueError) as exc:
                print(f"aismell: {exc}", file=sys.stderr)
                return 2
        else:
            print(
                f"aismell: --out only supports .docx and .pdf right now (got '{ext}' / '{in_ext}')",
                file=sys.stderr,
            )
            return 2
        pct = int(result.score * 100)
        msg = (
            f"{result.output_path}  •  {result.sentences} sentences  •  "
            f"smell: {pct}% ({result.severity_label})  •  "
            f"{result.findings} marks"
        )
        # Print to BOTH stderr (for piping) and stdout (so GUI launches see it).
        print(msg)
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

    if args.biblio:
        from .biblio import find_references, verify_all
        refs = find_references(text)
        if refs:
            print(f"\n--- bibliografía ({len(refs)} referencias) ---")
            print("verificando online (CrossRef/arXiv)...\n")
            results = verify_all(refs)
            for vr in results:
                r = vr.reference
                icon = {
                    "exists": "✓",
                    "not_found": "✗",
                    "error": "?",
                    "unverifiable": "·",
                }.get(vr.status, "·")
                ident = r.identifier or (r.title[:60] if r.title else r.raw[:60])
                print(f"  {icon} [{r.kind}] L{r.line}  {ident}")
                if vr.detail:
                    print(f"      {vr.detail[:100]}")
            fakes = sum(1 for vr in results if vr.status == "not_found")
            if fakes:
                print(f"\n⚠  {fakes}/{len(refs)} referencias no se encontraron — posible IA inventando")
        else:
            print("\nbibliografía: no se detectaron referencias parseables")

    # exit code: 0 clean, 1 findings (useful for CI / pre-commit)
    return 1 if report.total_findings else 0


if __name__ == "__main__":
    sys.exit(main())
