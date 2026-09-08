"""Перевірка стрічки перед пушем. Ненульовий код виходу = не пушити.
Порівнює data/items.json з версією в HEAD: кількість не впала більш ніж на 20%, дати в 30-денному вікні,
у кожного поста є заголовок/лід/означає, обкладинки існують у site/hosted/img/, сторінки /p/ згенеровані."""
import json, os, subprocess, sys
from datetime import datetime, timezone, timedelta
ROOT = os.path.dirname(os.path.abspath(__file__))
items = json.load(open(os.path.join(ROOT, "data", "items.json")))
errs, warns = [], []
try:
    prev = json.loads(subprocess.run(["git", "show", "HEAD:data/items.json"], capture_output=True, text=True, cwd=ROOT, check=True).stdout)
except Exception:
    prev = None
if prev is not None:
    lost = {i["id"] for i in prev} - {i["id"] for i in items}
    cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    lost_fresh = [i for i in prev if i["id"] in lost and i["date"] >= cutoff]
    if len(items) < len(prev) * 0.8: errs.append(f"стрічка скоротилась: {len(prev)} → {len(items)}")
    if len(lost_fresh) > 3: errs.append(f"зникли свіжі пости: {[i['title'][:40] for i in lost_fresh]}")
    elif lost_fresh: warns.append(f"зникли свіжі пости: {[i['title'][:40] for i in lost_fresh]}")
now = datetime.now(timezone.utc).isoformat(); cutoff = (datetime.now(timezone.utc) - timedelta(days=31)).isoformat()
hosted = os.path.join(ROOT, "site", "hosted")
for i in items:
    t = i["title"][:40]
    if i["date"] < cutoff: errs.append(f"старіше 30 днів: {t} ({i['date'][:10]})")
    if i["date"] > now: errs.append(f"дата в майбутньому: {t} ({i['date'][:10]})")
    for k in ("title", "lead", "means"):
        if not (i.get(k) or "").strip(): errs.append(f"порожнє {k}: {t}")
    if not i.get("full"): errs.append(f"порожній full: {t}")
    if i["importance"] not in range(1, 6): errs.append(f"оцінка поза 1..5: {t}")
    if i["category"] not in ("comp", "ai", "algo", "market"): errs.append(f"невідома категорія {i['category']}: {t}")
    if not os.path.exists(os.path.join(hosted, "p", i["id"] + ".html")): errs.append(f"нема сторінки /p/{i['id']}")
    m = i.get("media") or {}
    if m.get("hero_image") is not None and i["page"]["images"]:
        h = i["page"]["images"][m["hero_image"]] if 0 <= m["hero_image"] < len(i["page"]["images"]) else None
        if not h or not os.path.exists(os.path.join(hosted, "img", h["file"])): errs.append(f"нема обкладинки: {t}")
if not os.path.exists(os.path.join(hosted, "index.html")): errs.append("нема site/hosted/index.html")
for w in warns: print("⚠", w)
for e in errs: print("✗", e)
print(f"{'FAIL' if errs else 'OK'}: {len(items)} постів, помилок {len(errs)}, попереджень {len(warns)}")
sys.exit(1 if errs else 0)
