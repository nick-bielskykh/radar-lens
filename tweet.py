"""Додає твіти як кандидатів у data/raw.json.
Використання: python tweet.py <url або id> [...]. Дані з api.fxtwitter.com (без ключів), фото в data/img/.
Кандидат далі проходить звичайну редакторську обробку (EDITOR.md) і рендериться карткою твіта."""
import base64, hashlib, io, json, os, re, sys
from datetime import datetime, timezone

import requests
from PIL import Image

from fetch import DATA, download_image, log, yt_id

def tweet_id(s):
    m = re.search(r"(?:x\.com|twitter\.com)/(\w+)/status/(\d+)", s) or re.search(r"^(\d{6,})$", s.strip())
    return (m.group(2) if m.lastindex == 2 else m.group(1)) if m else None

def avatar_uri(url):
    """Аватар 96px як data URI, щоб картка не залежала від pbs.twimg.com."""
    try:
        im = Image.open(io.BytesIO(requests.get(url, timeout=15).content)).convert("RGB").resize((96, 96), Image.LANCZOS)
        buf = io.BytesIO(); im.save(buf, "JPEG", quality=80)
        return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    except Exception: return None

def fetch_tweet(tid):
    r = requests.get(f"https://api.fxtwitter.com/i/status/{tid}", headers={"User-Agent": "LensRadar/0.1"}, timeout=25)
    d = r.json()
    if d.get("code") != 200 or not d.get("tweet"):
        log("tweet fail", tid, d.get("message")); return None
    t = d["tweet"]; a = t["author"]
    media = t.get("media") or {}
    images, videos = [], []
    for ph in media.get("photos") or []:
        res = download_image(ph["url"])
        if res: images.append({"file": res[0], "w": res[1], "h": res[2], "alt": ph.get("altText") or "", "cap": "", "src": ph["url"]})
    for v in media.get("videos") or []:
        th = v.get("thumbnail_url")
        res = download_image(th) if th else None
        if res and not any(i["src"] == th for i in images):
            images.append({"file": res[0], "w": res[1], "h": res[2], "alt": "", "cap": "", "src": th})
        videos.append({"mp4": v.get("url"), "poster": th})
    text = t.get("text") or ""
    date = datetime.fromtimestamp(t["created_timestamp"], tz=timezone.utc).isoformat()
    url = t["url"]
    return {"id": hashlib.md5(url.encode()).hexdigest()[:10], "source": f"X · @{a['screen_name']}", "query": None, "cat_hint": "comp",
            "kind": "tweet", "title": text.split("\n")[0][:140], "url": url, "date": date, "summary": text[:2000], "yt": None,
            "page": {"text": text, "images": images, "videos": videos},
            "tweet": {"name": a["name"], "handle": a["screen_name"], "avatar": avatar_uri(a["avatar_url"]) if a.get("avatar_url") else None, "text": text,
                      "likes": t.get("likes"), "reposts": t.get("retweets"), "views": t.get("views")}}

def main(args):
    ids = [tweet_id(a) for a in args]
    if not args or None in ids:
        print(__doc__, file=sys.stderr); sys.exit(2)
    path = os.path.join(DATA, "raw.json")
    raw = json.load(open(path)) if os.path.exists(path) else []
    have = {r["id"] for r in raw}; added = 0
    for tid in ids:
        it = fetch_tweet(tid)
        if not it: continue
        if it["id"] in have: log("вже є:", it["url"]); continue
        raw.append(it); have.add(it["id"]); added += 1
        log("✓", it["id"], f"@{it['tweet']['handle']}:", it["title"][:80])
    raw.sort(key=lambda x: x["date"], reverse=True)
    json.dump(raw, open(path, "w"), ensure_ascii=False, indent=1)
    log(f"Додано {added} твітів, разом {len(raw)} кандидатів")

if __name__ == "__main__":
    main(sys.argv[1:])
