"""Збір новин: RSS -> сторінка -> текст + медіа. Результат: data/raw.json, картинки в data/img/."""
import hashlib, io, json, os, re, sys, time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from urllib.parse import urljoin, urlparse

import base64
import feedparser, requests
from bs4 import BeautifulSoup
from PIL import Image

from sources import SOURCES, KEYWORDS, STRICT_KEYWORDS

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data"); IMG = os.path.join(DATA, "img")
os.makedirs(IMG, exist_ok=True)
DAYS = int(os.environ.get("DAYS", "14"))
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36 LensRadar/0.1"}
SINCE = datetime.now(timezone.utc) - timedelta(days=DAYS)
BAD_IMG = re.compile(r"(logo|avatar|icon|sprite|badge|pixel|tracking|gravatar|emoji|\.svg|\.gif|1x1|spacer|button)", re.I)


def log(*a): print(*a, file=sys.stderr, flush=True)

def get(url, **kw):
    return requests.get(url, headers=UA, timeout=25, **kw)

def resolve_youtube(url):
    try:
        html = get(url.rstrip("/") + "/videos", cookies={"CONSENT": "YES+cb", "SOCS": "CAI"}).text
        m = re.search(r'"externalId":"(UC[\w-]+)"', html) or re.search(r'channel_id=(UC[\w-]+)', html)
        if m: return f"https://www.youtube.com/feeds/videos.xml?channel_id={m.group(1)}"
    except Exception as e: log("yt resolve fail", url, e)
    return None

def gnews_decode(url):
    """Декодує посилання news.google.com/rss/articles/... в оригінальний URL."""
    m = re.search(r'/(?:articles|read)/([^?/]+)', url)
    if not m: return url
    gid = m.group(1)
    try:
        raw = base64.urlsafe_b64decode(gid + "==").decode("latin-1")
        if "AU_yqL" not in raw:
            mm = re.search(r'(https?://[ -~]+)', raw)
            if mm: return mm.group(1)
    except Exception: pass
    try:
        r = get(f"https://news.google.com/articles/{gid}")
        d = BeautifulSoup(r.text, "lxml").select_one("c-wiz > div")
        sg, ts = d.get("data-n-a-sg"), d.get("data-n-a-ts")
        payload = [["Fbv4je", json.dumps(["garturlreq", [["X", "X", ["X", "X"], None, None, 1, 1, "US:en", None, 1, None, None, None, None, None, 0, 1], "X", "X", 1, [1, 1, 1], 1, 1, None, 0, 0, None, 0], gid, ts, sg])]]
        r = requests.post("https://news.google.com/_/DotsSplashUi/data/batchexecute", headers={**UA, "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"}, data={"f.req": json.dumps([payload])}, timeout=25)
        arr = json.loads(r.text.split("\n\n")[1]); return json.loads(arr[0][2])[1]
    except Exception as e:
        log("gnews decode fail", e); return url

SPAM = re.compile(r"(deal|bundle|discount|% off|save \$|coupon|black friday|prime day|giveaway|sale)", re.I)

def entry_date(e):
    for k in ("published_parsed", "updated_parsed"):
        if e.get(k): return datetime(*e[k][:6], tzinfo=timezone.utc)
    return None

def matches(text, strict):
    t = text.lower()
    kws = STRICT_KEYWORDS if strict else KEYWORDS
    return any(k in t for k in kws)

def img_id(url): return hashlib.md5(url.encode()).hexdigest()[:12]

def download_image(url):
    """Завантажує, зменшує до 1000px по ширині, зберігає jpeg. Повертає (filename, w, h) або None."""
    fid = img_id(url); path = os.path.join(IMG, fid + ".jpg")
    if os.path.exists(path):
        with Image.open(path) as im: return fid + ".jpg", im.width, im.height
    try:
        r = get(url); r.raise_for_status()
        im = Image.open(io.BytesIO(r.content)); im.load()
        if im.width < 400 or im.height < 250: return None
        if im.mode in ("RGBA", "P", "LA"): im = im.convert("RGB")
        if im.width > 1000: im = im.resize((1000, int(im.height * 1000 / im.width)), Image.LANCZOS)
        im.save(path, "JPEG", quality=80, optimize=True)
        return fid + ".jpg", im.width, im.height
    except Exception: return None

