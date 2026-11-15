# Design KB research: social posts, posters and flyers (November 2026)

All fonts, textures and effects are Shoof built-ins. Contrast ratios use the WCAG 2.1 formula.

## 1. Verdict

- **IN (mass appeal):** warm, human, "imperfect" design: paper/grain textures, hand-drawn accents, scrapbook layouts (shared theme of Canva, Adobe, Kittl 2026).
- **IN:** oversized expressive type as the main graphic: big bold sans, bubbly letters, type collages. Cheap to make, stops the scroll.
- **IN:** calm warm-neutral bases (Pantone 2026 is an off-white) with one confident saturated accent.
- **IN (niche, rising):** retro-futurist neon for events and nightlife; local/heritage patterns for regional brands.
- **OUT:** (1) frosted or "liquid glass" panels on everything; (2) AI-looking imagery and caricatures, plus Corporate Memphis-style flat people; (3) default purple-to-blue gradients and bento grids used without a reason.

## 2. Styles

Roles: bg / surface / text / accent / accent2. Text/bg and text/surface are both at least 4.5:1 (ratio shown). Button labels: 28 px bold or larger.

| id | name | why / who | fonts {head, body} | palette | texture | effect | shape language | radius |
|---|---|---|---|---|---|---|---|---|
| warm_tactile | Warm & Tactile | Handmade, trustworthy. Cafés, bakeries, crafts. | DM Serif Display / DM Sans | bg #F3EADF, surface #FFFAF3, text #3B2A20 (11.5), accent #C8643B, accent2 #7A8B5C | dotGrid (low opacity) | soft | Soft cards, slightly rotated photo with tape strips, blob behind the product | 24 |
| bold_type_pop | Big Type Pop | Type as hero, readable as a thumbnail. Sales, launches. | Anton / Poppins | bg #FFE14D, surface #FFFFFF, text #141414 (14.2), accent #FF3D7F, accent2 #2B59FF | none | retro | Headline fills 60–80% of the width, pill tags, one star burst | 40 |
| scrapbook_notes | Scrapbook Notes | Notes-app collage, personal. Stories, creators, boutiques. | Caveat / Nunito | bg #F6F1E7, surface #FFFFFF, text #2A2A2A (12.8), accent #F2B8C6, accent2 #8FB8DE | stripesFade | marker | Paper cards at ±3° rotation, polaroid frames, hand-drawn arrows | 8 |
| quiet_serif | Quiet Serif | Calm premium. Clinics, coaches, boutiques. | Cormorant Garamond / Lato | bg #F4F1EC, surface #FFFFFF, text #2E2C2A (12.4), accent #A68A64, accent2 #6E7B73 | none | none | Thin rules, generous margins, one arch or full-bleed photo, no ornaments | 0 |
| naive_playful | Naive & Playful | Bubbly, friendly to all ages. Kids, desserts, family events. | Fredoka / Nunito | bg #FFF4E0, surface #FFFFFF, text #2D1E5C (13.3), accent #FF7A59, accent2 #3CC4A0 | pixelCircle | sticker | Blobs, chunky stars, wobbly rounded cards, oversized emoji-like icons | 48 |
| retro_neon | Retro Neon Night | Fastest-rising Envato search. Events, gaming, nightlife only. | Righteous / Space Grotesk | bg #14112B, surface #241E4A, text #F5F3FF (16.7), accent #FF4FD8, accent2 #36E2F0 | contours | neon | Dark field, glowing outline shapes, a horizon grid made of lines | 16 |
| heritage_local | Heritage Local | Local pride. Regional food, Ramadan/Eid, national days. | Playfair Display / Lora | bg #0F3D3A, surface #164B47 (text 8.9), text #F8F3EA (10.9), accent #D9A441, accent2 #B5523B | dotsRing | none | Arches and domes made from ellipse + rect, hexagon/star lattice borders, gold rules | 30 |
| grainy_glow | Grainy Glow | Dreamy grain-blur colour. Beauty, wellness, music. | Raleway / Inter | bg #FBE9E4, surface #FFFFFF, text #2B2235 (12.9), accent #FF8A65, accent2 #9C7BE8 | dotsFade | soft | Large radial-gradient blobs at 40–60% opacity, one clean card on top | 32 |
| bold_block | Bold Block | Light neo-brutalism, very legible. Promos, gyms, street food. | Archivo Black / Work Sans | bg #FFFFFF, surface #F2F2F2, text #111111 (18.9), accent #FF5A1F, accent2 #FFD23F | stripes | retro | Thick black outlines (6–8 px), solid offset shadows, square tags | 0 |
| blueprint_tech | Blueprint Tech | Technical-drawing decor. Startups, apps, workshops. | Space Grotesk / JetBrains Mono | bg #0B2545, surface #13315C, text #EEF4ED (13.8), accent #5FD3F3, accent2 #F2C94C | dotGrid | none | Thin lines, arrows with labels, crosshair corners, mono captions | 4 |

