#!/usr/bin/env bash
# Fetch the published Velbus module protocol and extract the PDFs to text.
#
# 1. shallow-clones (or refreshes) https://github.com/velbus/moduleprotocol
# 2. ensures pypdf is available in the venv
# 3. extracts every protocol PDF to plain text under <workdir>/text/
#
# Output layout:
#   $WORKDIR/README.md         - the module ID -> name table (ground truth)
#   $WORKDIR/*.pdf             - the protocol manuals
#   $WORKDIR/text/<stem>.txt   - extracted text, one file per PDF
set -euo pipefail

REPO_URL="https://github.com/velbus/moduleprotocol.git"
WORKDIR="${1:-/tmp/velbus_proto}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Python interpreter — NOT hardcoded. Resolution order:
#   1. $VELBUS_VENV/bin/python   (venv root, matches the retest skill)
#   2. $VELBUS_PY                (explicit interpreter path)
#   3. $VIRTUAL_ENV/bin/python   (a venv already activated in the shell)
#   4. python3 on PATH           (last resort; may lack pip permissions)
if [ -n "${VELBUS_VENV:-}" ]; then
    PY="$VELBUS_VENV/bin/python"
elif [ -n "${VELBUS_PY:-}" ]; then
    PY="$VELBUS_PY"
elif [ -n "${VIRTUAL_ENV:-}" ]; then
    PY="$VIRTUAL_ENV/bin/python"
else
    PY="$(command -v python3)"
fi

if [ ! -x "$PY" ]; then
    PY="$(command -v python3)"
fi
echo "Using python: $PY"

if [ -d "$WORKDIR/.git" ]; then
    echo "Refreshing existing clone in $WORKDIR"
    git -C "$WORKDIR" fetch --depth 1 origin 2>&1 | tail -2
    git -C "$WORKDIR" reset --hard origin/HEAD 2>&1 | tail -1
else
    echo "Cloning $REPO_URL into $WORKDIR"
    rm -rf "$WORKDIR"
    git clone --depth 1 "$REPO_URL" "$WORKDIR" 2>&1 | tail -2
fi

if ! "$PY" -c "import pypdf" 2>/dev/null; then
    echo "Installing pypdf into the venv..."
    "$PY" -m pip install --quiet pypdf
fi

echo "Extracting PDFs..."
"$PY" "$SCRIPT_DIR/extract_pdf.py" --all "$WORKDIR" "$WORKDIR/text"

echo "Done. Protocol ready in $WORKDIR"
