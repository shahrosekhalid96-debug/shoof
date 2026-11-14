<div align="center">

# Shoof · شوف

**A free, open-source design editor for social posts and posters — in English and Arabic.**
**محرر تصاميم مجاني ومفتوح المصدر للمنشورات والملصقات — بالعربية والإنجليزية.**

[Live demo](https://shoof.pages.dev/) · [About Shoof](https://shoof.pages.dev/welcome.html) · [Report a bug](../../issues/new?template=bug_report.md) · [Request a feature](../../issues/new?template=feature_request.md) · [Contributing](CONTRIBUTING.md) · [العربية](#العربية)

`AGPL-3.0` · no account · no watermark · no tracking · works offline · runs entirely in your browser

</div>

---

## English

### What is Shoof?
Shoof (شوف, "look!") is a Canva-style editor that runs entirely in your browser. Open it, pick a template, edit it and download a PNG, JPG or PDF. You don't need an account, there's no watermark, there are no paid templates and nothing is uploaded. **The page makes no network requests at all**, because libraries and fonts ship with it, so your designs never leave your device.

Arabic is fully supported, not added as an afterthought. The interface switches to a mirrored right-to-left layout, Arabic text renders and edits correctly (text direction follows the first strong character), and the template library includes Arabic, English and bilingual designs.

### Features (v0.2)
- **Welcome home screen**: big template search, "start with a size" tiles (Instagram post, Story, Poster, Flyer, Logo, Business card, Presentation), Trending and Picks rows, and a "Continue your design" card
- **122 templates** including 4 multi-slide pitch decks and 6 editorial posters (105 built by a generator script, plus 17 originals incl. Arabic and bilingual), filterable by format (Social, Posters, Stories, With photo) and topic (Sale & promo, Events, Hiring, Quotes, Tips, Food, Real estate, Business, Seasonal, Arabic) and searchable in EN and AR. Sizes cover Instagram, Stories/Reels, LinkedIn, Facebook, X and YouTube thumbnails, plus A4 and A3 posters.
- **New-design dialog** with 12 size presets or a custom size (16–10000 px)
- **Text**: 42 bundled open-licence fonts in groups (sans, serif, display, handwriting, monospace, Arabic) with a live preview list, 22 ready-made **text styles**, a change-case button, plus size, colour, alignment, line height and letter spacing (automatically 0 for Arabic)
- **Text effects**: shadow, outline and highlight box
- **Elements panel** (searchable): shapes (incl. blob and slanted box), device mockups with photo slots (phone, tablet, laptop, browser, polaroid), 11 subtle code-drawn patterns (halftone dots, wave lines, contour rings, stripes, pixel dither), infographic blocks (step buttons, mind map, timeline, process, stats, percentage ring), line styles (dashed, dotted, arrows), photo frames with circle/blob/arch/hexagon/heart/diamond masks, 9 stickers, bar/line/pie/donut charts with editable data, and 209 Lucide icons (recolour, line weight, fill)
- **Multi-page designs**: a pages bar to add, duplicate, reorder and delete pages (great for decks and carousels)
- **Export**: PNG (also with no background, or double size), JPG, WebP, PDF (all pages), **SVG** (shapes, icons and text stay editable vectors) and **PowerPoint .pptx** with editable text
- **122 original templates and 35 mockups** (three-phone fan, laptop with phone, TV, story frame, video thumbnail, chat bubbles, review card, tote bag, mug, shopping bag, ID card, shop sign, magazine cover, gallery wall and more): phones, laptop, monitor, browser, watch, billboard, framed poster, business cards and photo grids, all built from editable shapes with photo slots; new template families for app and website launches, price lists, certificates, name badges, photo grids and big-number posts
- **Landing page**: `welcome.html`, a short, light introduction to share with new people
- **Logo maker (free)**: type a name, tagline and what you do, pick a style, and choose from 24 logo ideas at a time; each one opens as a normal editable design, or saves straight into your brand kit
- **Bulk create (free)**: paste rows from Excel or Google Sheets, drop `{Column}` tags into a design, and get one page per row or a zip of PNGs (name cards, price tags, certificates, one post per product)
- **Background remover (free, private)**: a small AI model runs in your browser, so photos never leave your device
- **Text effects and curved text**: one-click soft shadow, retro, hollow, neon, sticker and marker looks; bend any line into an arc
- **Brand kit (free)**: save your colours, heading and body fonts and logo on your device, then apply the brand to any design in one click (text stays readable, one undo step)
- **Smart resize (free)**: change format and the layout adapts (full-width blocks stretch, items keep their edges, labels stay on their cards); **Download → PNG · 4 social sizes** exports Instagram, Story, LinkedIn and X versions at once
- **Gradients**: linear and radial gradient fills for shapes, text and the page background, with 12 presets, two-colour editor, angle and swap
- **Shapes**: rectangle, ellipse, triangle, star, line, arrow, speech bubble and hexagon, with fill, border, corners and shadow
- **Images**: drag and drop, paste or upload (large images are downscaled to 2400 px), photo frames (placeholders), replace image, flip, crop (fill or fit), and brightness, contrast, blur and black & white filters
- **Multi-select and groups**: Shift-click, drag a box or Ctrl+A to select; Ctrl+G / Ctrl+Shift+G to group and ungroup; align to page or to the selection
- **Layers**: reorder, lock, hide and duplicate; snapping guides
- **Undo / redo**, and **autosave** in your browser (you're warned if storage is full or blocked)
- **Save / Open** a design as a `.shoof.json` file (validated on open; unsafe content is dropped)
- **Export** as PNG, JPG or PDF at exact full resolution (A3 is 3508 × 4961 px, in under a second on a laptop)
- **Bilingual UI** (English / عربي) with RTL mirroring; works on phones (390 px and narrower) with a bottom-sheet properties panel
- **Ask Claude** when opened inside Claude (see below)

### Live demo
`https://shahrosekhalid96-debug.github.io/shoof/`

### Run it locally
There's no build step and no internet needed.

```bash
git clone https://github.com/shahrosekhalid96-debug/shoof.git
cd shoof
# Option 1: just open the file (double-click index.html, or:)
open index.html            # macOS  (Linux: xdg-open index.html, Windows: start index.html)
# Option 2: serve the folder (recommended; it matches GitHub Pages)
npx serve .                # then visit http://localhost:3000
```

### Project layout
```
index.html            the whole app (HTML + CSS + JS, single file)
vendor/               Konva 10.9.1 (MIT) and jsPDF 4.2.1 (MIT, loaded only on the first PDF export)
fonts/                fonts.css + self-hosted woff2 (Latin and Arabic subsets) + each font's OFL licence
templates/            template format docs (template JSON files from v0.3)
tests/qa_suite.py     Playwright end-to-end suite (desktop and phone, EN and AR)
.github/              issue templates, Pages deploy and CI workflows
LICENSE               GNU AGPL-3.0
```

### "Ask Claude" (works only inside Claude)
When Shoof is opened as an artifact inside [Claude](https://claude.ai), an **Ask Claude / اسأل Claude** tab appears. It runs on the **viewer's own Claude account** through the artifact's `sample` capability, so there are no API keys and nothing for you to pay for or configure.
- **Quick actions:** write a post, translate EN ↔ AR, rewrite text, caption + hashtags (with a Copy button), make it bilingual, restyle, fix layout. You can also type your own request.
- Claude edits the design only through a small set of validated page tools: read the design; add, update or delete elements; set the background; group and ungroup; apply effects. Every change goes through the same safety checks as opening a file.
- **A whole Claude action is a single undo step**, and there's an "Undo Claude's changes" button. **Stop** cancels the request at any time.
- Claude is called only when you click. Nothing is sent in the background.

On GitHub Pages or any other host this capability doesn't exist, so the tab is **hidden** and everything else works as normal.
*Publishers:* when you publish Shoof as a Claude artifact, declare the `sample` capability, or the tab stays hidden.

### Roadmap
| Version | Focus |
|---|---|
| v0.1 | Prototype: single-file editor, templates, export |
| **v0.2** | **Public preview:** offline (bundled libraries and fonts), safe file import, mobile layout, full EN/AR UI, multi-select and groups, image tools, effects, 17 templates, Ask Claude, CI suite |
| v0.3 | PWA (installable, cached offline), templates loaded from `templates/*.json`, CSP |
| v0.4 | Community templates, icon library, distribute spacing, rounded lines |
| v0.5 | Delta-based undo, ZIP file format with embedded images and migrations |
| v1.0 | Stable file format, WCAG AA audit, full EN/AR parity sign-off, documented template API |
| Later | Multi-page designs, more languages (Urdu, Persian, French), brand kits, SVG export |

### Licence
Shoof is free software under the **GNU Affero General Public License v3.0**. See [LICENSE](LICENSE). The **About** panel shows a source-code link, as AGPL §13 requires.
Third-party: [Konva](https://konvajs.org) (MIT) and [jsPDF](https://github.com/parallax/jsPDF) (MIT); their notices are in the file headers in `vendor/`. Fonts use the SIL Open Font License 1.1 (`fonts/*-OFL.txt`).
Designs you make with Shoof belong to you. The AGPL covers the editor's code, not your artwork.

---

<div dir="rtl" lang="ar">

## العربية

### ما هو شوف؟
شوف محرر تصاميم يشبه Canva ويعمل بالكامل داخل متصفحك. افتحه، واختر قالبًا، وعدّله، ثم نزّل التصميم بصيغة PNG أو JPG أو PDF. لا يحتاج إلى حساب، ولا يضع علامة مائية، ولا توجد فيه قوالب مدفوعة. **الصفحة لا تتصل بالإنترنت إطلاقًا** لأن المكتبات والخطوط مضمّنة فيها، لذلك تبقى تصاميمك على جهازك.

العربية مدعومة دعمًا كاملًا من البداية: تنقلب الواجهة من اليمين إلى اليسار، ويُكتب النص العربي ويُعرض بشكل صحيح، وتضم مكتبة القوالب تصاميم عربية وإنجليزية وثنائية اللغة.

### المزايا
- **١٧ قالبًا** مع تصنيفات (منشورات، ملصقات، قصص، عربي، مع صورة) وبحث بالعربية والإنجليزية
- **تصميم جديد** بثمانية مقاسات جاهزة أو بمقاس مخصّص
- **نصوص** بثمانية خطوط مضمّنة: أربعة عربية (Cairo وTajawal وAmiri وIBM Plex Sans Arabic) وأربعة لاتينية، مع ظل وحدّ خارجي وخلفية للنص
- **أشكال**: مستطيل وشكل بيضاوي ومثلث ونجمة وخط وسهم وفقاعة كلام وشكل سداسي
- **صور**: إطارات للصور، واستبدال الصورة، وقلب وقص، وفلاتر للسطوع والتباين والتمويه والأبيض والأسود
- **تحديد متعدد وتجميع العناصر**، و**طبقات** يمكن ترتيبها وقفلها وإخفاؤها
- **تراجع وإعادة**، مع **حفظ تلقائي** وتنبيه إذا امتلأت مساحة التخزين في المتصفح
- **حفظ وفتح** التصميم كملف `.shoof.json`، و**تنزيل** بصيغة PNG أو JPG أو PDF بالدقة الكاملة
- **واجهة ثنائية اللغة** تعمل على الجوال أيضًا

### العرض المباشر
`https://shahrosekhalid96-debug.github.io/shoof/`

### التشغيل على جهازك
لا يحتاج شوف إلى أي بناء أو إلى اتصال بالإنترنت: افتح `index.html` مباشرة في المتصفح، أو شغّل الأمر `npx serve .` ثم افتح `http://localhost:3000`.

### «اسأل Claude» (يعمل داخل Claude فقط)
عند فتح شوف داخل [Claude](https://claude.ai) يظهر تبويب **اسأل Claude**، ويعمل على **حساب Claude الخاص بالمستخدم** بدون مفاتيح API وبدون تكلفة إضافية. يمكنه كتابة منشور، والترجمة بين العربية والإنجليزية، وإعادة صياغة النص، واقتراح وصف ووسوم، وتحويل التصميم إلى ثنائي اللغة. كل ما يفعله Claude في الطلب الواحد يمكن التراجع عنه بخطوة واحدة، ويمكنك إيقافه في أي وقت. وخارج Claude يكون التبويب مخفيًا، وتعمل بقية المزايا كالمعتاد.

### خارطة الطريق
0.1 نموذج أولي ← **0.2 إصدار تجريبي عام** ← 0.3 تطبيق ويب قابل للتثبيت (PWA) وقوالب بصيغة JSON ← 0.4 قوالب من المجتمع ← 0.5 صيغة ملفات جديدة ← **1.0 إصدار مستقر**.

### الرخصة
برنامج حر بموجب رخصة **GNU AGPL الإصدار 3.0**. تبقى ملكية التصاميم التي تصنعها لك، فالرخصة تشمل كود المحرر فقط ولا تشمل أعمالك.

</div>