**Do / don't tips**

- warm_tactile: texture under 15% opacity; one serif only.
- bold_type_pop: headline on 2–3 lines, line height about 0.9; no photo plus pattern.
- scrapbook_notes: at most 3 tilted items; script only for 6 words or fewer.
- quiet_serif: 10–12% margins; no gradients or effects.
- naive_playful: navy text, not black; shapes never cover price or date.
- retro_neon: neon on headline and 1–2 shapes only; not for food, health or finance.
- heritage_local: patterns from simple geometry; never sacred calligraphy as decoration.
- grainy_glow: 2–3 neighbouring hues; no small text over blob edges.
- bold_block: strict grid; no rounded corners.
- blueprint_tech: label lines like a real diagram; max 2 accents.

## 3. Palettes

bg / surface / text / accent / accent2 (text/bg ratio; text/surface also ≥4.5).

**Food & café**
- `food_espresso` Espresso Bar (cosy, roasted, artisanal): #F5ECE1 / #FFFFFF / #3E2723 / #C0692B / #6B8E4E (11.8)
- `food_fresh` Fresh Market (zesty, appetising, sunny): #FFF8EC / #FFFFFF / #233D2A / #F25C2A / #F7B32B (11.2)

**Beauty & spa**
- `beauty_blush` Blush Studio (soft, feminine, polished): #FBEFEC / #FFFFFF / #4A2B33 / #D98A94 / #C9A27E (11.1)
- `beauty_spa` Sage Spa (calm, clean, restorative): #EEF2EC / #FFFFFF / #2F3E36 / #8BA888 / #D8C3A5 (10.0)

**Tech & startup**
- `tech_midnight` Midnight Launch (smart, energetic, nocturnal): #0E1525 / #1A2440 / #F1F5FF / #5B8CFF / #2EE6A6 (16.7)
- `tech_clean` Clean SaaS (crisp, trustworthy, modern): #F7F8FC / #FFFFFF / #121826 / #4F46E5 / #14B8A6 (16.7)

**Luxury**
- `lux_noir_gold` Noir & Gold (exclusive, dramatic, refined): #111111 / #1E1E1E / #F5EFE3 / #C9A55C / #8C7853 (16.5)
- `lux_ivory` Ivory Atelier (elegant, quiet, heritage): #F7F3EC / #FFFFFF / #1F1B16 / #9C7C4A / #2F4A3A (15.5)

**Kids & fun**
- `kids_candy` Candy Shop (cheerful, bouncy, sweet): #FFF3D6 / #FFFFFF / #2B2D6E / #FF6B6B / #4ECDC4 (11.2)
- `kids_sky` Sky Play (bright, sunny, adventurous): #E7F5FF / #FFFFFF / #1D2B53 / #FFB703 / #FB5607 (12.4)

**Health**
- `health_care` Clinic Teal (caring, clean, reassuring): #F1F7F6 / #FFFFFF / #12343B / #2A9D8F / #E76F51 (12.3)

**Eco**
- `eco_earth` Earth & Moss (natural, grounded, honest): #EFEBDD / #FAF7EE / #2D3A22 / #6A8D3A / #C17C3C (10.1)

**Finance / corporate**
- `finance_navy` Navy Trust (stable, professional, clear): #F5F7FA / #FFFFFF / #0F2340 / #1F5FBF / #F2A900 (14.7)
- `finance_slate` Slate Ledger (serious, modern, confident): #1C2833 / #273746 / #F4F6F7 / #48C9B0 / #F4D03F (13.8)

**Events & celebrations**
- `event_fiesta` Fiesta Night (festive, loud, joyful): #2A0F3D / #3D1A57 / #FFF6E9 / #FF4E8A / #FFC53D (15.9)
- `event_gala` Evening Gala (formal, romantic, glamorous): #0E1F2F / #17324A / #F6F1E6 / #D4AF6A / #E8C7C8 (14.9)

**Ramadan / Eid & Middle-East seasonal**
- `ramadan_night` Ramadan Night (serene, spiritual, golden): #0D1B3E / #16285A / #F8F1DE / #E3B04B / #6FA3C8 (15.0)
- `eid_pastel` Eid Pastel (joyful, soft, fresh).: #F4EEF8 / #FFFFFF / #3A2B4F / #9BC4A8 / #E6A9C0 (11.3)

**Fashion**
- `fashion_mono` Editorial Mono (bold, stylish, minimal): #EDEAE4 / #FFFFFF / #121212 / #B5462F / #8A8F7A (15.6)

**Real estate**
- `realestate_stone` Stone & Pine (solid, upscale, calm): #F2F0EB / #FFFFFF / #1E2A32 / #2F6F63 / #C8A46B (12.9)

