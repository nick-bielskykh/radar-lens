"""Збирає site/index.html (картинки як data URI, для артефакту) і site/hosted/index.html (картинки файлами, для хостингу)."""
import base64, json, os, shutil
from PIL import Image

def ahash(path):
    im = Image.open(path).convert("L").resize((16, 16), Image.LANCZOS); px = list(im.getdata()); avg = sum(px) / len(px)
    return sum(1 << i for i, p in enumerate(px) if p > avg)

def near(a, b): return bin(a ^ b).count("1") <= 12
ROOT = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(ROOT, "data"); IMG = os.path.join(DATA, "img")
SITE = os.path.join(ROOT, "site"); os.makedirs(os.path.join(SITE, "hosted", "img"), exist_ok=True)
tpl = open(os.path.join(ROOT, "template.html")).read()
items = json.load(open(os.path.join(DATA, "items.json")))

# картинка, що є hero у 2+ постах, — логотип джерела, а не ілюстрація
from collections import Counter
_hero_hash = {}
for _it in items:
    _p = _it["page"]; _m = _it["media"]
    if _p["images"] and _m.get("hero_image") is not None and 0 <= _m["hero_image"] < len(_p["images"]):
        _path = os.path.join(IMG, _p["images"][_m["hero_image"]]["file"])
        if os.path.exists(_path): _hero_hash[_it["id"]] = ahash(_path)
_counts = Counter(); _seen = []
for _h in _hero_hash.values():
    _k = next((x for x in _seen if near(_h, x)), None)
    if _k is None: _seen.append(_h); _k = _h
    _counts[_k] += 1
LOGO_HASHES = [h for h, c in _counts.items() if c >= 2]
if LOGO_HASHES: print(f"логотипів серед hero: {len(LOGO_HASHES)} (прибрано з постів)")

def slim(it, inline):
    p = it["page"]; imgs = []; hashes = []; remap = {}
    m = dict(it["media"])
    order = list(range(len(p["images"])))
    if m.get("hero_image") is not None and m["hero_image"] in order:  # hero першим, щоб дублі падали на нього
        order.remove(m["hero_image"]); order.insert(0, m["hero_image"])
    for idx in order:
        im = p["images"][idx]; path = os.path.join(IMG, im["file"])
        if not os.path.exists(path): continue
        h = ahash(path)
        if any(near(h, x) for x in hashes) or any(near(h, x) for x in LOGO_HASHES): continue
        hashes.append(h); remap[idx] = len(imgs)
        if inline:
            uri = "data:image/jpeg;base64," + base64.b64encode(open(path, "rb").read()).decode()
        else:
            shutil.copy(path, os.path.join(SITE, "hosted", "img", im["file"])); uri = "/img/" + im["file"]
        imgs.append({"uri": uri, "w": im["w"], "h": im["h"], "alt": im["alt"], **({"generated": True} if im.get("generated") else {})})
    if m.get("hero_image") is not None: m["hero_image"] = remap.get(m["hero_image"], 0 if imgs else None)
    if not imgs and m.get("kind") in ("image", "gallery"): m["kind"] = "none"
    out = {k: it[k] for k in ("id", "source", "url", "date", "title", "lead", "full", "means", "importance", "category")} | {"media": m, "page": {"images": imgs, "videos": [v for v in p["videos"] if v.get("yt")]}}
    if it.get("tweet"): out["tweet"] = it["tweet"]
    return out

import html
SITE_URL = "https://lens-radar-feed.vercel.app"

def page(data, single, title, meta=""):
    js = json.dumps(data, ensure_ascii=False).replace("</script", "<\\/script")
    return tpl.replace("__TITLE__", html.escape(title)).replace("__META__", meta).replace("__SINGLE__", "true" if single else "false").replace("__DATA__", js)

for inline, out in ((True, os.path.join(SITE, "index.html")), (False, os.path.join(SITE, "hosted", "index.html"))):
    open(out, "w").write(page([slim(i, inline) for i in items], False, "Lens Radar"))
    print(out, f"{os.path.getsize(out)/1e6:.1f} MB")

# окрема сторінка на кожен пост: /p/<id> (cleanUrls у vercel.json)
PDIR = os.path.join(SITE, "hosted", "p"); shutil.rmtree(PDIR, ignore_errors=True); os.makedirs(PDIR)
for it in items:
    s = slim(it, False)
    hero = s["page"]["images"][s["media"]["hero_image"]] if s["media"].get("hero_image") is not None and s["page"]["images"] else None
    meta = "\n".join(f'<meta property="{k}" content="{html.escape(v, quote=True)}">' for k, v in [
        ("og:type", "article"), ("og:site_name", "Lens Radar"), ("og:title", s["title"]),
        ("og:description", s["lead"]), ("og:url", f"{SITE_URL}/p/{s['id']}"),
    ] + ([("og:image", SITE_URL + hero["uri"])] if hero else []))
    meta += '\n<meta name="twitter:card" content="' + ("summary_large_image" if hero else "summary") + '">'
    open(os.path.join(PDIR, s["id"] + ".html"), "w").write(page([s], True, s["title"] + " — Lens Radar", meta))
print(f"{len(items)} сторінок постів у site/hosted/p/")
