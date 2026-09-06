"""Обробка через Claude: відсів шуму -> українські тексти, оцінка, категорія, вибір медіа.
Вхід data/raw.json, вихід data/items.json. Кеш по кожній новині в data/enriched/."""
import json, os, sys
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional, Literal

import anthropic
from pydantic import BaseModel

ROOT = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(ROOT, "data")
CACHE = os.path.join(DATA, "enriched"); os.makedirs(CACHE, exist_ok=True)
MODEL = os.environ.get("MODEL", "claude-opus-5")
client = anthropic.Anthropic()
CONTEXT = open(os.path.join(ROOT, "luminar_context.md")).read()

def log(*a): print(*a, file=sys.stderr, flush=True)

# ---------- етап 1: відсів ----------
class TriageItem(BaseModel):
    id: str
    keep: bool
    dup_of: Optional[str] = None   # id іншої новини про ту саму подію, якщо ця гірша

class Triage(BaseModel):
    items: List[TriageItem]

TRIAGE_SYS = f"""Ти редактор внутрішнього порталу новин для продакт-команди Skylum (Luminar Neo, Luminar Mobile).
Портал збирає новини про фоторедагування: конкуренти, AI-моделі та алгоритми обробки зображень, ринок фотософту.

{CONTEXT}

Тобі дають список кандидатів (id, джерело, заголовок, короткий опис). Для кожного вирішуй:
- keep=true, якщо новина стосується фоторедагування, AI для зображень, конкурентів або ринку фотософту і має цінність для продакта.
- keep=false для: не по темі (нерухомість, спорт, музика), рекламних добірок і знижок, загальних порад "як редагувати", кадрових новин без впливу на продукт, SEO-статей-порівнянь низької якості.
- Якщо кілька кандидатів описують ту саму подію, залиш найкращий (першоджерело або найповніший), а в інших постав keep=false і dup_of=<id найкращого>.
Поверни рішення для КОЖНОГО id зі списку."""

def triage(raw):
    cache = os.path.join(CACHE, "_triage.json")
    if os.path.exists(cache):
        return json.load(open(cache))
    lines = [{"id": r["id"], "source": r["source"], "title": r["title"], "summary": (r["summary"] or r["page"]["text"])[:220]} for r in raw]
    res = client.messages.parse(
        model=MODEL, max_tokens=32000, system=TRIAGE_SYS,
        messages=[{"role": "user", "content": json.dumps(lines, ensure_ascii=False)}],
        output_format=Triage,
    )
    out = {t.id: t.model_dump() for t in res.parsed_output.items}
    json.dump(out, open(cache, "w"), ensure_ascii=False, indent=1)
    return out

# ---------- етап 2: збагачення ----------
class Media(BaseModel):
    kind: Literal["ba", "video", "gallery", "image", "none"]
    hero_image: Optional[int] = None      # індекс у списку images для головної картинки (image/gallery/video-постер)
    ba_pair: Optional[List[int]] = None   # [before_idx, after_idx] індекси в images, тільки якщо це справді пара до/після одного кадру
    video: Optional[str] = None           # youtube id, якщо kind=video

class Enriched(BaseModel):
    relevant: bool
    title: str            # заголовок українською, до 90 символів, без клікбейту
    lead: str             # 1–2 речення українською: що сталося
    full: List[str]       # 2–3 абзаци українською з деталями: як працює, ціна, доступність, платформи, ліцензія
    means: str            # 2–4 речення: що це означає для Luminar Neo та/або Mobile; конкретно, з назвами наших фіч
    importance: int       # 1..5 за рубрикою
    category: Literal["comp", "ai", "algo", "market"]
    media: Media

ENRICH_SYS = f"""Ти пишеш пости для внутрішнього порталу новин продакт-команди Skylum. Мова: українська. Тон: діловий, конкретний, без води й без клікбейту.

{CONTEXT}

Рубрика для importance (оцінюй чесно, більшість новин — 2 або 3):
5 — реліз tier-1 конкурента або доступна модель/API, що прямо перетинається з нашою ключовою фічею і змінює очікування користувачів.
4 — реліз tier-2 конкурента з фічею, якої в нас нема, або відкрита модель, яку реально інтегрувати.
3 — помітне оновлення конкурента чи дослідження з практичною цінністю, але без прямої загрози.
2 — контекст: ринкові дані, огляди, бета-функції, дослідження без коду.
1 — фон.

Категорії: comp = конкуренти й продукти, ai = генеративні та нейромережеві моделі, algo = класичні алгоритми та дослідження обробки зображень, market = ринок, опитування, бізнес.

Медіа: тобі дають список зображень зі сторінки (індекс, розмір, alt, підпис) і відео. Вибери головне медіа:
- kind="ba" ТІЛЬКИ якщо серед зображень є справжня пара "до/після" одного кадру (з alt/підписів або очевидних назв файлів). Не вигадуй пари.
- kind="video", якщо є YouTube-відео і воно є суттю новини (демо, огляд). Вкажи hero_image як постер, якщо є.
- kind="gallery", якщо є 3+ змістовних зображення. hero_image — найінформативніше.
- kind="image", якщо є одне-два зображення.
- kind="none", якщо зображень нема або вони декоративні (стокові фото, логотипи).
Пропускай зображення, що виглядають як реклама, аватари, банери.

relevant=false, якщо після читання повного тексту виявилось, що новина не про фоторедагування / AI для зображень / конкурентів."""

def enrich_one(r):
    cache = os.path.join(CACHE, r["id"] + ".json")
    if os.path.exists(cache):
        return json.load(open(cache))
    p = r["page"]
    imgs = [{"idx": i, "w": im["w"], "h": im["h"], "alt": im["alt"][:120], "caption": im["cap"][:160], "file": im["src"].rsplit("/", 1)[-1][:60]} for i, im in enumerate(p["images"])]
    payload = {"source": r["source"], "date": r["date"][:10], "url": r["url"], "title": r["title"],
               "summary": r["summary"], "text": p["text"][:9000], "images": imgs,
               "videos": [v.get("yt") for v in p["videos"] if v.get("yt")], "detected_before_after_pairs": p["before_after"]}
    try:
        res = client.messages.parse(
            model=MODEL, max_tokens=16000, system=ENRICH_SYS,
            messages=[{"role": "user", "content": json.dumps(payload, ensure_ascii=False)}],
            output_format=Enriched,
        )
        out = res.parsed_output.model_dump()
    except Exception as e:
        log("enrich fail", r["id"], r["title"][:50], e); return None
    json.dump(out, open(cache, "w"), ensure_ascii=False, indent=1)
    log(("✓" if out["relevant"] else "✗"), out["importance"], out["title"][:70])
    return out

def main():
    raw = json.load(open(os.path.join(DATA, "raw.json")))
    tri = triage(raw)
    keep = [r for r in raw if tri.get(r["id"], {}).get("keep")]
    log(f"Після відсіву: {len(keep)} з {len(raw)}")
    with ThreadPoolExecutor(4) as ex:
        outs = list(ex.map(enrich_one, keep))
    items = []
    for r, o in zip(keep, outs):
        if not o or not o["relevant"]: continue
        items.append({**{k: r[k] for k in ("id", "source", "url", "date")}, "page": r["page"], **o})
    items.sort(key=lambda x: x["date"], reverse=True)
    json.dump(items, open(os.path.join(DATA, "items.json"), "w"), ensure_ascii=False, indent=1)
    log(f"Готово: {len(items)} новин у data/items.json")

if __name__ == "__main__":
    main()
