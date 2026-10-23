#!/usr/bin/env bash
# Canonical Python/pattern source: aismell/. Consumers: Pyodide and Worker.
# Run from any cwd before shipping either consumer. Bash + coreutils only.
set -euo pipefail
cd "$(dirname "$0")"
for target in . ../worker/analyzer/src/aismell; do
    mkdir -p "$target/patterns"
    cp ../aismell/core.py "$target/core.py"
    cp ../aismell/patterns/*.yaml "$target/patterns/"
done
cp ../aismell/docx.py docx.py
cp ../aismell/biblio.py biblio.py
# Keep the legacy public YAML URLs in sync too.
cp ../aismell/patterns/*.yaml .
cp ../worker/src/unicode_strip.js unicode_strip.js
echo "synced docs/ and worker/analyzer core/patterns; docs Unicode cleaner"
