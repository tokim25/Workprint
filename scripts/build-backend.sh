#!/usr/bin/env bash
# Builds the standalone Python backend binary electron-builder bundles as
# an extraResource. Requires Python 3.10+ (pyproject.toml's declared
# minimum) with PyInstaller available; this is a build-time dependency
# only -- the whole point of this binary is that end users need no
# Python installed at all to run the packaged app.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${WORKPRINT_BUILD_PYTHON:-python3}"

if ! "$PYTHON_BIN" -c "import PyInstaller" >/dev/null 2>&1; then
  echo "PyInstaller is not available for $PYTHON_BIN." >&2
  echo "Install it in a Python 3.10+ environment first, e.g.:" >&2
  echo "  python3.12 -m venv .build-venv && source .build-venv/bin/activate" >&2
  echo "  pip install -e . && pip install pyinstaller" >&2
  echo "Then re-run this script with that environment active, or set" >&2
  echo "WORKPRINT_BUILD_PYTHON to that environment's python executable." >&2
  exit 1
fi

rm -rf dist-backend build-backend
"$PYTHON_BIN" -m PyInstaller \
  --onefile \
  --name workprint-backend \
  --distpath dist-backend \
  --workpath build-backend \
  --specpath build-backend \
  src/workprint/bundled_cli.py

echo "Built dist-backend/workprint-backend"
