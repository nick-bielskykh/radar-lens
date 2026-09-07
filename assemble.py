"""Збирає data/enriched/*.json (від enrich.py або агентів) + data/raw.json у data/items.json."""
import json, os, glob
ROOT = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(ROOT, "data")
raw = {r["id"]: r for r in json.load(open(os.path.join(DATA, "raw.json")))}
items, bad = [], []
for f in glob.glob(os.path.join(DATA, "enriched", "*.json")):
    rid = os.path.basename(f)[:-5]
    if rid.startswith("_") or rid not in raw: continue
    try: o = json.load(open(f))
    except Exception as e: bad.append((rid, str(e))); continue
    if not o.get("relevant", True): continue
    r = raw[rid]; n = len(r["page"]["images"])
    m = o.get("media") or {}
    if m.get("hero_image") is not None and not (0 <= m["hero_image"] < n): m["hero_image"] = 0 if n else None
    if m.get("kind") == "video" and not m.get("video"): m["kind"] = "image" if n else "none"
    o["media"] = m
    o["importance"] = max(1, min(5, int(o.get("importance", 2))))
    items.append({**{k: r[k] for k in ("id", "source", "url", "date")}, "page": r["page"], **({"tweet": r["tweet"]} if r.get("tweet") else {}), **o})
items.sort(key=lambda x: x["date"], reverse=True)
json.dump(items, open(os.path.join(DATA, "items.json"), "w"), ensure_ascii=False, indent=1)
print(f"{len(items)} новин; зламаних файлів: {bad}")
