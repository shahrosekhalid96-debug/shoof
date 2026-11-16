# Handover: Shoof (free open-source Canva alternative)
Updated: 2026-11-16 | From: Claude chat session with repo access (repo `shahrosekhalid96-debug/shoof`)

## Goal
Shoof is Shary's free, browser-only design editor (posts, posters) with the Shoofy helper/designer chat. Live at https://shoof.pages.dev (auto-deploys on every push to `main`). Keep making it easier and better than Canva, at zero cost.

## Status
- Done (all pushed, last commit `2209da3`, GitHub tests green):
  - Try-before-apply previews (Keep / Back), big design picker, slim phone chat.
  - 446 fonts (on-demand library, search by feeling, upload your own font).
  - QR code, photo duotone/tint, copy/paste style, fit text to a box.
  - Share a link, free photo search (Openverse), animated video/GIF export.
  - Shoofy: a new pattern replaces the old one; "different colours, same mood" gives palette choices (neon set).
  - Easier to find: Photos tab, background-remover button, "Browse all fonts" in the Text tab and phone quick bar, labelled "Ask Shoofy about this item" button.
  - Phone: chat shrinks after an edit so the design shows, Undo in the slim bar.
- In progress: nothing.
- Not started: Illustrations section (needs Shary's Open Peeps / Open Doodles zip files).

## Next step
Ask Shary what he saw when testing on the live site (see "Open questions"), fix whatever he reports, then continue with his next request.

## Files
| File / link | What it is | State |
|---|---|---|
| `CLAUDE.md` | Full project record: every feature, function names, rules, tests. Read the section you need, not all of it. | current |
| `index.html` | The whole app (one file) | current |
| `functions/api/shoofy.js` | Shoofy chat server (Cloudflare Pages Function, free Workers AI, D1 `shoof-learn`) | current |
| `tests/qa_suite.py` | 113 browser tests. Subset: `QA_ONLY=a,b python3 tests/qa_suite.py`. Full run ~9 min: `timeout 590 python3 tests/qa_suite.py > /tmp/full.txt` | current |
| `tools/fonts_lib.py`, `fonts/lib/` | Font library generator + 404 font families | current |
| `tools/design_kb.py`, `docs/design-kb-research-2026-11.md` | Shoofy's design knowledge book | current |

## Decisions and rules (do not redo)
- English only for new work; keep existing Arabic working.
- Free cost only. No Unsplash/Pexels, no copied templates; check licences first.
- Everything editable; every page starts with a background block.
- Save usage: build directly, no parallel agents, run only related tests, one full run before big pushes. Short plain replies.
- Commit as `Shoof contributors <shahrosekhalid96-debug@users.noreply.github.com>`; never rewrite history or force-push.
- Never enter passwords/keys; Shary does those steps. No scheduled tasks (he declined).
- Update `CLAUDE.md` with every change.
- When Shary cannot find a feature, make it visible (button/tab), do not just explain.

## Tried and failed
- Live site cannot be reached from the sandbox (proxy blocks it), so live behaviour is checked only through Shary's screenshots.
- Local-first chat rules that are too broad hijack other requests ("make it pop", "change the colour of it"); keep new regexes narrow and run `shoofy_chat`.
- GitHub Pages deploy sometimes fails with "No artifacts named github-pages": rerun it (`gh run rerun <id>`).

## Open questions for the user
- Does photo search return photos on the live site (Photos tab)? Not verified.
- Does Shoofy show "I looked at your design" when asked for an opinion? Not verified.
- Does the phone chat now shrink after an edit, and is "Browse all fonts" visible after a refresh? Not verified on his phone.
