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
BAD_IMG = re.compile(r"(logo|avatar|icon|sprite|badge|pixel|tracking|gravatar|emoji|\.svg|\.gif|1x1|spacer|button|smileybones|/static/base/)", re.I)


def log(*a): print(*a, file=sys.stderr, flush=True)

SESSION = requests.Session()
SESSION.headers.update(UA)

def get(url, tries=3, **kw):
    """GET з ретраями на 429/5xx — Reddit і Google News інколи тротлять паралельні запити."""
    last = None
    for i in range(tries):
        try:
            r = SESSION.get(url, timeout=25, **kw)
            if r.status_code in (429, 500, 502, 503, 504) and i < tries - 1:
                time.sleep(2 ** i + 1); continue
            return r
        except requests.RequestException as e:
            last = e
            if i == tries - 1: raise
            time.sleep(2 ** i + 1)
    raise last

def resolve_youtube(url):
    try:
        html = get(url.rstrip("/") + "/videos", cookies={"CONSENT": "YES+cb", "SOCS": "CAI"}).text
        m = re.search(r'"externalId":"(UC[\w-]+)"', html) or re.search(r'channel_id=(UC[\w-]+)', html)
        if m: return f"https://www.youtube.com/feeds/videos.xml?channel_id={m.group(1)}"
    except Exception as e: log("yt resolve fail", url, e)
    return None

GNEWS_BATCH_URL = "https://news.google.com/_/DotsSplashUi/data/batchexecute"

def gnews_meta(gid):
    """Витягує data-n-a-id/ts/sg зі сторінки статті. Саме /rss/articles/ — /articles/ віддає 429."""
    try:
        r = get(f"https://news.google.com/rss/articles/{gid}")
        d = BeautifulSoup(r.text, "lxml").select_one("c-wiz > div")
        if not d or not d.get("data-n-a-sg"): return None
        return d["data-n-a-id"], d["data-n-a-ts"], d["data-n-a-sg"]
    except Exception as e:
        log("gnews meta fail", gid[:24], e); return None

def gnews_decode_many(links):
    """Декодує посилання news.google.com/rss/articles/... в оригінальні URL. Повертає {link: url}."""
    gids, out = {}, {}
    for l in links:
        m = re.search(r"/(?:articles|read)/([^?/]+)", l)
        if not m: out[l] = l; continue
        gid = m.group(1)
        # частина id містить URL у відкритому вигляді
        try:
            raw = base64.urlsafe_b64decode(gid + "==").decode("latin-1")
            if "AU_yqL" not in raw:
                mm = re.search(r"(https?://[ -~]+)", raw)
                if mm: out[l] = mm.group(1); continue
        except Exception: pass
        gids[l] = gid
    if not gids: return out
    items = list(gids.items())
    with ThreadPoolExecutor(8) as ex:
        metas = list(ex.map(lambda kv: gnews_meta(kv[1]), items))
    pending = [(l, m) for (l, _), m in zip(items, metas) if m]
    for (l, _), m in zip(items, metas):
        if not m: out[l] = None
    for i in range(0, len(pending), 20):
        chunk = pending[i:i + 20]
        # 4-й елемент — id запиту: відповіді приходять НЕ по порядку, зіставляємо по ньому
        payload = [["Fbv4je", json.dumps(["garturlreq", [["X", "X", ["X", "X"], None, None, 1, 1, "US:en", None, 1, None, None, None, None, None, 0, 1], "X", "X", 1, [1, 1, 1], 1, 1, None, 0, 0, None, 0], aid, ts, sg]), None, str(j)]
                   for j, (_, (aid, ts, sg)) in enumerate(chunk)]
        got = {}
        try:
            r = SESSION.post(GNEWS_BATCH_URL, headers={"Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"},
                             data={"f.req": json.dumps([payload])}, timeout=30)
            for line in r.text.split("\n"):
                if '"wrb.fr"' not in line: continue
                for row in json.loads(line):
                    if row[0] == "wrb.fr" and row[1] == "Fbv4je" and row[2] and len(row) > 6 and row[6] is not None:
                        got[int(row[6])] = json.loads(row[2])[1]
            if len(got) != len(chunk):
                log(f"gnews batch: {len(got)} відповідей на {len(chunk)} запитів")
        except Exception as e:
            log("gnews batch fail", e)
        for j, (l, _) in enumerate(chunk): out[l] = got.get(j)
    return out

SPAM = re.compile(r"(deal|bundle|discount|% off|save \$|coupon|black friday|prime day|giveaway|\bsale\b|free right now|\bvs\.?\b|specs and price|release date|leak|rumou?r|stock (price|heading|down|up)|earnings|tax credit)", re.I)

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

def arxiv_figures(url):
    """Для arXiv: фігури з HTML-версії статті (на сторінці абстракту картинок нема, лише логотип)."""
    m = re.search(r"arxiv\.org/(?:abs|pdf|html)/(\d{4}\.\d{4,5})", url)
    if not m: return None
    try:
        r = get(f"https://arxiv.org/html/{m.group(1)}"); r.raise_for_status()
    except Exception: return []
    soup = BeautifulSoup(r.text, "lxml"); cands = []
    for fig in soup.find_all("figure"):
        im = fig.find("img")
        if not im or not im.get("src") or BAD_IMG.search(im["src"]): continue
        cap = fig.find("figcaption"); cap = cap.get_text(" ", strip=True)[:200] if cap else ""
        cands.append((urljoin(r.url, im["src"]), (im.get("alt") or "")[:120], cap))
        if len(cands) >= 6: break
    return cands

