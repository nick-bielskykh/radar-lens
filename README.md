# Lens Radar

Внутрішній портал новин фоторедагування для команди Luminar (Neo та Mobile).

- `sources.py` — джерела (RSS, YouTube, Reddit, Google News) та ключові слова.
- `fetch.py` — збір новин за `DAYS` днів: текст, картинки, відео, пари before/after. Пише `data/raw.json`, `data/img/`.
- `enrich.py` — обробка через Claude API (потрібен `ANTHROPIC_API_KEY`): відсів, українські тексти, оцінка, медіа. Пише `data/enriched/<id>.json`.
  Модель і глибина міркувань — змінні `MODEL` (типово `claude-opus-5`) та `EFFORT` (типово `low`).
  Ту саму роботу може робити агент за інструкцією `EDITOR.md` без ключа.
- `assemble.py` — збирає `data/items.json` з `data/enriched/` та `data/raw.json`.
- `build.py` — генерує `site/index.html` (картинки вбудовані) та `site/hosted/` (для Vercel).
- `luminar_context.md` — контекст про продукти для промптів. Редагуйте, щоб покращити коментарі «Що це означає для Luminar».
- `run.sh` — весь конвеєр одним прогоном (fetch → enrich → assemble → build).
- `ROUTINE.md` — промпт щоденної cloud routine.

Локальний запуск:

```bash
ANTHROPIC_API_KEY=... DAYS=3 ./run.sh
```

Покроково:

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
DAYS=3 .venv/bin/python fetch.py
ANTHROPIC_API_KEY=... EFFORT=low .venv/bin/python enrich.py
.venv/bin/python assemble.py && .venv/bin/python build.py
```
