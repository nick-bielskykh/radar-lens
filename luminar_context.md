# Контекст про продукти Skylum (іде в промпт редактора; оновлюється з support.skylum.com і Notion «Документація фіч»)

_Оновлено: 2026-09-08. Джерела: support.skylum.com (llms.txt), Notion → Product Team → Luminar Neo → Документація фіч._

## Luminar Neo — десктоп (macOS, Windows; standalone, плагін для Lightroom Classic і Photoshop, розширення Photos для macOS)
Точні назви інструментів (використовуй саме їх):
- **Essential:** Develop RAW / Develop, Enhance AI, Erase, Structure AI, Color, Black & White, Details, Denoise, Vignette. Власний RAW-двигун.
- **Image Quality (платні pro-тули, ex-Extensions):** Noiseless AI, Supersharp AI (сітки Universal / Motion / Defocus, чекбокс Enhance Face), Upscale AI, Focus Stacking, HDR Merge, Panorama Stitching, Background Removal AI, Magic Light AI.
- **Generative (хмарні, лімітовані):** GenErase, GenSwap, GenExpand, Restoration (відновлення старих фото: Full / Color). Крок обробки ≈ 30 центів, лічильник на рік, єдиний пул на всі генеративні фічі.
- **Landscape:** Sky AI, Sunrays, Twilight Enhancer AI, Atmosphere AI, Landscape, Water Enhancer AI.
- **Creative:** Light Depth (світло по карті глибини, зараз тільки вісь Y), Color Transfer, Magic Light AI, Dramatic, Mood (LUT), Toning, Matte, Neon & Glow, Mystical, Glow, Blur, Film Grain.
- **Portrait:** Studio Light, Bokeh AI (з 1.27.1 працює на будь-якому фото, Focus Distance; старий інструмент перейменовано на Portrait Bokeh), Face AI, Skin AI, Body AI, High Key.
- **Professional:** Supercontrast, Color Harmony, Dodge & Burn, Clone.
- **Masking:** Brush, Linear/Radial Gradient, Mask AI (класи: Human, Sky, Flora, Architecture, Water, Mountains, Transport, Natural Ground, Man Made Ground), Object Select AI, Luminosity, Color; Layers.
- **Каталог і воркфлоу:** Catalog, Spaces (веб-галереї), Smart Search, Crop AI Tool, AI Assistant (текстовий запит → правки або підказка, які інструменти; Cmd/Ctrl+K), Presets (2 900+), LUT, Overlays, Cross-Device Editing (синк із Mobile через Skylum account), Lightroom Classic Catalog Migration.
Монетизація: підписка Luminar for Desktop (усе включно з pro-тулами і генеративкою), довічна ліцензія + add-on **Luminar Prime** (річна, дає апгрейди, генеративку, Spaces, Creative Library). X Membership більше не продається. Плани нової моделі (1.28+): Neo / Cross / Max із лімітами на генеративку; паси стають річними.

## Luminar Mobile — iOS, iPadOS, Android (підписка + lifetime IAP; MAU ≈ 275K)
Інструменти: Enhance AI, Structure AI, Light Depth, Details, Crop, Filters (one-tap looks + Amount), Presets, Sky Replacement (авто-маска неба, Lighting Match, Reflections, Adjust: Brightness / Warmth / Defocus), Erase (content-aware, брашем), Copy & Paste adjustments, Cross-Device Editing на десктоп. Обробка частково на пристрої, частково у хмарі. Немає: генеративних інструментів, масок, шарів, RAW-редактора рівня десктопа.

## Що в роботі (роадмап Neo; не публічно — використовуй для оцінки, чи новина конкурента б'є по наших планах)
- **1.28.1 (16.09.2026):** Gamification Checklist.
- **1.29.0 — Autumn Release (28.10.2026, «Fall Upgrade 2026»):** Crop 2.0 / Composition AI (Smart Compositions: Rule of Thirds, Golden Ratio, Golden Spiral, Golden Triangle, Center; auto-straighten), Atmosphere 2.0 (туман за картою глибини, колір із фото, пресети Drizzle / Low Fog / High Fog), AI Assistant 2.0 (правки за текстом, діагностика кадру, три варіанти на творчий запит), Enhance AI 2.0, Masking Improvements (дерево масок Master / Nested, Add / Subtract / Intersect, незапечені параметричні маски, copy-paste між тулами й фото, нова модель сегментації з кращими краями і класами коти/собаки/авто), Presets Improvements, Export Redesign, Printing.
- **Winter release:** нові Noiseless AI і Supersharp AI (поточні версії — головне джерело рефандів: розмиття текстур, артефакти, спотворення облич, програш DxO / Topaz / Lightroom), Studio Light.
- **Further / backlog:** Selective Erase (авто-детект дістракшенів по категоріях — дроти, стовпи, люди на фоні, dust spots — з review-панеллю; відповідь на Photoshop «Find distractions» і Clean Up в iOS), Generative Erase всередині Erase (чекбокс Use Generative AI, єдиний флоу), Bokeh AI 2.5, Light Depth 2.0 (рух світла по X і Y), Halo, Luminar DAM, Culling AI, Lazy Downloads, App Startup Performance, підтримка Generative Erase з мобілки на десктопі.

## Аудиторія і позиціонування
Ентузіасти та напівпрофесіонали, які хочуть швидкий результат без складного навчання; багато хто тримає Luminar другим редактором поруч із Lightroom. Сильні сторони за фідбеком: Sky AI, Erase дрібних дефектів (dust spots), Relight/Light Depth, простота. Слабкі: денойз і шарп проти DxO/Topaz, швидкість AI-тулів, мобільна версія бідніша за десктоп, Android слабший за iOS.

## Що для нас найважливіше стежити
- Adobe (Lightroom, Lightroom Mobile, Photoshop, Camera Raw, Firefly) і Google (Pixel, Google Photos, Snapseed, Nano Banana) — tier-1. Apple Photos (Clean Up, iOS 27 AI-інструменти) і Samsung Galaxy AI — тиск на Mobile.
- Capture One, Topaz, DxO, ON1, Affinity, Pixelmator/Photomator, Evoto, Photoroom, Picsart, Canva — tier-2.
- Відкриті моделі та API для інпейнту, релайту, денойзу, глибини, апскейлу, портретної ретуші, детекту дістракшенів, композиції — які можна інтегрувати (наша генеративка на єдиній хмарній моделі, вартість запиту критична).
- On-device обробка на Apple Silicon / Core ML / Android NNAPI / Vulkan — критично для Mobile і для швидкості десктопних AI-тулів.
- Ціни, ліміти генерацій, кредитні моделі конкурентів — ми самі переходимо на ліміти.

## Як писати «Що це означає для Luminar»
Називай конкретний наш інструмент і, якщо є, пункт роадмапу, який новина підтверджує, обганяє або знецінює. Не вигадуй фіч, яких нема в списках вище. Якщо новина про денойз/шарп — згадуй, що це наша зона рефандів і зимовий реліз. Якщо про клінап/дістракшени — Selective Erase і Generative Erase в Erase. Якщо про маски — Masking Improvements 1.29. Якщо про мобільне редагування від Apple/Google/Samsung — Luminar Mobile і його обмежений набір.
