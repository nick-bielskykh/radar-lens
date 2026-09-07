#!/usr/bin/env bash
# Повний цикл оновлення стрічки: збір -> збагачення (Claude) -> складання -> білд.
# Змінні: DAYS (за скільки днів збирати, 3), EFFORT (глибина міркувань моделі, low),
# MODEL (claude-opus-5), ANTHROPIC_API_KEY (обовʼязковий для кроку збагачення).
set -euo pipefail
cd "$(dirname "$0")"

PY=python3
if [ -x .venv/bin/python ]; then PY=.venv/bin/python; else
  $PY -m venv .venv && .venv/bin/pip -q install -r requirements.txt && PY=.venv/bin/python
fi

DAYS="${DAYS:-3}" $PY fetch.py

if [ -n "${ANTHROPIC_API_KEY:-}" ]; then
  EFFORT="${EFFORT:-low}" MODEL="${MODEL:-claude-opus-5}" $PY enrich.py
else
  echo "ANTHROPIC_API_KEY не заданий — крок збагачення пропущено (зробіть його агентом за EDITOR.md)" >&2
fi

$PY assemble.py
$PY build.py
