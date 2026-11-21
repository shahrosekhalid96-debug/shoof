# Shoof design system

One visual language for the landing page (`welcome.html`), the creative hub (editor home screen) and the editor (`index.html`). Dark-first, premium and calm, with glass panels. Neon is used only for active states, AI features, primary actions and selected tools. The design page itself always shows the user's own colours.

## Colours

| Token | Landing | Editor | Use |
|---|---|---|---|
| Background | `--bg #07060c` | `--bg #121119` | Page / work area |
| Panel | `--glass rgba(255,255,255,.045)` | `--panel #1b1a25` | Glass cards, side panels, menus, dialogs |
| Card | — | `--card #252433` | Buttons, inputs, tiles |
| Hover | `rgba(255,255,255,.1)` | `--hover #2f2d40` | Hover fill |
| Line | `--line rgba(255,255,255,.13)` | `--line #353349` | 1 px borders |
| Text | `--ink #f4f2ff` | `--ink #eeedf7` | Body and headings |
| Muted text | `--muted #b3afcf` | `--muted #a9a7bf` | Secondary text (≥4.5:1 on the background) |
| Accent | `--accent #6c4cf5` | `--accent #6c4cf5` | Filled primary buttons (white text 5:1) |
| Accent as text | `--hi #c2b3ff` | `--accent-ink #bdaaff` | Links, kickers, active icons |
| Accent soft | — | `--accent-soft #2d2552` | Icon tiles, chips behind icons |
| Holographic | `--holo` cyan → violet → pink → gold | — | AI headline words, final CTA, card icon tiles |
| Spark | `--spark #ff7a3d` | `#f76707` | Logo pupils, "Free AI" badges |

Rules: never put text on the holographic gradient except dark text on `.btn.lum`; never use `#fff` panels in the editor chrome — use the variables.

## Type

- Display: **Syne 700** (landing headings), **Poppins 700** (hub title).
- Text: **Inter** 400/600/700 everywhere.
- Scale (landing): h1 clamp(44–92 px), h2 clamp(34–62 px), body 18 px, small 14–15 px. Editor: 13–15 px UI, 18 px section headings.

## Shape, depth, motion

- Radius: pill (999 px) for buttons and chips, 14–16 px tiles and inputs, 22 px cards, 32 px bands.
- Glow: `0 0 0 1px rgba(108,76,245,.18), 0 18px 60px rgba(108,76,245,.28)` on the main AI input and the Ask Shoof button; nowhere else.
- Hover: cards lift 2 px, pictures zoom 1.03 inside their frame, buttons step up 2 px and press to 0.98.
- Motion is off under `prefers-reduced-motion`; the landing page also has a low-power mode (`html.lite`).

## Components

| Component | Landing | Hub / editor |
|---|---|---|
| Primary button | `.btn.primary` | `button.primary` |
| Secondary button | `.btn` | `button` |
| AI button | `.btn.lum` (final CTA) | `.askbtn` (Ask Shoof), `#homeDescGo` "Make it ✦" |
| Chip | `.chip[aria-checked]` | `.qtype` (quick types), `.aicmds button` (one-tap commands) |
| Glass card | `.card.foil` | `.tile.htool` (AI tools) |
| AI input | `form.ask .askrow` | `.hubask .hdrow` |
| Template card | `.gal a` | `.hcard` |
| Empty state | — | `.hempty` (icon, one line, one action) |
| Dialog | `<dialog>` | `modal()` + `.newfoot` |
| Loading | — | toast + button label ("Writing… a few seconds") |

## Flow

Landing (`/`) → Start designing → Creative hub (editor home) → Editor → Ask Shoof / AI tab → Download or Share. Landing search (`?q=`), gallery category (`?cat=`), describe box (`?describe=`) and template cards (`?tpl=`) all open the editor in the right place.
