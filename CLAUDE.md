# Shoof — project brief for Claude (read this first)

Shoof (شوف, "look!") is a free, open-source (AGPL-3.0), browser-only Canva alternative for social posts and posters. Owner: Shary (GitHub `shahrosekhalid96-debug`). Formerly named "Rasm".

- **Live site:** https://shahrosekhalid96-debug.github.io/shoof/ (GitHub Pages, auto-deploys on every push to `main`)
- **Repo:** https://github.com/shahrosekhalid96-debug/shoof
- **Claude artifact copy** (only place Ask Claude works): https://claude.ai/artifact/SC37XwK2xKrF4yu41YQpoK — slug `cbfef32e-d2be-48eb-beba-49773200fd62`, capabilities `downloads` + `sample` declared. Republish with `publish_files` (index.html; vendor/ and fonts/ already uploaded).
- **Status:** v0.2 public preview. CEO review gave GO. 71/71 tests green locally and on GitHub Actions. Sprint 3 (2026-11-08): home screen + gradients shipped.

## Working rules (from Shary)
- Be direct and execution-focused, minimal back-and-forth, brief explanations. Outputs must be deployable.
- **English only for new work.** Keep the existing Arabic UI/templates working, but add no new Arabic strings, templates or Arabic reviews. New I18N keys go in `en` only (Arabic falls back to English).
- **Lean process (keeps usage low):** Claude builds directly — no multi-agent teams per sprint. Quality comes from the automated test suite + Claude screenshotting every UI change. Use ONE fresh independent reviewer agent only before a public release (combined design/QA/CEO judgment, report ≤150 words + findings table). Never run several agents in parallel (it hit the 5-hour usage limit).
- Commit trailer: `Co-Authored-By: Claude <noreply@anthropic.com>`. Commit as `Shoof contributors <shahrosekhalid96-debug@users.noreply.github.com>`.

## Files
| Path | What |
|---|---|
| `index.html` | The whole app (~1300 lines): HTML + CSS + JS, single file |
| `vendor/konva.min.js` | Konva 10.9.1 (MIT) canvas engine, loaded locally |
| `vendor/jspdf.umd.min.js` | jsPDF 4.2.1 (MIT), lazy-loaded on first PDF export |
| `fonts/` | woff2 + `fonts.css` + OFL licences: Inter, Poppins, Playfair Display, Bebas Neue, Cairo, Tajawal, Amiri, IBM Plex Sans Arabic |
| `tests/qa_suite.py` | Playwright suite, 71 tests (`Ctx(home=True)` keeps the welcome screen; default hides it), desktop 1440 + phone 390, blocks all external requests |
| `tests/security/*.json` | Malicious design files used by tests |
| `.github/workflows/pages.yml` | Deploys site (copies index.html, LICENSE, vendor, fonts) |
| `.github/workflows/test.yml` | Runs the QA suite on push |
| `README.md`, `CONTRIBUTING.md`, `templates/README.md`, `CODE_OF_CONDUCT.md`, `LICENSE` | Repo docs |