On dark palettes, use bg-coloured text on accent buttons, not white.

## 4. Font pairings

| # | head | body | mood | best for |
|---|---|---|---|---|
| 1 | Anton | Poppins | loud, confident | Sales, launches, big offers |
| 2 | Bebas Neue | Montserrat | sporty, urban | Gyms, events, street food |
| 3 | DM Serif Display | DM Sans | warm, modern-classic | Cafés, restaurants, boutiques |
| 4 | Playfair Display | Lato | elegant, editorial | Fashion, beauty, real estate |
| 5 | Cormorant Garamond | Raleway | luxurious, airy | Spas, weddings, jewellery |
| 6 | Fredoka | Nunito | friendly, rounded | Kids, desserts, family events |
| 7 | Space Grotesk | Inter | techy, precise | Startups, apps, webinars |
| 8 | Archivo Black | Work Sans | punchy, utilitarian | Promos, price lists, hardware |
| 9 | Abril Fatface | Open Sans | dramatic, magazine | Covers, quotes, announcements |
| 10 | Righteous | Space Mono | retro-future | Nightlife, gaming, music |
| 11 | Pacifico (accent word only) | Poppins | cheerful, casual | Ice cream, cafés, summer posts |
| 12 | Merriweather | Roboto | trustworthy, clear | Clinics, finance, education |

Scripts (Great Vibes, Sacramento, Dancing Script): one accent word, 40 px or more, never body.

## 5. Colour rules

1. **60-30-10:** 60% bg, 30% surface/photo, 10% accent on the one thing to read first (price, date, button).
2. **3–5 colours:** one neutral, one text colour, at most two accents; tints don't count as extra.
3. **Contrast first:** body ≥4.5:1, big headlines ≥3:1. Text on busy photos needs a scrim (dark rect 40–60%) or a card.
4. **One harmony:** analogous for calm, complementary for energy, one hue plus neutral for premium.
5. **Temperature = mood:** warm for food and offers, cool for tech, health, finance; one dominates.
6. **Mute the base, saturate the accent** (matches the 2026 off-white trend).
7. **Photos lead:** sample accents from the product photo; desaturate busy photos.
8. **Gradients need a reason:** neighbouring hues, 2–3 stops, pointing to the headline.

## 6. Layout & composition rules

1. **Three levels:** headline, support line, CTA/details; headline ≥2× the next size.
2. **Thumb-stopping size:** at 1080 px, headline 90–160 px, body ≥32 px; must read at 25% zoom.
3. **Safe margins:** 6–8% each side (70–90 px). Stories 1080×1920: no text in top 250 px or bottom 340 px.
4. **Grid:** 4 or 12 columns, shared left edges; centre only text of ≤3 lines.
5. **Whitespace:** leave 30–40% empty.
6. **One focal point** on a rule-of-thirds line; nothing competes with it in size.
7. **Proximity:** date, place and price grouped on one card; separate groups with space, not lines.
8. **Restraint:** ≤25 words and ≤2 families per post (plus one accent word); logo in a corner at 8–12% width.

## 7. Sources

- Adobe Express, "Graphic design trends 2026", 12 Dec 2025: https://www.adobe.com/express/learn/blog/graphic-design-trends-2026
- Creative Bloq on Canva's 2026 Design Trends Report ("Imperfect by Design"), 28 Dec 2025: https://www.creativebloq.com/design/canvas-2026-trend-predictions-have-filled-me-with-hope
- Pantone Color of the Year 2026, Cloud Dancer (via Fox/KTVU wire), 4 Dec 2025: https://www.fox5ny.com/news/pantones-color-year-2026
- Envato Creative Trends 2026 (via CEPIC), 30 Mar 2026: https://www.cepic.org/post/envato-launches-its-creative-trends-2026-series-the-future-of-design-music-filmmaking-and-more
- Kittl, 2026 graphic design trends, 1 Jan 2026: https://www.kittl.com/blogs/?p=10191
- Creative Boom, "10 trends creatives are so over in 2026", 21 Apr 2026: https://creativeboom.com/insight/10-trends-creatives-are-so-over-in-2026/
- Creative Bloq, outdated graphic design trends, 9 Mar 2025: https://www.creativebloq.com/design/graphic-design/these-are-the-outdated-graphic-design-trends-that-creatives-wish-would-disappear
- BINUS International, "7 design trends in 2026 that actually matter", 25 May 2026: https://international.binus.ac.id/graphic-design/2026/05/25/7-design-trends-in-2026-that-actually-matter/
- Cornell Daily Sun, "Four trends for Eid 2026", 4 Mar 2026: https://www.cornellsun.com/article/2026/03/blessing-your-feed-four-trends-for-eid-2026