def yt_id(url):
    m = re.search(r"(?:youtu\.be/|youtube(?:-nocookie)?\.com/(?:embed/|watch\?v=|shorts/|v/))([\w-]{11})", url or "")
    return m.group(1) if m else None

def extract_page(url):
    """Повертає dict: text, images[], videos[], before_after[]"""
    out = {"text": "", "images": [], "videos": [], "before_after": []}
    try:
        r = get(url); r.raise_for_status(); html = r.text
    except Exception as e:
        log("page fail", url, e); return out
    soup = BeautifulSoup(html, "lxml")
    for t in soup(["script", "style", "nav", "footer", "header", "aside", "form", "noscript"]): t.decompose()
    main = soup.find("article") or soup.find("main") or soup.body or soup
    paras = [p.get_text(" ", strip=True) for p in main.find_all(["p", "li", "h2", "h3"])]
    out["text"] = "\n".join(p for p in paras if len(p) > 40)[:12000]

    # og:image першим
    og = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "twitter:image"})
    cands = []
    if og and og.get("content"): cands.append((urljoin(url, og["content"]), "", ""))
    for im in main.find_all("img"):
        src = im.get("data-src") or im.get("data-lazy-src") or im.get("src") or ""
        if im.get("srcset"):  # беремо найбільший
            parts = [s.strip().split(" ")[0] for s in im["srcset"].split(",") if s.strip()]
            if parts: src = parts[-1]
        if not src or src.startswith("data:") or BAD_IMG.search(src): continue
        alt = (im.get("alt") or "").strip()
        cap = ""
        fig = im.find_parent("figure")
        if fig and fig.find("figcaption"): cap = fig.find("figcaption").get_text(" ", strip=True)
        cands.append((urljoin(url, src), alt, cap))
    # унікальні, до 8
    seen, uniq = set(), []
    for c in cands:
        key = c[0].split("?")[0]
        if key in seen: continue
        seen.add(key); uniq.append(c)
        if len(uniq) >= 8: break
    with ThreadPoolExecutor(6) as ex:
        results = list(ex.map(lambda c: download_image(c[0]), uniq))
    for (src, alt, cap), res in zip(uniq, results):
        if res: out["images"].append({"file": res[0], "w": res[1], "h": res[2], "alt": alt, "cap": cap, "src": src})

    # відео: iframe youtube, посилання на youtube, <video>
    for f in main.find_all("iframe"):
        v = yt_id(f.get("src") or f.get("data-src"))
        if v: out["videos"].append({"yt": v})
    for a in main.find_all("a", href=True):
        v = yt_id(a["href"])
        if v: out["videos"].append({"yt": v})
    for v in main.find_all("video"):
        s = v.get("src") or (v.find("source") or {}).get("src")
        if s and not s.startswith("blob:"): out["videos"].append({"mp4": urljoin(url, s), "poster": v.get("poster")})
    uniq_v, seen = [], set()
    for v in out["videos"]:
        k = v.get("yt") or v.get("mp4")
        if k not in seen: seen.add(k); uniq_v.append(v)
    out["videos"] = uniq_v[:4]

    # before/after: пари сусідніх картинок з підказками в alt/caption/src, або відомі слайдери
    imgs = out["images"]
    def is_before(i): return bool(re.search(r"\b(before|original|source|input)\b", (i["alt"] + " " + i["cap"] + " " + i["src"]), re.I))
    def is_after(i): return bool(re.search(r"\b(after|result|output|edited|enhanced)\b", (i["alt"] + " " + i["cap"] + " " + i["src"]), re.I))
    for i in range(len(imgs) - 1):
        a, b = imgs[i], imgs[i + 1]
        if is_before(a) and is_after(b) and abs(a["w"] / a["h"] - b["w"] / b["h"]) < 0.05:
            out["before_after"].append([a["file"], b["file"]])
    # слайдери типу twentytwenty / juxtapose / beer-slider
    for sl in soup.select(".twentytwenty-container, .juxtapose, .beer-slider, [class*=before-after], [class*=compare]"):
        ims = [urljoin(url, (i.get("data-src") or i.get("src") or "")) for i in sl.find_all("img")][:2]
        if len(ims) == 2:
            res = [download_image(u) for u in ims]
            if all(res) and abs(res[0][1]/res[0][2] - res[1][1]/res[1][2]) < 0.05:
                out["before_after"].append([res[0][0], res[1][0]])
                for u, rr in zip(ims, res):
                    if not any(x["file"] == rr[0] for x in out["images"]):
                        out["images"].append({"file": rr[0], "w": rr[1], "h": rr[2], "alt": "", "cap": "", "src": u})
    return out

