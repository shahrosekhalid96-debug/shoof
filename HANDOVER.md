# Handover: Shoof (free open-source Canva alternative)
Updated: 2026-11-17 | From: Claude chat session with repo access (repo `shahrosekhalid96-debug/shoof`)

## Goal
Shoof is Shary's free, browser-only design editor (posts, posters, slides, logos) with the Shoofy helper chat. Live at https://shoof.pages.dev (auto-deploys on every push to `main`). Keep making it easier and better than Canva, at zero cost.

## Status
- Done (all pushed, full suite 116/116 green locally on 2026-11-17):
  - **Presentation maker (2026-11-17):** home tile → type a topic (free AI writes the slides) or paste own text → six looks → opens as an editable 16:9 deck. PowerPoint export as before.
  - **Logo maker upgrade (2026-11-17):** 441 icons, 18 abstract marks, symbol picker, kinds (any / with a symbol / name only / initials), 18 layouts, logo pack download (PNG + SVG for light and dark backgrounds, square icon).
  - **Website pass (2026-11-16):** Feedback box (saved to D1 table `feedback`), Install app button, interactive home page.
  - Earlier work (fonts, QR, share link, photo search, animation, Shoofy designer): see `CLAUDE.md`.
- In progress: nothing.
- Not started:
  - "Support Shoof" donation button. Shary chose donations, not a paid plan. Waiting for his Ko-fi link (he needs a Shoof Gmail, PayPal and Ko-fi first).
  - Microsoft Store listing (free for individuals, package with PWABuilder; Shary does the account steps). Google Play and Apple cost money, parked.
  - Shoofy chat intent "make a presentation", and a home-page card for the Presentation maker.
  - Illustrations section (needs Shary's Open Peeps / Open Doodles zips).

## Next step
Ask Shary to try "Write it for me" in the Presentation maker and the Logo maker on https://shoof.pages.dev, and to say what the AI-written slides look like. Fix what he reports. Then read new feedback (SQL below).

## Files
| File / link | What it is | State |
|---|---|---|
| `CLAUDE.md` | Full project record. Read only the section you need ("Presentation maker + logo maker upgrade", "Website pass"). | current |
| `index.html` | The whole editor (one file) | current |
| `welcome.html` | Home page | current |
| `functions/api/slides.js` | Outline writer for the Presentation maker (free Workers AI, nothing stored) | not verified live |
| `functions/api/feedback.js` | Feedback server (D1 `shoof-learn`, table `feedback`) | not verified live |
| `tools/icons_add.py` | Adds Lucide icons (run `npm i lucide-static` in any folder first) | current |
| `tests/qa_suite.py` | 116 browser tests. Subset: `QA_ONLY=a,b python3 tests/qa_suite.py`. Full run ~8 min, run it in the background: `timeout 1100 python3 tests/qa_suite.py > /tmp/full.txt` | current |

Read feedback (Cloudflare connector, database `shoof-learn`, id `41d56a00-edd0-4b4c-b60c-7e239f9af00a`):
`SELECT id, datetime(ts/1000,'unixepoch') at, kind, page, text, contact FROM feedback WHERE done=0 ORDER BY id DESC;`
"No such table" means nobody has written yet.

## Decisions and rules (do not redo)
- English only for new work; keep existing Arabic working.
- Free cost only. No Unsplash/Pexels, no copied templates; check licences first.
- Money: donations only, no paid plan, no accounts.
- Everything editable; every page starts with a background block.
- Save usage: build directly, no parallel agents, run only related tests, one full run before big pushes. Short plain replies.
- Commit as `Shoof contributors <shahrosekhalid96-debug@users.noreply.github.com>`; never rewrite history or force-push.
- Never enter passwords/keys; Shary does those steps. No scheduled tasks (he declined).
- Update `CLAUDE.md` with every change.
- When Shary cannot find a feature, make it visible (button/tab), do not just explain.
- The home screen keeps 8 tiles: the Presentation maker tile replaced the old Presentation size tile (ready templates are linked inside the maker).

## Tried and failed
- The sandbox shell cannot reach the live site; the WebFetch tool can read it as text but may need Shary's approval. Clicking is checked through his screenshots.
- Broad local chat rules hijack other requests; keep new regexes narrow and run `shoofy_chat`.
- GitHub Pages deploy sometimes fails with "No artifacts named github-pages": rerun it.
- On the home page a CSS class named `.in` broke the before/after box; inputs use `.inp`.
- A foreground full test run hits the 10-minute tool limit; run it in the background.

## Open questions for the user
- Does "Write it for me" return real slides on the live site, and how long does it take? Not verified.
- Does a Feedback message show "Thank you" on the live site? Does "Install app" appear? Not verified.
- Photo search and Shoofy's "I looked at your design" on the live site: not verified.
