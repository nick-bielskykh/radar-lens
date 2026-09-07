"""Джерела для збору. kind: rss | youtube (channel url) | reddit.
filter=True означає, що стрічка загальна і потрібно фільтрувати за ключовими словами."""

SOURCES = [
    # Галузеві медіа
    {"name": "PetaPixel", "url": "https://petapixel.com/feed/", "cat_hint": "market", "filter": True},
    {"name": "Fstoppers", "url": "https://fstoppers.com/rss", "cat_hint": "market", "filter": True},
    # Конкуренти
    # Google News: пошукові стрічки по продуктах (лінки декодуються в оригінал)
    {"name": "Google News", "q": "Adobe Lightroom", "kind": "gnews", "cat_hint": "comp"},
    {"name": "Google News", "q": "Adobe Photoshop AI", "kind": "gnews", "cat_hint": "comp"},
    {"name": "Google News", "q": "Adobe Firefly image", "kind": "gnews", "cat_hint": "comp"},
    {"name": "Google News", "q": "Topaz Photo OR \"Topaz Labs\"", "kind": "gnews", "cat_hint": "comp"},
    {"name": "Google News", "q": "\"Capture One\"", "kind": "gnews", "cat_hint": "comp"},
    {"name": "Google News", "q": "DxO PhotoLab OR PureRAW", "kind": "gnews", "cat_hint": "comp"},
    {"name": "Google News", "q": "\"Luminar Neo\" OR Skylum", "kind": "gnews", "cat_hint": "comp"},
    {"name": "Google News", "q": "Snapseed OR \"Lightroom Mobile\" OR \"Google Photos\" editing AI", "kind": "gnews", "cat_hint": "comp"},
    {"name": "Google News", "q": "Photoroom OR Picsart OR Evoto OR \"Imagen AI\" photo", "kind": "gnews", "cat_hint": "comp"},
    {"name": "Google News", "q": "\"AI photo editing\" OR \"AI image editing\" model", "kind": "gnews", "cat_hint": "ai"},
    {"name": "Google News", "q": "FLUX Kontext OR \"Nano Banana\" OR \"Stable Diffusion\" image editing", "kind": "gnews", "cat_hint": "ai"},
    {"name": "Google News", "q": "\"Apple Photos\" OR \"Apple Intelligence\" \"Clean Up\" OR photo editing iOS", "kind": "gnews", "cat_hint": "comp"},
    {"name": "Google News", "q": "Samsung \"Galaxy AI\" photo OR \"Generative Edit\" OR \"Photo Assist\"", "kind": "gnews", "cat_hint": "comp"},
    {"name": "Google News", "q": "Lensa OR Remini OR Meitu OR \"Photo AI\" OR Facetune app update", "kind": "gnews", "cat_hint": "comp"},
    {"name": "Google News", "q": "Pixelmator OR Photomator OR \"Affinity Photo\" OR Canva photo OR VSCO update", "kind": "gnews", "cat_hint": "comp"},
    {"name": "Google News", "q": "\"Black Forest Labs\" OR \"Stability AI\" OR \"Meta AI\" OR \"Qwen-Image\" OR Seedream image model", "kind": "gnews", "cat_hint": "ai"},
    {"name": "ON1", "url": "https://www.on1.com/blog/feed/", "cat_hint": "comp"},
    {"name": "Digital Camera World", "url": "https://www.digitalcameraworld.com/feeds/all", "cat_hint": "market", "filter": True},
    {"name": "Lightroom Queen", "url": "https://www.lightroomqueen.com/feed/", "cat_hint": "comp", "filter": True},
    {"name": "Picsart Blog", "url": "https://picsart.com/blog/feed/", "cat_hint": "comp", "filter": True},
    {"name": "Apple Newsroom", "url": "https://www.apple.com/newsroom/rss-feed.rss", "cat_hint": "comp", "filter": True},
    {"name": "Product Hunt · Photo editing", "url": "https://www.producthunt.com/feed?category=photo-editing", "cat_hint": "market"},
    # YouTube канали (RSS резолвиться зі сторінки каналу)
    {"name": "Topaz Labs · YouTube", "url": "https://www.youtube.com/@TopazLabs", "kind": "youtube", "cat_hint": "comp"},
    {"name": "Adobe Lightroom · YouTube", "url": "https://www.youtube.com/@Lightroom", "kind": "youtube", "cat_hint": "comp"},
    {"name": "Capture One · YouTube", "url": "https://www.youtube.com/@captureone", "kind": "youtube", "cat_hint": "comp"},
    {"name": "DxO · YouTube", "url": "https://www.youtube.com/@DxOLabs", "kind": "youtube", "cat_hint": "comp"},
    {"name": "Adobe Photoshop · YouTube", "url": "https://www.youtube.com/@Photoshop", "kind": "youtube", "cat_hint": "comp"},
    # ІІ та дослідження
    {"name": "Hugging Face Blog", "url": "https://huggingface.co/blog/feed.xml", "cat_hint": "ai", "filter": True},
    {"name": "Google Research", "url": "https://research.google/blog/rss/", "cat_hint": "algo", "filter": True},
    {"name": "Google AI Blog", "url": "https://blog.google/technology/ai/rss/", "cat_hint": "ai", "filter": True, "strict": True},
    {"name": "Google DeepMind", "url": "https://deepmind.google/blog/rss.xml", "cat_hint": "ai", "filter": True, "strict": True},
    {"name": "fal.ai Blog", "url": "https://blog.fal.ai/rss/", "cat_hint": "ai", "filter": True},
    {"name": "Replicate Blog", "url": "https://replicate.com/blog/rss", "cat_hint": "ai", "filter": True},
    {"name": "arXiv eess.IV", "url": "https://rss.arxiv.org/rss/eess.IV", "cat_hint": "algo", "filter": True, "strict": True},
    {"name": "arXiv cs.CV", "url": "https://rss.arxiv.org/rss/cs.CV", "cat_hint": "ai", "filter": True, "strict": True},
    {"name": "NVIDIA Research", "url": "https://blogs.nvidia.com/feed/", "cat_hint": "ai", "filter": True, "strict": True},
    # Tech-медіа (загальні, тільки з фільтром)
    {"name": "The Verge", "url": "https://www.theverge.com/rss/index.xml", "cat_hint": "market", "filter": True},
    {"name": "9to5Mac", "url": "https://9to5mac.com/feed/", "cat_hint": "comp", "filter": True},
    {"name": "Android Authority", "url": "https://www.androidauthority.com/feed/", "cat_hint": "comp", "filter": True},
    # Спільнота
    {"name": "Reddit r/photography", "url": "https://www.reddit.com/r/photography/top/.rss?t=week", "kind": "reddit", "cat_hint": "market", "filter": True},
    {"name": "Reddit r/Lightroom", "url": "https://www.reddit.com/r/Lightroom/top/.rss?t=week", "kind": "reddit", "cat_hint": "comp"},
    {"name": "Reddit r/postprocessing", "url": "https://www.reddit.com/r/postprocessing/top/.rss?t=week", "kind": "reddit", "cat_hint": "market", "filter": True},
    {"name": "Reddit r/StableDiffusion", "url": "https://www.reddit.com/r/StableDiffusion/top/.rss?t=week", "kind": "reddit", "cat_hint": "ai", "filter": True, "strict": True},
]

