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
        if any(near(h, x) for x in hashes): continue
        hashes.append(h); remap[idx] = len(imgs)
        if inline:
            uri = "data:image/jpeg;base64," + base64.b64encode(open(path, "rb").read()).decode()
        else:
            shutil.copy(path, os.path.join(SITE, "hosted", "img", im["file"])); uri = "img/" + im["file"]
        imgs.append({"uri": uri, "w": im["w"], "h": im["h"], "alt": im["alt"]})
    if m.get("hero_image") is not None: m["hero_image"] = remap.get(m["hero_image"], 0 if imgs else None)
    if m.get("ba_pair"):
        pair = [remap.get(i) for i in m["ba_pair"]]
        m["ba_pair"] = pair if None not in pair else None
    return {k: it[k] for k in ("id", "source", "url", "date", "title", "lead", "full", "means", "importance", "category")} | {"media": m, "page": {"images": imgs, "videos": [v for v in p["videos"] if v.get("yt")]}}

for inline, out in ((True, os.path.join(SITE, "index.html")), (False, os.path.join(SITE, "hosted", "index.html"))):
    data = json.dumps([slim(i, inline) for i in items], ensure_ascii=False).replace("</script", "<\\/script")
    open(out, "w").write(tpl.replace("__DATA__", data))
    print(out, f"{os.path.getsize(out)/1e6:.1f} MB")
