# Lens Radar

Внутрішній портал новин фоторедагування для команди Luminar (Neo та Mobile).

- `sources.py` — джерела (RSS, YouTube, Reddit, Google News) та ключові слова.
- `fetch.py` — збір новин за `DAYS` днів: текст, картинки, відео. Пише `data/raw.json`, `data/img/`.
- `enrich.py` — обробка через Claude API (потрібен `ANTHROPIC_API_KEY`): відсів, українські тексти, оцінка, медіа. Пише `data/enriched/<id>.json`.
  Модель і глибина міркувань — змінні `MODEL` (типово `claude-opus-5`) та `EFFORT` (типово `low`).
  Ту саму роботу може робити агент за інструкцією `EDITOR.md` без ключа.
- `assemble.py` — збирає `data/items.json` з `data/enriched/` та `data/raw.json`.
- `build.py` — генерує `site/index.html` (картинки вбудовані) та `site/hosted/` (для Vercel).
- `luminar_context.md` — контекст про продукти для промптів. Редагуйте, щоб покращити коментарі «Що це означає для Luminar».
- `tweet.py` — додає твіти як кандидатів (`./run.sh tweet <url>`), дані з api.fxtwitter.com, без ключів.
- `run.sh` — обгортка над кроками: `fetch` (збір), `todo` (що ще не оброблено), `build` (assemble + build), `tweet <url>` (додати твіт), `enrich` (опційно, через API).
- `ROUTINE.md` — промпт щоденної cloud routine.

Локальний запуск:

Основний режим — редагує агент (ключ не потрібен):

```bash
./run.sh fetch     # збір новин
./run.sh todo      # id без data/enriched/<id>.json — їх обробляє агент за EDITOR.md
./run.sh build     # data/items.json + site/hosted/
```

Опційно, через API:

```bash
ANTHROPIC_API_KEY=... ./run.sh enrich
```

## Деплой

Хостинг: https://lens-radar-feed.vercel.app — проект `lens-radar-feed` на Vercel (команда skylum1),
підключений до GitHub-репозиторію `nick-bielskykh/radar-lens`, гілка `main`.
Білду на Vercel нема: віддається готова статика з `site/hosted/` (див. `vercel.json`),
тому її треба комітити разом із даними. Пуш у `main` = новий деплой.
