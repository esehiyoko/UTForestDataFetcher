#!/bin/sh
# Build a local JupyterLite site with the examples and this package's wheel, and serve it.
#
#   examples/jupyterlite/build.sh          # build into examples/jupyterlite/_output and serve on :8000
#   examples/jupyterlite/build.sh --no-serve
#
# The notebook runs in the browser (Pyodide), so the API must allow this page's origin
# (http://localhost:8000 and http://127.0.0.1:8000) with CORS. The development Rails of
# fgdc_publish_platform allows them (FGDC_API_CORS_ORIGINS in compose.development.yaml).
set -eu
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
root=$(CDPATH= cd -- "$here/../.." && pwd)
venv=$here/.venv
[ -x "$venv/bin/jupyter" ] || { python3 -m venv "$venv"; "$venv/bin/pip" install -q -r "$here/requirements.txt"; }
rm -rf "$here/wheels" "$here/_output" "$here/.jupyterlite.doit.db"
"$venv/bin/python" -m build --wheel --outdir "$here/wheels" "$root" >/dev/null
cd "$here"
"$venv/bin/jupyter" lite build --contents "$root/examples/weather_quickstart.ipynb" \
  --piplite-wheels "$here"/wheels/*.whl --output-dir "$here/_output"
[ "${1:-}" = "--no-serve" ] || "$venv/bin/jupyter" lite serve --output-dir "$here/_output" --port 8000