def collect_source(s):
    kind = s.get("kind", "rss"); url = s.get("url")
    if kind == "gnews":
        url = f"https://news.google.com/rss/search?q={requests.utils.quote(s['q'])}+when:{DAYS}d&hl=en-US&gl=US&ceid=US:en"
    if kind == "youtube":
        url = resolve_youtube(url)
        if not url: return []
    try:
        r = get(url); fp = feedparser.parse(r.content)
    except Exception as e:
        log("feed fail", s["name"], e); return []
    if fp.bozo and not fp.entries: log("feed empty/bozo", s["name"], url); return []
    items = []
    for e in fp.entries[:60]:
        d = entry_date(e)
        if not d or d < SINCE: continue
        title = e.get("title", "").strip(); link = e.get("link", "")
        src_name = s["name"]
        if kind == "gnews":
            if SPAM.search(title): continue
            src_name = (e.get("source") or {}).get("title") or "Google News"
            title = re.sub(r"\s+-\s+[^-]+$", "", title)  # прибрати " - Назва видання"
            link = gnews_decode(link)
        summary = BeautifulSoup(e.get("summary", "") or "", "lxml").get_text(" ", strip=True)
        if s.get("filter") and not matches(title + " " + summary, s.get("strict")): continue
        items.append({"id": hashlib.md5(link.encode()).hexdigest()[:10], "source": src_name, "query": s.get("q"), "cat_hint": s["cat_hint"],
                      "kind": kind, "title": title, "url": link, "date": d.isoformat(), "summary": summary[:2000],
                      "yt": yt_id(link) if kind == "youtube" else None})
    log(f"{s.get('q') or s['name']}: {len(items)} за {DAYS} дн.")
    return items

def main():
    with ThreadPoolExecutor(8) as ex:
        all_items = [i for lst in ex.map(collect_source, SOURCES) for i in lst]
    seen, uniq = set(), []
    for it in all_items:
        key = it["url"].split("?")[0].rstrip("/")
        if key in seen or "news.google.com" in key: continue
        seen.add(key); uniq.append(it)
    all_items = uniq
    log(f"Разом кандидатів: {len(all_items)}")
    # сторінки
    def enrich(it):
        if it["kind"] == "youtube":
            th = download_image(f"https://i.ytimg.com/vi/{it['yt']}/maxresdefault.jpg") or download_image(f"https://i.ytimg.com/vi/{it['yt']}/hqdefault.jpg")
            it["page"] = {"text": it["summary"], "images": [{"file": th[0], "w": th[1], "h": th[2], "alt": "", "cap": "", "src": ""}] if th else [],
                          "videos": [{"yt": it["yt"]}], "before_after": []}
        elif it["kind"] == "reddit":
            it["page"] = extract_page(it["url"])
        else:
            it["page"] = extract_page(it["url"])
        return it
    with ThreadPoolExecutor(6) as ex:
        all_items = list(ex.map(enrich, all_items))
    all_items.sort(key=lambda x: x["date"], reverse=True)
    json.dump(all_items, open(os.path.join(DATA, "raw.json"), "w"), ensure_ascii=False, indent=1)
    with_media = sum(1 for i in all_items if i["page"]["images"] or i["page"]["videos"])
    ba = sum(1 for i in all_items if i["page"]["before_after"])
    log(f"Збережено {len(all_items)} новин, з медіа: {with_media}, з before/after: {ba}")

if __name__ == "__main__":
    main()