## Code map (index.html)
- `I18N` (~l.237) — `en` / `ar` string tables; `t(key)` falls back to English.
- `safeGrad()` / `gradAttrs()` / `gradCSS()` — gradient model `fillGradient` (shapes, text) and `background.gradient`: `{type:'linear'|'radial', angle, stops:[{offset,color}] (2–5)}`. UI: `gradUI()` + `bindGrad()` (props prefix `p`, Background tab prefix `b`), `GRAD_PRESETS` / `presetGrad()`.
- Home screen: `renderHome()`, `showHome()` / `hideHome()` / `homeOpen()`, `HOME_TILES` (size tiles → `newFromTile`), `HOME_TRENDING` / `HOME_PICKS`. Shown on every boot; `#homeBtn` (phone: ⋯ menu → Home). Keyboard/paste ignored while open.
- `LIM` (~l.359) and `sanitizeDoc()` (~l.402) — strict validator for every file open, autosave restore and Ask Claude tool input. All new element properties MUST be allow-listed here (security: XSS, remote URLs, sizes). Images must be `data:image/`.
- `SIZES`, `FONTS` (~l.420); `TEMPLATES` with helper `T()` (~l.651), 17 templates, categories + search.
- History: `commit()` / `undo()` / `redo()` (~l.434) — snapshot JSON; every user action = one undo step.
- Rendering: `buildNode()` (element → Konva group), `fullRender()`.
- Panels: `renderDrawer()` (left: templates/text/shapes/uploads/background/layers/Ask Claude/about), `renderProps()` (right/bottom sheet).
- Export: `exportAs()` (PNG/JPG/PDF at exact design pixels), `saveFile()` (artifact `downloads` capability, else `<a download>`).
- Ask Claude: `buildPrompt()` (~l.1097) + page tools via `claude.use('sample')`; hidden when unavailable. Design text is wrapped as untrusted data.
- `boot()` (~l.1159): language auto-detect, autosave restore (keys `shoof.autosave`, `shoof.lang`; migrates old `rasm.*`), file format `app:"shoof"` (still opens old `app:"rasm"`).
- Features present: templates, text (fonts, effects: shadow/outline/highlight), shapes (rect, ellipse, triangle, star, line, arrow, speech bubble, hexagon, photo placeholder), images (upload/paste/drop, downscale, replace, flip, crop fit/fill, filters), background colour/image, layers, multi-select, group/ungroup, align, lock/hide, snapping, undo/redo, autosave, save/open `.shoof.json`, PNG/JPG/PDF, mobile bottom sheet + "⋯" menu.

## Test & deploy
```bash
python3 tests/qa_suite.py                 # full suite (~2 min); QA_ONLY=name1,name2 for a subset
RASM_ROOT=/path/to/repo python3 tests/qa_suite.py   # if running from elsewhere
git push                                    # Actions: tests + Pages deploy (~20 s)
gh run list -R shahrosekhalid96-debug/shoof
```
- Chrome at `/usr/bin/google-chrome` or Playwright Chromium (auto-detected). Tests serve local files via a fake host and fail on any external request.
- GitHub notes: this session's proxy allows repo-scoped git/gh only. Repo settings (Pages, app access) must be changed in Shary's Chrome (Claude in Chrome, "Browser 2" is signed in to GitHub). The Claude GitHub App has access to `shoof` and `cleantube-shield-updates`.

## Licence rules for assets
- OK to bundle: Open Peeps / Open Doodles (CC0), Tabler / Lucide / Phosphor icons (MIT/ISC), Google Fonts (OFL), uiGradients (MIT), Hero Patterns (CC BY 4.0, credit in About).
- Do NOT bundle: Canva templates (copyright), unDraw (forbids use inside apps), Unsplash/Pexels collections (forbid compiling into a competing service), DrawKit, tldraw code.
- Templates must be original, built in Shoof's JSON format.

## Backlog (next sprint, in order)
- Done in sprint 3: ~~Welcome home screen~~, ~~Gradients~~ (also Ask Claude can set them), ~~relax Arabic-parity tests to keys that have an Arabic entry~~ (`en_only_strip` in tests).
3. **Elements panel**: searchable icons (bundle a subset of Tabler/Lucide SVGs), CC0 illustrations, stickers, lines, frames (circle/blob photo masks), simple charts.
4. **100+ English templates** across ~10 categories via a template generator script + style spec (no agent hand-writing). Seasonal sets (Ramadan, Eid, Saudi National Day, White Friday) in English.
5. Text style presets, curved text, more fonts.
6. Brand kit (logo, colours, fonts).
7. Later: multi-page designs, resize/adapt to other formats, background removal, animation.
- Also: one automated "gates" addition — axe-core contrast check, page-weight budget, screenshot comparison.
- Gradient follow-ups: multi-stop editor (data model already allows 5 stops), gradient on image frames/placeholders.
- Open items: test Ask Claude for real inside the claude.ai artifact; LICENSE is the SPDX copy of AGPL-3.0 (official text, gnu.org was unreachable).