def page_date(soup):
    """Дата публікації зі сторінки: meta article:published_time / datePublished (ld+json) / <time datetime>."""
    for sel in ({"property": "article:published_time"}, {"name": "article:published_time"}, {"property": "og:published_time"},
                {"name": "pubdate"}, {"name": "publish-date"}, {"name": "date"}, {"itemprop": "datePublished"}, {"name": "DC.date.issued"}):
        m = soup.find("meta", attrs=sel)
        if m and m.get("content"):
            d = parse_date(m["content"])
            if d: return d
    for sc in soup.find_all("script", type="application/ld+json"):
        try: data = json.loads(sc.string or "")
        except Exception: continue
        stack = data if isinstance(data, list) else [data]
        while stack:
            o = stack.pop()
            if isinstance(o, dict):
                if o.get("datePublished"):
                    d = parse_date(o["datePublished"])
                    if d: return d
                stack.extend(v for v in o.values() if isinstance(v, (dict, list)))
            elif isinstance(o, list): stack.extend(o)
    t = soup.find("time", attrs={"datetime": True})
    return parse_date(t["datetime"]) if t else None

def parse_date(v):
    try:
        d = datetime.fromisoformat(v.strip().replace("Z", "+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except Exception: return None

def extract_page(url):
    """Повертає dict: text, images[], videos[], published (ISO або None)"""
    out = {"text": "", "images": [], "videos": [], "published": None}
    try:
        r = get(url); r.raise_for_status(); html = r.text
    except Exception as e:
        log("page fail", url, e); return out
    soup = BeautifulSoup(html, "lxml")
    pd = page_date(soup); out["published"] = pd.isoformat() if pd else None
    figs = arxiv_figures(url)
    for t in soup(["script", "style", "nav", "footer", "header", "aside", "form", "noscript"]): t.decompose()
    main = soup.find("article") or soup.find("main") or soup.body or soup
    paras = [p.get_text(" ", strip=True) for p in main.find_all(["p", "li", "h2", "h3"])]
    out["text"] = "\n".join(p for p in paras if len(p) > 40)[:12000]

    # og:image першим (крім arXiv — там це логотип, беремо фігури статті)
    og = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "twitter:image"})
    cands = []
    if figs is not None: cands = figs
    elif og and og.get("content"): cands.append((urljoin(url, og["content"]), "", ""))
    for im in ([] if figs is not None else main.find_all("img")):
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
    entries = fp.entries[:60]
    decoded = {}
    if kind == "gnews":
        fresh = [e for e in entries if (entry_date(e) or SINCE) >= SINCE and not SPAM.search(e.get("title", ""))]
        decoded = gnews_decode_many([e.get("link", "") for e in fresh])
        lost = sum(1 for v in decoded.values() if not v)
        if lost: log(f"{s.get('q')}: не декодовано {lost} з {len(decoded)} посилань")
    items = []
    for e in entries:
        d = entry_date(e)
        if not d or d < SINCE: continue
        title = e.get("title", "").strip(); link = e.get("link", "")
        src_name = s["name"]
        if kind == "gnews":
            if SPAM.search(title): continue
            src_name = (e.get("source") or {}).get("title") or "Google News"
            title = re.sub(r"\s+-\s+[^-]+$", "", title)  # прибрати " - Назва видання"
            link = decoded.get(link)
            if not link: continue
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
                          "videos": [{"yt": it["yt"]}]}
        elif it["kind"] == "reddit":
            it["page"] = extract_page(it["url"])
        else:
            it["page"] = extract_page(it["url"])
        return it
    with ThreadPoolExecutor(6) as ex:
        all_items = list(ex.map(enrich, all_items))
    # Google News ставить дату індексації, а не публікації: якщо сторінка каже, що стаття старіша, — віримо сторінці
    fresh = []
    for it in all_items:
        pd = it["page"].get("published")
        if it["kind"] == "gnews" and pd and pd < it["date"]:
            it["date"] = pd
            if pd < SINCE.isoformat():
                log(f"застаріле ({pd[:10]}): {it['title'][:60]}"); continue
        fresh.append(it)
    all_items = fresh
    # обʼєднати з попереднім raw.json, залишити 30 днів; при нульовому зборі нічого не затирати
    path = os.path.join(DATA, "raw.json")
    old = json.load(open(path)) if os.path.exists(path) else []
    if not all_items and old:
        log("Нічого не зібрано (мережа?), raw.json залишено без змін"); return
    merged = {r["id"]: r for r in old}
    for r in all_items: merged[r["id"]] = r
    cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    all_items = sorted([r for r in merged.values() if r["date"] >= cutoff], key=lambda x: x["date"], reverse=True)
    json.dump(all_items, open(path, "w"), ensure_ascii=False, indent=1)
    with_media = sum(1 for i in all_items if i["page"]["images"] or i["page"]["videos"])
    log(f"Збережено {len(all_items)} новин, з медіа: {with_media}")

if __name__ == "__main__":
    main()
