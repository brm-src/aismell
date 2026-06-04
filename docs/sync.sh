#!/usr/bin/env bash
# Sync the core.py and patterns/ from the package into docs/ so the
# Pyodide build can fetch them with relative paths. Run before committing
# changes to either the package or the web app.
set -euo pipefail
cd "$(dirname "$0")"
cp ../aismell/core.py core.py
cp ../aismell/docx.py docx.py
cp ../aismell/biblio.py biblio.py
mkdir -p patterns
cp ../aismell/patterns/*.yaml patterns/
echo "synced docs/core.py, docs/docx.py, docs/biblio.py and docs/patterns/ from aismell/"