# Слова, за якими фільтруються загальні стрічки (нижній регістр)
KEYWORDS = [
    "lightroom", "photoshop", "firefly", "capture one", "topaz", "dxo", "on1", "affinity", "luminar", "skylum",
    "pixelmator", "photoroom", "canva", "snapseed", "picsart", "vsco", "darktable", "rawtherapee", "evoto", "retouch",
    "photo edit", "photo-edit", "image edit", "image-edit", "inpaint", "generative fill", "generative remove",
    "denoise", "denois", "noise reduction", "upscal", "super-resolution", "super resolution", "relight", "relighting",
    "sky replacement", "masking", "mask", "portrait", "bokeh", "depth estimation", "depth map", "hdr", "raw ",
    "demosaic", "colour grading", "color grading", "lut", "diffusion", "flux", "stable diffusion", "image generation",
    "text-to-image", "image restoration", "face restoration", "deblur", "harmonization", "object removal",
    "photos app", "apple photos", "clean up tool", "galaxy ai", "generative edit", "photo assist", "magic editor", "magic eraser",
    "lensa", "remini", "meitu", "facetune", "photomator", "nano banana", "kontext", "qwen-image", "seedream", "gpt-image",
    "image model", "photo editing", "photo editor", "image editor",
]
# Для strict-стрічок (arXiv, NVIDIA, SD) потрібно, щоб збіглося саме з цих слів
STRICT_KEYWORDS = [
    "image edit", "image-edit", "photo edit", "inpaint", "denois", "super-resolution", "super resolution", "relight",
    "image restoration", "face restoration", "deblur", "harmonization", "object removal", "portrait retouch",
    "depth estimation", "colorization", "color grading", "low-light", "raw image", "demosaic", "hdr", "tone mapping",
    "matting", "image enhancement", "photo enhancement", "sky replacement", "lightroom", "photoshop", "flux", "kontext",
    "nano banana", "image editing", "image generation model", "text-to-image", "qwen-image", "seedream", "gpt-image", "imagen",
]
