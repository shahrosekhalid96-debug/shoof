# Handover: Shoof (free open-source Canva alternative)
Updated: 2026-11-16 | From: Claude chat session with repo access (repo `shahrosekhalid96-debug/shoof`)

## Goal
Shoof is Shary's free, browser-only design editor (posts, posters) with the Shoofy helper/designer chat. Live at https://shoof.pages.dev (auto-deploys on every push to `main`). Keep making it easier and better than Canva, at zero cost.

## Status
- Done (all pushed, full suite 114/114 green locally on 2026-11-16):
  - **Website pass (2026-11-16):** Feedback box (editor top bar + phone menu + floating pill on the home page, saved to D1 table `feedback`), Install app button (editor + home page, iPhone steps in words), interactive home page (type a headline into a real template, three looks, "Describe it" box, draggable before/after, every example picture opens its template).
  - Try-before-apply previews (Keep / Back), big design picker, slim phone chat.
  - 446 fonts (on-demand library, search by feeling, upload your own font).
  - QR code, photo duotone/tint, copy/paste style, fit text to a box.
  - Share a link, free photo search (Openverse), animated video/GIF export.
  - Shoofy: a new pattern replaces the old one; "different colours, same mood" gives palette choices (neon set).
  - Easier to find: Photos tab, background-remover button, "Browse all fonts", labelled "Ask Shoofy about this item" button.
- In progress: nothing.
- Not started:
  - "Support Shoof" donation button. Shary chose donations (not a paid plan). Waiting for him to create a Shoof Gmail, a PayPal account (check it can receive and withdraw in Saudi Arabia) and a Ko-fi page, then send the Ko-fi link.
  - Microsoft Store listing (free for individual developers; package with PWABuilder; Shary does the account and ID steps). Google Play ($25 once, 12 testers for 14 days) and Apple ($99 a year) cost money, so they are parked.
  - Illustrations section (needs Shary's Open Peeps / Open Doodles zip files).

## Next step
Ask Shary to try the new home page, the Feedback button and the Install button on https://shoof.pages.dev, then read any feedback that has arrived (SQL below) and fix what people report.

## Files
| File / link | What it is | State |
|---|---|---|
| `CLAUDE.md` | Full project record: every feature, function names, rules, tests. Read the section you need ("Website pass" for this session's work), not all of it. | current |
| `index.html` | The whole editor (one file) | current |
| `welcome.html` | Home page (one file, 45 KB, budget 60 KB) | current |
| `functions/api/feedback.js` | Feedback server (Cloudflare Pages Function, D1 `shoof-learn`, table `feedback`) | current |
| `functions/api/shoofy.js` | Shoofy chat server (free Workers AI, D1 `shoof-learn`) | current |
| `tools/landing_try.py` | Copies three real templates into the home page preview; rerun after changing those templates | current |
| `tests/qa_suite.py` | 114 browser tests. Subset: `QA_ONLY=a,b python3 tests/qa_suite.py`. Full run ~9 min: `timeout 590 python3 tests/qa_suite.py > /tmp/full.txt` | current |
| `tools/fonts_lib.py`, `fonts/lib/` | Font library generator + 404 font families | current |
| `tools/design_kb.py`, `docs/design-kb-research-2026-11.md` | Shoofy's design knowledge book | current |

Read feedback (Cloudflare connector, database `shoof-learn`, id `41d56a00-edd0-4b4c-b60c-7e239f9af00a`):
`SELECT id, datetime(ts/1000,'unixepoch') at, kind, page, text, contact FROM feedback WHERE done=0 ORDER BY id DESC;`
Mark handled: `UPDATE feedback SET done=1 WHERE id=?;` The table is created by the first message, so "no such table" means nobody has written yet.

## Decisions and rules (do not redo)
- English only for new work; keep existing Arabic working.
- Free cost only. No Unsplash/Pexels, no copied templates; check licences first.
- Money: donations only (Ko-fi with PayPal), no paid plan, no accounts. The page says "Free" and "No account"; keep that true.
- Everything editable; every page starts with a background block.
- Save usage: build directly, no parallel agents, run only related tests, one full run before big pushes. Short plain replies.
- Commit as `Shoof contributors <shahrosekhalid96-debug@users.noreply.github.com>`; never rewrite history or force-push.
- Never enter passwords/keys; Shary does those steps. No scheduled tasks (he declined).
- Update `CLAUDE.md` with every change.
- When Shary cannot find a feature, make it visible (button/tab), do not just explain.

## Tried and failed
- The sandbox shell cannot reach the live site (proxy blocks it), but the WebFetch tool can read https://shoof.pages.dev as text. Anything that needs clicking is still checked through Shary's screenshots.
- Local-first chat rules that are too broad hijack other requests ("make it pop", "change the colour of it"); keep new regexes narrow and run `shoofy_chat`.
- GitHub Pages deploy sometimes fails with "No artifacts named github-pages": rerun it (`gh run rerun <id>`).
- On the home page, a CSS class named `.in` broke the before/after box (it is the scroll-reveal state). Inputs use `.inp`.

## Open questions for the user
- Does a message sent from the Feedback box on the live site show "Thank you"? (Needs the `DB` binding, which is already set.) Not verified live.
- Does the Install app button appear in his Chrome and on his phone? Not verified live.
- Does photo search return photos on the live site (Photos tab)? Not verified.
- Does Shoofy show "I looked at your design" when asked for an opinion? Not verified.
