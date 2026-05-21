#!/usr/bin/env bash
# Sync the core.py and patterns/ from the package into docs/ so the
# Pyodide build can fetch them with relative paths. Run before committing
# changes to either the package or the web app.
set -euo pipefail
cd "$(dirname "$0")"
cp ../aismell/core.py core.py
mkdir -p patterns
cp ../aismell/patterns/*.yaml patterns/
echo "synced docs/core.py and docs/patterns/ from aismell/"
