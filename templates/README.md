# Template format · صيغة القوالب

A template is a Shoof document: the same JSON that **Save** produces (`.shoof.json`), plus a few metadata fields. Files live in `templates/<category>/<name>.json` and are listed in `templates/index.json` (from v0.3). Categories: `social`, `poster`, `story`, `arabic`, `photo`.

## Generated template set (50 English templates)
Most built-in templates come from **`tools/templates/gen_templates.py`**: a style spec (12 palettes, 3 font pairs, 11 layout recipes such as `bold`, `center`, `photo`, `promo`, `quote`, `list`, `event`, `story`, `card`, `logo`, `slide`) plus a content table. The script writes the result into `index.html` between the `@generated-templates` markers; never edit that block by hand.

```bash
python3 tools/templates/gen_templates.py           # rebuild the block in index.html
python3 tools/templates/gen_templates.py --check   # CI: fail if index.html is stale
```
To add a template, add one row to the content table `T` (key, name, categories, keywords, size, recipe, palette, fonts, content). The QA test `generated_templates_quality` renders every template and fails on text off the page, overlapping text boxes or elements dropped by the validator. Topic categories: `promo`, `event`, `hiring`, `quote`, `tips`, `food`, `realestate`, `business`, `seasonal`.

## Example
```json
{
  "app": "shoof",
  "formatVersion": 1,
  "name": "Ramadan offer",
  "name_ar": "عرض رمضان",
  "lang": "ar",
  "tags": ["sale", "ramadan", "instagram"],
  "width": 1080,
  "height": 1080,
  "background": { "color": "#fff4e8", "image": null },
  "elements": [
    { "type": "ellipse", "x": -200, "y": 600, "width": 800, "height": 800, "fill": "#ff6a3d" },
    { "type": "text", "x": 100, "y": 130, "width": 880, "text": "عرض خاص",
      "fontFamily": "Cairo", "fontSize": 150, "bold": true, "fill": "#2a1407", "align": "right" },
    { "type": "rect", "x": 100, "y": 860, "width": 380, "height": 96, "radius": 48, "fill": "#ffffff" }
  ]
}
```

## Document fields
| Field | Type | Required | Notes |
|---|---|---|---|
| `app` | `"shoof"` | yes | Files without this are rejected |
| `formatVersion` | integer | yes | Currently `1` |
| `width`, `height` | integer px | yes | Use a standard size: 1080×1080, 1080×1920, 1200×627, 1200×630, 1600×900, 1280×720, A4 2480×3508, A3 3508×4961 |
| `background.color` | hex colour | yes | e.g. `#ffffff` |
| `background.image` | data URL or `null` | no | No remote URLs |
| `elements` | array | yes | Drawn bottom to top (first = back) |
| `name`, `name_ar` | string | template only | Title shown in the picker, EN and AR |
| `lang` | `en` \| `ar` \| `bilingual` | template only | Used for filtering |
| `tags` | string[] | template only | Lowercase English keywords |

## Element fields
Common to every element: `type`, `x`, `y`, `width`, `height` (px, page coordinates), plus the optional `rotation` (degrees), `opacity` (0–1), `locked`, `hidden` and `groupId` (elements sharing a safe id form a group; a group needs at least 2 members).
Shadow, on every type except `placeholder`: `shadowColor`, `shadowBlur` (0–500), `shadowX`, `shadowY`, `shadowOpacity` (0–1).
`id`, `version` and `versionNonce` are generated on load, so leave them out of templates.

| `type` | Extra fields |
|---|---|
| `text` | `text` (≤20 000 chars), `fontFamily`, `fontSize` (1–2000), `fill`, `bold`, `italic` (ignored for Arabic), `align` (`left`/`center`/`right`/`justify`), `lineHeight` (0.5–5, default 1.2), `letterSpacing` (forced to 0 when the text contains Arabic), `dir` (`ltr`/`rtl`; omit for automatic first-strong-character direction), outline `stroke`/`strokeWidth`, highlight box `bgColor`/`bgPad`/`bgRadius`. The height is computed automatically. |
| `rect` | `fill`, `stroke`, `strokeWidth`, `radius` (corner radius) |
| `ellipse`, `triangle`, `star`, `arrow`, `bubble`, `hexagon` | `fill`, `stroke`, `strokeWidth` |
| `line` | `fill` (line colour); `height` = thickness |
| `placeholder` | Photo frame the user clicks to fill: `fill` (frame colour), `radius` |
| `image` | `src` (**`data:image/png\|jpeg\|webp\|gif;base64` only**), `radius`, `flipX`, `flipY`, `fit` (`fill` cover-crop / `fit` letterbox), `cropZoom` (1–5), `cropX`/`cropY` (−1…1), `brightness` (−1…1), `contrast` (−100…100), `blur` (0–100), `grayscale` |

Colours must be hex (`#rgb`, `#rrggbb` or `#rrggbbaa`). Unknown keys, unknown types and invalid values are dropped when the file is loaded. A file is capped at 2000 elements and 50 MB, and page size is clamped to 16–10000 px.

## Rules
- Fonts: Inter, Poppins, Playfair Display, Bebas Neue (Latin) and Cairo, Tajawal, Amiri, IBM Plex Sans Arabic (Arabic). Any other name falls back to Inter.
- Arabic text: set `align: "right"` and use an Arabic font. Leave `dir` unset unless the text starts with a Latin word but should read right to left.
- Prefer a `placeholder` over an embedded stock photo.
- Keep each file under 300 KB, and use only images you own or that are CC0.
- Run `QA_ONLY=templates_load python tests/qa_suite.py` before opening a PR.

> v0.2: built-in templates are still defined in `index.html` (`TEMPLATES`). From v0.3 they will be loaded from `templates/index.json` in this format.
