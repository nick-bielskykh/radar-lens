#!/usr/bin/env bash
# Збір новин і білд сайту. Редакторську роботу (відсів, українські тексти, оцінки)
# робить агент за EDITOR.md між кроками fetch і assemble.
#
#   ./run.sh fetch      — тільки збір у data/raw.json + data/img/
#   ./run.sh build      — assemble.py + build.py (після того, як агент заповнив data/enriched/)
#   ./run.sh enrich      — опційно: збагачення через Claude API (потрібен ANTHROPIC_API_KEY)
#   ./run.sh todo       — список id, для яких ще нема data/enriched/<id>.json
#
# Змінні: DAYS (за скільки днів збирати, 3), MODEL/EFFORT (тільки для кроку enrich).
set -euo pipefail
cd "$(dirname "$0")"

PY=python3
if [ -x .venv/bin/python ]; then PY=.venv/bin/python; else
  $PY -m venv .venv && .venv/bin/pip -q install -r requirements.txt && PY=.venv/bin/python
fi

case "${1:-fetch}" in
  fetch)  DAYS="${DAYS:-3}" $PY fetch.py ;;
  build)  $PY assemble.py && $PY build.py ;;
  enrich) EFFORT="${EFFORT:-low}" MODEL="${MODEL:-claude-opus-5}" $PY enrich.py ;;
  todo)   $PY - <<'PYEOF'
import json, os
raw = json.load(open("data/raw.json"))
todo = [r["id"] for r in raw if not os.path.exists(f"data/enriched/{r['id']}.json")]
print("\n".join(todo))
print(f"# {len(todo)} з {len(raw)} без enriched", file=__import__("sys").stderr)
PYEOF
  ;;
  *) echo "usage: ./run.sh [fetch|build|enrich|todo]" >&2; exit 2 ;;
esac
