#!/bin/bash
# One-click viewer: double-click in Finder.
# By default it opens the built dashboard and the report PDF;
# type r and press Return within 5 seconds to rebuild the dashboard from the frozen results first.
# From a terminal you can also run: ./open_dashboard.command --rebuild

cd "$(dirname "$0")" || exit 1
DASH="dashboard/index.html"
REPORT="report/report_draft_v1.pdf"

find_python() {
  for py in "$HOME/anaconda3/bin/python3" "$HOME/opt/anaconda3/bin/python3" "$HOME/miniconda3/bin/python3" "$(command -v python3)"; do
    if [ -x "$py" ] && "$py" -c "import pandas, pyarrow" >/dev/null 2>&1; then
      echo "$py"
      return 0
    fi
  done
  return 1
}

rebuild() {
  PY="$(find_python)" || {
    echo "No Python with pandas and pyarrow found, so the dashboard cannot be rebuilt."
    echo "Install them first: conda install pandas pyarrow (or pip install pandas pyarrow)"
    return 1
  }
  echo "Rebuilding the dashboard with $PY ..."
  "$PY" src/dashboard/build.py || { echo "Rebuild failed; see the error above."; return 1; }
}

MODE="$1"
if [ -z "$MODE" ]; then
  echo "Perception Gap Monitor"
  echo "Press Return or wait 5 seconds to open; type r and press Return to rebuild first"
  read -r -t 5 ANS
  [ "$ANS" = "r" ] && MODE="--rebuild"
fi

if [ "$MODE" = "--rebuild" ]; then
  rebuild || { read -r -p "Press Return to close this window" _; exit 1; }
fi

if [ ! -f "$DASH" ]; then
  echo "$DASH not found; type r to rebuild it first."
  read -r -p "Press Return to close this window" _
  exit 1
fi

[ -f "$REPORT" ] && open "$REPORT"
open "$DASH"
echo "Opened the dashboard and the report. You can close this window."
