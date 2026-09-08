"""Збирає data/enriched/*.json (від enrich.py або агентів) + data/raw.json у data/items.json."""
import json, os, glob, hashlib, io, re, sys
from datetime import datetime, timezone, timedelta
import requests
from PIL import Image
ROOT = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(ROOT, "data")
raw = {r["id"]: r for r in json.load(open(os.path.join(DATA, "raw.json")))}
IMG = os.path.join(DATA, "img")

def illustrate(r):
    """Генерує ілюстрацію через pollinations.ai (без ключа) для поста без медіа. Кеш у data/img/gen_<id>.jpg."""
    fid = "gen_" + r["id"] + ".jpg"; path = os.path.join(IMG, fid)
    if not os.path.exists(path):
        topic = re.sub(r"\s+", " ", (r["title"] + ". " + (r["summary"] or r["page"]["text"])[:200])).strip()
        prompt = f"Editorial illustration for a tech news article about: {topic}. Dark minimal style, photography and image editing theme, abstract, no text, no letters, no logos."
        try:
            resp = requests.get("https://image.pollinations.ai/prompt/" + requests.utils.quote(prompt[:600]),
                                params={"width": 1000, "height": 563, "nologo": "true", "seed": int(r["id"][:6], 16)}, timeout=90)
            resp.raise_for_status(); im = Image.open(io.BytesIO(resp.content)).convert("RGB"); im.load()
            im.save(path, "JPEG", quality=80, optimize=True)
        except Exception as e:
            print("illustrate fail", r["id"], e, file=sys.stderr); return None
    with Image.open(path) as im: return {"file": fid, "w": im.width, "h": im.height, "alt": "", "cap": "", "src": "", "generated": True}
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
    if not r["page"]["images"] and not any(v.get("yt") for v in r["page"]["videos"]) and not r.get("tweet"):
        g = illustrate(r)
        if g:
            r["page"]["images"] = [g]; m = {"kind": "image", "hero_image": 0, "video": None, "generated": True}
    o["media"] = m
    o["importance"] = max(1, min(5, int(o.get("importance", 2))))
    items.append({**{k: r[k] for k in ("id", "source", "url", "date")}, "page": r["page"], **({"tweet": r["tweet"]} if r.get("tweet") else {}), **o})
cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
items = [i for i in items if i["date"] >= cutoff]   # стрічка — 30 днів
items.sort(key=lambda x: x["date"], reverse=True)
json.dump(items, open(os.path.join(DATA, "items.json"), "w"), ensure_ascii=False, indent=1)
print(f"{len(items)} новин; зламаних файлів: {bad}")
