# Contributing to Shoof · المساهمة في شوف

Thanks for helping. Shoof is a browser-only, single-file editor, so most contributions are small and easy to review.
شكرًا لمساهمتك! يمكنك المساهمة بالقوالب أو الترجمة أو إصلاح الأخطاء. التفاصيل أدناه بالإنجليزية، ويمكنك فتح Issue بالعربية.

## Ground rules
- Shoof must keep working **with no server, no account and no API keys**, from a plain static host or a local `index.html`.
- **No tracking, analytics or third-party calls** beyond the pinned libraries and fonts.
- Every UI change must work in **both English and Arabic (RTL)** and at **phone width (390 px)**.
- By contributing, you agree that your contribution is licensed under **AGPL-3.0**.
- Follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## Getting set up
```bash
git clone https://github.com/shahrosekhalid96-debug/shoof.git && cd shoof
npx serve .                      # http://localhost:3000 (or just open index.html)
pip install playwright pillow && python -m playwright install chromium
python tests/qa_suite.py         # full suite: 64 tests, about 2 minutes, runs from any directory
QA_ONLY=templates_load,export_all_presets_exact_px python tests/qa_suite.py   # run a subset
```

## 1. Adding a template
Templates are plain JSON documents. They use the same format as a design saved with **Save** (`.shoof.json`). See [templates/README.md](templates/README.md) for the full format.

1. Make your design in Shoof and click **Save**. Alternatively, write the JSON by hand.
2. Copy the file to `templates/<category>/<short-name>.json`, for example `templates/social/ar-ramadan-offer.json`.
3. Add `"name"` and `"name_ar"` (the title shown in the template picker in each language), `"lang"` (`en`, `ar` or `bilingual`) and `"tags"`.
4. Register the file in `templates/index.json`.
5. Rules:
   - Use only the bundled fonts: Inter, Poppins, Playfair Display, Bebas Neue (Latin) and Cairo, Tajawal, Amiri, IBM Plex Sans Arabic (Arabic).
   - For a photo, use a `placeholder` element (photo frame) that the user can click to fill.
   - **No remote image URLs.** Embed small images as `data:` URLs (under 300 KB per template) or leave image slots empty.
   - Only include images you own or that are CC0 or public domain. State the source in your PR.
   - Arabic text must be real, natural Arabic, not machine-translated filler.
   - Remove `id`, `version` and `versionNonce` from elements. The app regenerates them.
6. Run `QA_ONLY=templates_load python tests/qa_suite.py`, which checks that every template loads and renders.

> Note (v0.2): the 17 built-in templates still live in the `TEMPLATES` array in `index.html`, with `name`/`name_ar`, a category and keywords. Loading them from `templates/*.json` is planned for v0.3. Until then you can either send a JSON file (maintainers port it) or add an entry to `TEMPLATES` directly.

## 2. Translations
- All UI strings are in the `I18N` object at the top of the `<script>` in `index.html`, with one key per string: `I18N.en.key` and `I18N.ar.key`.
- **Every key must exist in every language.** The test suite fails if a key is missing.
- Keep strings short (buttons are small on phones). Use Arabic punctuation (، ؛ ؟) in Arabic.
- Adding a language: add `I18N.<code>`, set its `dir` (`rtl` for ur/fa/he), add it to the language switcher and include screenshots in your PR.

## 3. Code style
- Shoof is a **single file, `index.html`**: vanilla JS (ES2020, `'use strict'`) with no framework and no build step. Please don't add a bundler or framework without discussing it in an issue first.
- 1-space indentation, terse helpers (`$`, `t()`, `el()`), and functions grouped under `/* ==== section ==== */` banners. Follow the surrounding code.
- **Escape all user text** with `esc()` before it goes into `innerHTML`. Never pass file contents to `eval` or to `innerHTML`.
- Every document change goes through `commit()` so that undo and autosave keep working.
- New document fields need a `migrate()` step. Bump `formatVersion` if the change isn't backward compatible.
- **No network calls.** Libraries live in `vendor/` and fonts in `fonts/`, pinned to exact versions. To update one, replace the file, note the version in About and the README, and run the full suite. The suite fails if the page requests anything outside the app folder.
- New fonts must be OFL (or similarly permissive) and subset to woff2 (Latin and/or Arabic), with an `@font-face` rule in `fonts/fonts.css` and the licence saved as `fonts/<family>-OFL.txt`.
- Anything Ask Claude can do must go through the same `sanitizeEl`/`safeColor` validators as file import, and a whole action must stay one undo step.

## 4. Tests
- `tests/qa_suite.py` drives Chrome (or Playwright's Chromium) at 1440 × 900 and 390 × 844, in English and Arabic. It covers every tool, exact-pixel export for every preset, undo/redo, save/open, malicious files, Ask Claude (with a mock), offline and failure behaviour, **zero console errors** and **zero external requests**.
- Environment variables: `QA_ONLY` (comma-separated test names), `QA_APP` (path to another index.html), `RASM_BROWSER` (path to a Chrome binary; otherwise auto-detected).
- CI runs the same suite on every PR (`.github/workflows/test.yml`). **A PR must be green before it is merged.**
- Add a test for every bug you fix: an `@test('name')` function in `tests/qa_suite.py`.

## 5. Pull requests
- Keep PRs to one topic and link the issue. Include **before and after screenshots in EN and AR** for UI changes.
- Use Conventional Commit titles: `feat:`, `fix:`, `i18n:`, `template:`, `docs:`, `test:`, `chore:`.
- Maintainers squash-merge, and the PR title becomes the changelog line.
