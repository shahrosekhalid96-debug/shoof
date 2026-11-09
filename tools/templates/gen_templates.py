#!/usr/bin/env python3
"""Shoof template generator.

Builds the English template set from a small style spec (palettes, font pairs,
layout recipes) plus a content table, then writes it into index.html between
the @generated-templates markers. Edit this file, not the generated block.

    python3 tools/templates/gen_templates.py            # write into index.html
    python3 tools/templates/gen_templates.py --check    # fail if index.html is stale

All templates are original. Text sizes are chosen with a rough width model so
text wraps inside its box; the QA suite checks the real rendering (no text off
the page, no overlapping text boxes).
"""
import json, math, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INDEX = os.path.join(ROOT, 'index.html')
START = '/* @generated-templates:start'
END = '/* @generated-templates:end */'

# ------------------------------------------------------------------ style spec
PAL = {  # bg, ink, muted, accent, accent2, surface, on (text on accent)
    'violet': dict(bg='#f4f0ff', ink='#1d1640', muted='#5d5683', accent='#6c4cf5', accent2='#ff6a88', surface='#ffffff', on='#ffffff'),
    'navy':   dict(bg='#0f2742', ink='#ffffff', muted='#b9cbe0', accent='#ffb020', accent2='#1e4d7b', surface='#16365a', on='#0f2742'),
    'coral':  dict(bg='#fff1ea', ink='#2a1407', muted='#7a5240', accent='#ff6a3d', accent2='#ffc94d', surface='#ffffff', on='#ffffff'),
    'mint':   dict(bg='#e9f8f2', ink='#0d3b2e', muted='#3f6b5d', accent='#14a374', accent2='#ffcf5c', surface='#ffffff', on='#ffffff'),
    'black':  dict(bg='#111111', ink='#f5efe6', muted='#a8a29a', accent='#ff4f6d', accent2='#2a2a2a', surface='#1e1e1e', on='#ffffff'),
    'sand':   dict(bg='#f5efe6', ink='#2b2420', muted='#6f625a', accent='#c76a12', accent2='#e3d3bd', surface='#fffaf3', on='#ffffff'),
    'sky':    dict(bg='#eaf4ff', ink='#0c2a4d', muted='#4a6585', accent='#2f62d6', accent2='#ffd27a', surface='#ffffff', on='#ffffff'),
    'pink':   dict(bg='#ffe9f0', ink='#3a0f22', muted='#80485f', accent='#e0457b', accent2='#ffc2d4', surface='#ffffff', on='#ffffff'),
    'forest': dict(bg='#0e3b2c', ink='#f3f7f2', muted='#b5cfc3', accent='#d8b45a', accent2='#15513c', surface='#15513c', on='#0e3b2c'),
    'green':  dict(bg='#006c35', ink='#ffffff', muted='#cfe8da', accent='#ffffff', accent2='#0b7d43', surface='#0b7d43', on='#006c35'),
    'night':  dict(bg='#141b3a', ink='#ffffff', muted='#b8bfe0', accent='#d8b45a', accent2='#232c5c', surface='#1f2850', on='#141b3a'),
    'lemon':  dict(bg='#fff6cc', ink='#1d2330', muted='#5c5a48', accent='#1d2330', accent2='#ffde59', surface='#ffffff', on='#ffffff'),
}
FONTS = {  # display font, body font
    'modern': ('Poppins', 'Inter'),
    'loud': ('Bebas Neue', 'Inter'),
    'classic': ('Playfair Display', 'Inter'),
}
# average glyph width / font size, used to estimate wrapping
CW = {('Poppins', True): 0.62, ('Poppins', False): 0.57, ('Inter', True): 0.57, ('Inter', False): 0.53,
      ('Bebas Neue', True): 0.42, ('Bebas Neue', False): 0.42, ('Playfair Display', True): 0.58, ('Playfair Display', False): 0.53}


def lines(text, font, size, width, bold):
    cw = CW[(font, bold)] * size * 1.06
    n = 0
    for para in text.split('\n'):
        words, cur, k = para.split(' '), 0.0, 1
        for w in words:
            wl = len(w) * cw
            add = wl if cur == 0 else wl + cw
            if cur + add > width and cur > 0:
                k += 1; cur = wl
            else:
                cur += add
        n += k
    return n


def fit(text, font, size, width, bold, max_lines):
    """Shrink size until the text fits in max_lines; never wider than the box."""
    longest = max(len(w) for w in re.split(r'\s+', text) if w)
    size = min(size, width / (longest * CW[(font, bold)] * 1.1))
    while size > 10 and lines(text, font, size, width, bold) > max_lines:
        size *= 0.94
    return round(size)


# ------------------------------------------------------------------ element helpers
def R(x, y, w, h, fill, **kw): return dict(type='rect', x=round(x), y=round(y), width=round(w), height=round(h), fill=fill, **kw)
def E(x, y, w, h, fill, **kw): return dict(type='ellipse', x=round(x), y=round(y), width=round(w), height=round(h), fill=fill, **kw)
def S(kind, x, y, w, h, fill, **kw): return dict(type=kind, x=round(x), y=round(y), width=round(w), height=round(h), fill=fill, **kw)
def I(name, x, y, sz, color, sw=2, fill=''): return dict(type='icon', icon=name, x=round(x), y=round(y), width=round(sz), height=round(sz), stroke=color, strokeWidth=sw, fill=fill)
def PH(x, y, w, h, fill, **kw): return dict(type='placeholder', x=round(x), y=round(y), width=round(w), height=round(h), fill=fill, **kw)


class Flow:
    """Stacks text blocks top-down and remembers the bottom edge."""
    def __init__(self, x, y, w, align='left'):
        self.x, self.y, self.w, self.align, self.els = x, y, w, align, []

    def text(self, text, font, size, color, bold=False, lh=1.2, max_lines=3, gap=0.0, ls=0, w=None):
        w = w or self.w
        size = fit(text, font, size, w, bold, max_lines)
        n = lines(text, font, size, w, bold)
        el = dict(type='text', x=round(self.x), y=round(self.y), width=round(w), text=text, fontFamily=font, fontSize=size,
                  bold=bold, fill=color, align=self.align, lineHeight=lh)
        if ls: el['letterSpacing'] = ls
        self.els.append(el)
        self.y += n * size * lh + gap
        return el

    def space(self, d): self.y += d


def shift(els, dy):
    for e in els: e['y'] = round(e['y'] + dy)
    return els


def pill(x, y, text, font, size, bg, fg, pad=1.2, w=None, align='left'):
    tw = len(text) * CW[(font, True)] * size * 1.08 + pad * size * 2
    w = w or tw
    h = size * 2.3
    if align == 'center': x = x - w / 2
    return [R(x, y, w, h, bg, radius=round(h / 2)),
            dict(type='text', x=round(x), y=round(y + (h - size * 1.2) / 2), width=round(w), text=text, fontFamily=font, fontSize=round(size), bold=True, fill=fg, align='center', lineHeight=1.2)], h, w


# ------------------------------------------------------------------ recipes
def r_bold(W, H, P, F, c):
    """Big headline, colour blob, badge, body and a CTA pill anchored to the bottom."""
    s = W / 1080; m = 90 * s; D, B = F
    els = [E(W * 0.55, -W * 0.18, W * 0.62, W * 0.62, P['accent2'])]
    if c.get('shape') == 'star': els.append(S('star', W - m - 260 * s, H - m - 300 * s, 260 * s, 260 * s, P['accent']))
    f = Flow(m, m + 40 * s, W - 2 * m)
    if c.get('badge'):
        p, h, _ = pill(m, f.y, c['badge'], B, 22 * s, P['accent'], P['on']); els += p; f.space(h + 50 * s)
    f.text(c['title'], D, (150 if D == 'Bebas Neue' else 112) * s, P['ink'], bold=D != 'Bebas Neue', lh=1.0 if D == 'Bebas Neue' else 1.05, max_lines=3, gap=36 * s)
    if c.get('sub'): f.text(c['sub'], B, 46 * s, P['accent'] if P['accent'] != P['ink'] else P['ink'], bold=True, max_lines=2, gap=26 * s)
    if c.get('body'): f.text(c['body'], B, 34 * s, P['muted'], lh=1.4, max_lines=4)
    els += f.els
    if c.get('cta'):
        p, h, _ = pill(m, H - m - 100 * s, c['cta'], D if D != 'Bebas Neue' else B, 34 * s, P['ink'], P['bg'])
        els += p
    return els


def r_center(W, H, P, F, c):
    s = W / 1080; m = 100 * s; D, B = F
    els = [E(-W * 0.2, H - W * 0.38, W * 0.55, W * 0.55, P['accent2']), E(W * 0.78, -W * 0.12, W * 0.36, W * 0.36, P['accent2'])]
    y = m + 50 * s
    if c.get('icon'):
        els.append(I(c['icon'], W / 2 - 70 * s, y, 140 * s, P['accent'], sw=1.75)); y += 190 * s
    f = Flow(m, y, W - 2 * m, 'center')
    if c.get('kicker'): f.text(c['kicker'].upper(), B, 30 * s, P['accent'], bold=True, max_lines=1, gap=24 * s, ls=round(4 * s))
    f.text(c['title'], D, (160 if D == 'Bebas Neue' else 104) * s, P['ink'], bold=D != 'Bebas Neue', lh=1.05, max_lines=3, gap=30 * s)
    if c.get('sub'): f.text(c['sub'], B, 40 * s, P['muted'], lh=1.4, max_lines=3)
    els += f.els
    if c.get('cta'):
        p, h, _ = pill(W / 2, H - m - 110 * s, c['cta'], B, 32 * s, P['accent'], P['on'], align='center'); els += p
    return els


def r_photo(W, H, P, F, c):
    """Photo frame on top, text below; the photo shrinks if the text needs room above the bottom pill."""
    s = W / 1080; m = 80 * s; D, B = F
    ph = H * (0.5 if H > W else 0.46)
    bottom = H - m - (96 if c.get('price') else 90) * s - 30 * s if (c.get('price') or c.get('cta')) else H - m
    for _ in range(3):
        f = Flow(m, m + ph + 60 * s, W - 2 * m)
        if c.get('kicker'): f.text(c['kicker'].upper(), B, 28 * s, P['accent'], bold=True, max_lines=1, gap=18 * s, ls=round(3 * s))
        f.text(c['title'], D, (120 if D == 'Bebas Neue' else 84) * s, P['ink'], bold=D != 'Bebas Neue', lh=1.05, max_lines=2, gap=22 * s)
        if c.get('sub'): f.text(c['sub'], B, 34 * s, P['muted'], lh=1.4, max_lines=2)
        over = f.y - bottom
        if over <= 0: break
        ph = max(H * 0.28, ph - over)
    els = [PH(m, m, W - 2 * m, ph, P['accent2'], radius=round(36 * s), **({'mask': c['mask']} if c.get('mask') else {}))]
    els += f.els
    if c.get('price'):
        p, h, w = pill(W - m, H - m - 96 * s, c['price'], B, 34 * s, P['accent'], P['on']); p[0]['x'] = round(W - m - w); p[1]['x'] = round(W - m - w); els += p
    elif c.get('cta'):
        p, h, _ = pill(m, H - m - 90 * s, c['cta'], B, 30 * s, P['ink'], P['bg']); els += p
    return els


def r_promo(W, H, P, F, c):
    s = W / 1080; m = 90 * s; D, B = F
    split = 0.64 if H > W * 1.2 else 0.62
    els = [R(0, H * split, W, H * (1 - split), P['accent2']), S('star', W - m - 230 * s, m, 230 * s, 230 * s, P['accent'])]
    f = Flow(m, m + 20 * s, W - 2 * m - 230 * s)
    if c.get('kicker'): f.text(c['kicker'].upper(), B, 32 * s, P['ink'], bold=True, max_lines=1, gap=10 * s, ls=round(4 * s))
    f.text(c['big'].replace(' ', '\n') if H > W * 1.2 else c['big'], 'Bebas Neue', (380 if H > W * 1.2 else 330) * s, P['accent'], lh=0.95, max_lines=2 if H > W * 1.2 else 1, gap=0)
    els += f.els
    f2 = Flow(m, H * split + 60 * s, W - 2 * m)
    f2.text(c['title'], D, (110 if D == 'Bebas Neue' else 76) * s, P['ink'], bold=D != 'Bebas Neue', lh=1.05, max_lines=2, gap=20 * s)
    if c.get('sub'): f2.text(c['sub'], B, 32 * s, P['muted'], lh=1.4, max_lines=2)
    els += f2.els
    return els


def r_quote(W, H, P, F, c):
    s = W / 1080; m = 110 * s; D, B = F
    els = [I('quote', m, m, 120 * s, P['accent'], sw=1.5, fill=P['accent'])]
    f = Flow(m, m + 190 * s, W - 2 * m)
    f.text(c['title'], 'Playfair Display', 84 * s, P['ink'], lh=1.3, max_lines=6, gap=50 * s)
    els += f.els
    els.append(S('line', m, f.y, 120 * s, 8 * s, P['accent']))
    f.space(50 * s)
    f.text(c['sub'], B, 34 * s, P['ink'], bold=True, max_lines=1, gap=8 * s)
    if c.get('body'): f.text(c['body'], B, 28 * s, P['muted'], max_lines=1)
    els += f.els[-2:] if c.get('body') else f.els[-1:]
    used = f.y - m
    return shift(els, max(0, (H - used) / 2 - m - 20 * s))


def r_list(W, H, P, F, c):
    s = W / 1080; m = 90 * s; D, B = F
    els = [R(0, 0, W, 16 * s, P['accent'])]
    f = Flow(m, m + 20 * s, W - 2 * m)
    if c.get('kicker'): f.text(c['kicker'].upper(), B, 28 * s, P['accent'], bold=True, max_lines=1, gap=18 * s, ls=round(3 * s))
    f.text(c['title'], D, (120 if D == 'Bebas Neue' else 78) * s, P['ink'], bold=D != 'Bebas Neue', lh=1.05, max_lines=2, gap=50 * s)
    els += f.els
    items = c['items']
    avail = H - f.y - m - (60 * s if c.get('foot') else 0)
    tall = H > W * 1.4
    row = min(avail / len(items), (260 if tall else 190) * s)
    for i, it in enumerate(items):
        y = f.y + i * row
        d = min((100 if tall else 84) * s, row * 0.6)
        if c.get('checks'): els.append(I('circle-check', m, y, d, P['accent'], sw=2))
        else:
            els += [E(m, y, d, d, P['accent']), dict(type='text', x=round(m), y=round(y + d * 0.2), width=round(d), text=str(i + 1), fontFamily=B, fontSize=round(d * 0.5), bold=True, fill=P['on'], align='center', lineHeight=1.2)]
        tw = W - 2 * m - d - 30 * s
        fs = fit(it, B, (50 if tall else 38) * s, tw, False, 2)
        nl = lines(it, B, fs, tw, False)
        els.append(dict(type='text', x=round(m + d + 30 * s), y=round(y + d / 2 - nl * fs * 1.3 / 2), width=round(tw), text=it, fontFamily=B, fontSize=fs, fill=P['ink'], align='left', lineHeight=1.3))
    if c.get('foot'):
        els.append(dict(type='text', x=round(m), y=round(H - m - 30 * s), width=round(W - 2 * m), text=c['foot'], fontFamily=B, fontSize=round(28 * s), bold=True, fill=P['muted'], align='left', lineHeight=1.2))
    return els


def r_event(W, H, P, F, c):
    s = W / 1080; m = 90 * s; D, B = F
    els = [R(m, m, 200 * s, 220 * s, P['accent'], radius=round(28 * s)),
           dict(type='text', x=round(m), y=round(m + 28 * s), width=round(200 * s), text=c['month'], fontFamily=B, fontSize=round(34 * s), bold=True, fill=P['on'], align='center', lineHeight=1.2),
           dict(type='text', x=round(m), y=round(m + 70 * s), width=round(200 * s), text=c['day'], fontFamily='Bebas Neue', fontSize=round(130 * s), fill=P['on'], align='center', lineHeight=1.0),
           E(W - W * 0.32, H - W * 0.3, W * 0.5, W * 0.5, P['accent2'])]
    f = Flow(m, m + 290 * s, W - 2 * m)
    if c.get('kicker'): f.text(c['kicker'].upper(), B, 30 * s, P['accent'], bold=True, max_lines=1, gap=18 * s, ls=round(3 * s))
    f.text(c['title'], D, (140 if D == 'Bebas Neue' else 92) * s, P['ink'], bold=D != 'Bebas Neue', lh=1.05, max_lines=3, gap=44 * s)
    els += f.els
    for ic, txt in c['info']:
        els.append(I(ic, m, f.y, 46 * s, P['accent'], sw=2))
        els.append(dict(type='text', x=round(m + 70 * s), y=round(f.y + 4 * s), width=round(W - 2 * m - 70 * s), text=txt, fontFamily=B, fontSize=round(34 * s), fill=P['muted'], align='left', lineHeight=1.2))
        f.space(70 * s)
    if c.get('cta'):
        p, h, _ = pill(m, H - m - 100 * s, c['cta'], B, 32 * s, P['ink'], P['bg']); els += p
    return els


def r_story(W, H, P, F, c):
    s = W / 1080; m = 90 * s; D, B = F
    els = [E(-W * 0.3, -W * 0.25, W * 0.9, W * 0.9, P['accent2'])]
    y = 260 * s
    if c.get('badge'):
        p, h, _ = pill(m, y, c['badge'], B, 26 * s, P['accent'], P['on']); els += p; y += h + 60 * s
    f = Flow(m, y, W - 2 * m)
    f.text(c['title'], D, (260 if D == 'Bebas Neue' else 160) * s, P['ink'], bold=D != 'Bebas Neue', lh=1.0, max_lines=4, gap=50 * s)
    if c.get('sub'): f.text(c['sub'], B, 52 * s, P['muted'], lh=1.4, max_lines=4)
    block = els[1:] + f.els
    if not c.get('photo'):
        dy = max(0, (H - 300 * s) * 0.46 - (f.y - 260 * s) / 2 - 260 * s)
        shift(block, dy); f.y += dy
    els = els[:1] + block
    if c.get('photo'): els.append(PH(m, f.y + 80 * s, W - 2 * m, min(640 * s, H - f.y - 480 * s), P['accent2'], radius=round(40 * s)))
    if c.get('cta'):
        p, h, w = pill(m, H - 300 * s, c['cta'], B, 40 * s, P['ink'], P['bg']); els += p
        els.append(I('arrow-up', W - m - 90 * s, H - 300 * s, 90 * s, P['ink'], sw=2))
    return els


def r_card(W, H, P, F, c):
    m = 60; D, B = F
    els = [R(0, 0, 24, H, P['accent'])]
    f = Flow(m + 30, m + 10, W * 0.55)
    f.text(c['title'], D, 58, P['ink'], bold=D != 'Bebas Neue', max_lines=1, gap=8)
    f.text(c['sub'], B, 26, P['accent'] if P['accent'] not in ('#ffffff',) else P['muted'], bold=True, max_lines=1)
    els += f.els
    y = H - m - len(c['info']) * 52
    for ic, txt in c['info']:
        els.append(I(ic, m + 30, y, 32, P['accent'], sw=2))
        els.append(dict(type='text', x=m + 80, y=round(y + 2), width=round(W * 0.55), text=txt, fontFamily=B, fontSize=24, fill=P['muted'], align='left', lineHeight=1.2))
        y += 52
    els += [S('hexagon', W - 300, H / 2 - 130, 240, 260, P['accent2']), I(c['icon'], W - 245, H / 2 - 55, 130, P['accent'], sw=1.75)]
    return els


def r_logo(W, H, P, F, c):
    D, B = F
    shape = c.get('shape', 'ellipse')
    els = [S(shape, W / 2 - 230, 170, 460, 460, P['accent'], **({'radius': 110} if shape == 'rect' else {})),
           I(c['icon'], W / 2 - 130, 270, 260, P['on'], sw=1.75)]
    f = Flow(80, 700, W - 160, 'center')
    f.text(c['title'], D, 110 if D == 'Bebas Neue' else 84, P['ink'], bold=D != 'Bebas Neue', max_lines=1, gap=14, ls=4 if D == 'Bebas Neue' else 0)
    f.text(c['sub'].upper(), B, 26, P['muted'], bold=True, max_lines=1, ls=6)
    return els + f.els


def r_slide(W, H, P, F, c):
    m = 120; D, B = F
    els = [E(W * 0.62, -H * 0.25, H * 1.1, H * 1.1, P['accent2']), PH(W * 0.6, H * 0.2, H * 0.62, H * 0.62, P['surface'], mask='circle')] if c.get('photo') else \
          [E(W * 0.62, -H * 0.25, H * 1.1, H * 1.1, P['accent2']), S('star', W * 0.72, H * 0.3, 300, 300, P['accent'])]
    f = Flow(m, H * 0.2, W * 0.5)
    if c.get('kicker'): f.text(c['kicker'].upper(), B, 30, P['accent'], bold=True, max_lines=1, gap=24, ls=4)
    f.text(c['title'], D, 170 if D == 'Bebas Neue' else 124, P['ink'], bold=D != 'Bebas Neue', lh=1.05, max_lines=3, gap=40)
    f.text(c['sub'], B, 44, P['muted'], lh=1.4, max_lines=2)
    els += f.els
    els.append(dict(type='text', x=m, y=H - m - 30, width=round(W * 0.5), text=c['foot'], fontFamily=B, fontSize=28, bold=True, fill=P['ink'], align='left', lineHeight=1.2))
    return els


RECIPES = dict(bold=r_bold, center=r_center, photo=r_photo, promo=r_promo, quote=r_quote, list=r_list, event=r_event,
               story=r_story, card=r_card, logo=r_logo, slide=r_slide)
SIZE = dict(sq=(1080, 1080), story=(1080, 1920), a4=(2480, 3508), card=(1050, 600), logo=(1000, 1000), slide=(1920, 1080), wide=(1200, 630))

# ------------------------------------------------------------------ content table (50 original templates)
# key, name, categories, keywords, size, recipe, palette, fonts, content
T = [
 # promo (6)
 ('summer_sale', 'Summer sale', ['promo', 'social'], 'sale discount summer offer', 'sq', 'promo', 'coral', 'modern', dict(kicker='Summer sale', big='50% OFF', title='Everything must go', sub='This weekend only, in store and online.')),
 ('flash_sale', 'Flash sale', ['promo', 'social'], 'flash sale discount hours deal', 'sq', 'bold', 'black', 'loud', dict(badge='TODAY ONLY', title='FLASH SALE\n24 HOURS', sub='Up to 70% off selected items', cta='Shop now', shape='star')),
 ('new_arrivals', 'New arrivals', ['promo', 'social', 'photo'], 'new arrivals collection fashion shop', 'sq', 'photo', 'sand', 'classic', dict(kicker='Just landed', title='The autumn collection', sub='Soft fabrics, warm colours, made to last.', cta='Explore')),
 ('bogo', 'Buy one get one', ['promo', 'social'], 'buy one get one free bogo offer deal', 'sq', 'center', 'lemon', 'loud', dict(icon='gift', kicker='Limited offer', title='BUY ONE\nGET ONE FREE', sub='On all drinks, every Tuesday.', cta='Visit us')),
 ('free_delivery', 'Free delivery', ['promo', 'story'], 'free delivery shipping order online', 'story', 'story', 'sky', 'modern', dict(badge='THIS WEEK', title='Free delivery on every order', sub='No minimum spend. Order before 9 pm for next-day delivery.', cta='Order now')),
 ('opening_offer', 'Grand opening offer', ['promo', 'poster'], 'grand opening launch store discount', 'a4', 'promo', 'violet', 'modern', dict(kicker='Grand opening', big='30% OFF', title='Our new store is open', sub='Opening week offers on everything. See you there.')),
 # events (5)
 ('workshop', 'Workshop', ['event', 'social'], 'workshop class training learn event', 'sq', 'event', 'violet', 'modern', dict(month='MAR', day='14', kicker='Free workshop', title='Design basics for beginners', info=[('clock', '6:00 – 8:00 pm'), ('map-pin', 'Community Hall, Room 2')], cta='Register')),
 ('webinar', 'Webinar', ['event', 'social'], 'webinar online live talk zoom', 'sq', 'event', 'navy', 'modern', dict(month='APR', day='02', kicker='Live webinar', title='Grow your small business online', info=[('monitor', 'Online · 45 minutes'), ('users', 'Free for everyone')], cta='Save your seat')),
 ('music_night', 'Music night', ['event', 'poster'], 'music concert live night party gig', 'a4', 'bold', 'black', 'loud', dict(badge='LIVE MUSIC', title='ACOUSTIC\nNIGHT', sub='Friday · 8 pm · Free entry', body='Local artists, warm drinks and a cosy crowd. Bring a friend.', cta='See the line-up')),
 ('conference', 'Conference', ['event', 'story'], 'conference summit talks speakers tech', 'story', 'story', 'night', 'modern', dict(badge='MAY 20–21', title='Future of Work Summit', sub='Two days of talks, workshops and new connections.', cta='Get tickets')),
 ('meetup', 'Community meetup', ['event', 'social'], 'meetup community club gathering', 'sq', 'center', 'mint', 'modern', dict(icon='users', kicker='Community meetup', title='Coffee and good conversation', sub='First Saturday of every month. Everyone welcome.', cta='Join us')),
 # hiring (4)
 ('hiring_designer', 'Hiring: designer', ['hiring', 'social'], 'job hiring designer vacancy career', 'sq', 'bold', 'violet', 'modern', dict(badge='WE ARE HIRING', title='Graphic designer', sub='Full-time · Riyadh or remote', body='You love clean layouts, bold colour and working with a friendly team.', cta='Apply now')),
 ('hiring_drivers', 'Hiring: drivers', ['hiring', 'social'], 'job hiring driver delivery vacancy', 'sq', 'center', 'lemon', 'loud', dict(icon='truck', kicker='Now hiring', title='DELIVERY DRIVERS', sub='Flexible shifts, weekly pay and fuel support.', cta='Apply today')),
 ('internship', 'Internship', ['hiring', 'social'], 'internship students graduate program job', 'sq', 'list', 'sky', 'modern', dict(kicker='Summer internship', title='What you will get', items=['Real projects from day one', 'A mentor who has your back', 'A paid 10-week program'], foot='Apply by 30 April')),
 ('join_team_story', 'Join our team (story)', ['hiring', 'story'], 'job hiring team career story', 'story', 'story', 'mint', 'modern', dict(badge='CAREERS', title='Join our team', sub='We are looking for friendly people to help our customers every day.', cta='Apply now', photo=True)),
 # quotes (4)
 ('quote_motivation', 'Motivational quote', ['quote', 'social'], 'quote motivation inspiration', 'sq', 'quote', 'sand', 'classic', dict(title='Small steps every day add up to big results.', sub='Your name', body='@yourhandle')),
 ('testimonial', 'Customer testimonial', ['quote', 'social'], 'testimonial customer review feedback quote', 'sq', 'quote', 'violet', 'modern', dict(title='Fast delivery, friendly team and great quality. We will order again.', sub='Customer name', body='Company or city')),
 ('monday_quote', 'Monday motivation', ['quote', 'social'], 'monday motivation quote week', 'sq', 'center', 'pink', 'classic', dict(icon='sun', kicker='Monday motivation', title='Start where you are. Use what you have.', sub='Have a great week, everyone.')),
 ('founder_quote', 'Founder quote', ['quote', 'social'], 'founder ceo quote leadership', 'sq', 'quote', 'navy', 'classic', dict(title='We started with one idea: make good design free for everyone.', sub='Founder name', body='Founder, Your Company')),
 # tips (5)
 ('tips_productivity', '5 productivity tips', ['tips', 'social'], 'tips productivity list advice', 'sq', 'list', 'mint', 'modern', dict(kicker='Work smarter', title='5 productivity tips', items=['Plan tomorrow tonight', 'Do the hardest task first', 'Batch your emails', 'Take short breaks', 'Say no more often'])),
 ('how_to', 'How-to steps', ['tips', 'social'], 'how to steps guide tutorial', 'sq', 'list', 'violet', 'modern', dict(kicker='Quick guide', title='How to brew better coffee', items=['Use freshly ground beans', 'Heat water to 93 °C', 'Brew for four minutes'], foot='Save this for later')),
 ('did_you_know', 'Did you know?', ['tips', 'social'], 'did you know fact trivia', 'sq', 'center', 'sky', 'modern', dict(icon='lightbulb', kicker='Did you know?', title='Honey never spoils.', sub='Archaeologists have found pots of honey over 3,000 years old that are still good to eat.')),
 ('checklist', 'Checklist', ['tips', 'social'], 'checklist todo list tasks', 'sq', 'list', 'lemon', 'modern', dict(kicker='Before you post', title='Your social checklist', items=['Clear headline', 'One call to action', 'Brand colours', 'Proofread twice'], checks=True)),
 ('faq', 'FAQ', ['tips', 'story'], 'faq questions answers help', 'story', 'list', 'coral', 'modern', dict(kicker='You asked', title='Frequently asked questions', items=['Do you deliver? Yes, citywide.', 'Opening hours? 9 am – 11 pm daily.', 'Can I return items? Within 14 days.', 'Gift cards? Available in store.'], foot='More questions? Send us a message')),
 # food (5)
 ('menu_special', 'Menu special', ['food', 'social', 'photo'], 'menu special dish restaurant food', 'sq', 'photo', 'coral', 'classic', dict(kicker="Chef's special", title='Grilled salmon bowl', sub='Fresh salmon, rice, avocado and sesame dressing.', price='45 SAR')),
 ('coffee_promo', 'Coffee promo', ['food', 'social'], 'coffee cafe drink promo latte', 'sq', 'center', 'sand', 'classic', dict(icon='coffee', kicker='Morning deal', title='Any coffee + croissant', sub='Only 18 SAR before 11 am.', cta='See you soon')),
 ('new_dish', 'New on the menu', ['food', 'story', 'photo'], 'new dish menu restaurant food story', 'story', 'story', 'forest', 'classic', dict(badge='NEW', title='Something new on the menu', sub='Slow-cooked lamb with saffron rice. Try it this week.', cta='Book a table', photo=True)),
 ('breakfast', 'Breakfast deal', ['food', 'social'], 'breakfast deal morning restaurant', 'sq', 'promo', 'lemon', 'modern', dict(kicker='Breakfast deal', big='2 FOR 1', title='Weekend breakfast', sub='Saturday and Sunday, 8 am to noon.')),
 ('bakery', 'Bakery', ['food', 'social', 'photo'], 'bakery bread cake pastry fresh', 'sq', 'photo', 'pink', 'classic', dict(kicker='Fresh every morning', title='Baked with love', sub='Sourdough, pastries and cakes made in house.', cta='Order ahead', mask='arch')),
 # real estate (4)
 ('just_listed', 'Just listed', ['realestate', 'social', 'photo'], 'real estate just listed home apartment property', 'sq', 'photo', 'navy', 'modern', dict(kicker='Just listed', title='3-bedroom family home', sub='Garden, parking and close to schools.', price='Call for price')),
 ('open_house', 'Open house', ['realestate', 'social'], 'real estate open house viewing property', 'sq', 'event', 'sand', 'classic', dict(month='JUN', day='08', kicker='Open house', title='Come and see your next home', info=[('clock', '10 am – 2 pm'), ('map-pin', 'Al Olaya, Riyadh')], cta='Book a viewing')),
 ('for_rent', 'For rent', ['realestate', 'poster', 'photo'], 'for rent apartment flat property', 'a4', 'photo', 'mint', 'modern', dict(kicker='For rent', title='Bright 2-bedroom apartment', sub='Furnished, balcony, 10 minutes to the metro.', price='Contact us')),
 ('sold', 'Sold', ['realestate', 'social'], 'sold real estate property congrats', 'sq', 'center', 'black', 'loud', dict(icon='key', kicker='Congratulations', title='SOLD!', sub='Another happy family in their new home.')),
 # business (8)
 ('card_modern', 'Business card: modern', ['business'], 'business card contact modern', 'card', 'card', 'violet', 'modern', dict(title='Your Name', sub='Product Designer', icon='pen-tool', info=[('phone', '+966 50 000 0000'), ('mail', 'hello@yourname.com'), ('globe', 'yourname.com')])),
 ('card_dark', 'Business card: dark', ['business'], 'business card contact dark', 'card', 'card', 'night', 'classic', dict(title='Your Name', sub='Consultant', icon='briefcase', info=[('phone', '+966 50 000 0000'), ('mail', 'name@company.com'), ('map-pin', 'Riyadh, Saudi Arabia')])),
 ('card_fresh', 'Business card: fresh', ['business'], 'business card contact green', 'card', 'card', 'mint', 'modern', dict(title='Green Leaf Café', sub='Coffee · Breakfast · Brunch', icon='coffee', info=[('phone', '+966 11 000 0000'), ('globe', 'greenleaf.cafe')])),
 ('logo_leaf', 'Logo: leaf', ['business'], 'logo brand leaf nature', 'logo', 'logo', 'mint', 'modern', dict(title='Green Leaf', sub='Café & bakery', icon='leaf', shape='ellipse')),
 ('logo_bold', 'Logo: bold', ['business'], 'logo brand bold studio', 'logo', 'logo', 'black', 'loud', dict(title='NORTH STUDIO', sub='Design & print', icon='compass', shape='rect')),
 ('slide_title', 'Presentation title', ['business'], 'presentation slide title deck', 'slide', 'slide', 'violet', 'modern', dict(kicker='Quarterly review', title='Q3 results and next steps', sub='What went well, what we learned and where we go next.', foot='Your Name · October')),
 ('slide_pitch', 'Pitch deck cover', ['business'], 'presentation pitch deck startup investor', 'slide', 'slide', 'night', 'modern', dict(kicker='Seed round', title='Making design free for everyone', sub='A short introduction for partners and investors.', foot='Your Company · 2026', photo=True)),
 ('thank_you', 'Thank you post', ['business', 'social'], 'thank you customers followers milestone', 'sq', 'center', 'violet', 'classic', dict(icon='heart', kicker='10,000 followers', title='Thank you for being here', sub='We could not do it without you.')),
 # seasonal (6)
 ('ramadan_en', 'Ramadan Kareem', ['seasonal', 'social'], 'ramadan kareem islamic month greeting', 'sq', 'center', 'night', 'classic', dict(icon='moon-star', kicker='Ramadan Kareem', title='Wishing you a blessed month', sub='From all of us at Your Company.')),
 ('ramadan_hours', 'Ramadan hours', ['seasonal', 'story'], 'ramadan opening hours timings iftar suhoor', 'story', 'list', 'night', 'modern', dict(kicker='Ramadan', title='Our opening hours', items=['Sat – Thu: 8 pm – 2 am', 'Friday: 9 pm – 3 am', 'Iftar boxes: order by 4 pm'], foot='Ramadan Kareem from our team')),
 ('eid_mubarak', 'Eid Mubarak', ['seasonal', 'social'], 'eid mubarak greeting celebration', 'sq', 'center', 'forest', 'classic', dict(icon='sparkles', kicker='Eid Mubarak', title='Joy, peace and togetherness', sub='Wishing you and your family a happy Eid.')),
 ('national_day', 'Saudi National Day', ['seasonal', 'social'], 'saudi national day september celebration ksa', 'sq', 'center', 'green', 'modern', dict(icon='star', kicker='23 September', title='Happy Saudi National Day', sub='Proud of our home. Celebrating together.')),
 ('white_friday', 'White Friday sale', ['seasonal', 'promo', 'social'], 'white friday black friday sale november', 'sq', 'promo', 'black', 'loud', dict(kicker='White Friday', big='UP TO 70%', title='Our biggest sale of the year', sub='Starts Thursday at midnight. While stocks last.')),
 ('new_year', 'Happy New Year', ['seasonal', 'social'], 'new year celebration greeting', 'sq', 'center', 'night', 'loud', dict(icon='party-popper', kicker='Hello, 2027', title='HAPPY NEW YEAR', sub='Thank you for an amazing year.')),
 # product / announcements (3)
 ('product_launch', 'Product launch', ['promo', 'social', 'photo'], 'product launch new release', 'sq', 'photo', 'sky', 'modern', dict(kicker='Introducing', title='The new Shoof bottle', sub='Keeps drinks cold for 24 hours.', price='79 SAR', mask='blob')),
 ('coming_soon', 'Coming soon', ['promo', 'story'], 'coming soon launch teaser countdown', 'story', 'story', 'black', 'loud', dict(badge='STAY TUNED', title='SOMETHING NEW IS COMING', sub='Turn on notifications so you don’t miss it.', cta='Follow us')),
 ('giveaway', 'Giveaway', ['promo', 'social'], 'giveaway contest win prize', 'sq', 'list', 'pink', 'modern', dict(kicker='Giveaway', title='Win a gift box worth 500 SAR', items=['Follow our account', 'Like this post', 'Tag two friends'], foot='Winner announced Friday')),
]

CAT_ORDER = ['promo', 'event', 'hiring', 'quote', 'tips', 'food', 'realestate', 'business', 'seasonal']


def build():
    out, keys = [], set()
    for key, name, cats, kw, size, recipe, pal, fonts, content in T:
        assert key not in keys, key; keys.add(key)
        W, H = SIZE[size]; P = PAL[pal]
        els = [e for e in RECIPES[recipe](W, H, P, FONTS[fonts], content)]
        bg = {'color': P['bg'], 'image': None}
        out.append(dict(key=key, name=name, cats=cats, kw=kw, w=W, h=H, bg=P['bg'], els=els))
    return out


def render_block(data):
    js = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    return (START + ' — built by tools/templates/gen_templates.py from its style spec + content table; edit the generator, not this block */\n'
            'const GEN_TEMPLATES=' + js + ';\n' + END)


def main():
    data = build()
    assert len(data) == 50, len(data)
    src = open(INDEX, encoding='utf-8').read()
    i, j = src.index(START), src.index(END) + len(END)
    new = src[:i] + render_block(data) + src[j:]
    if '--check' in sys.argv:
        if new != src:
            sys.exit('index.html is out of date: run python3 tools/templates/gen_templates.py')
        print('templates up to date'); return
    open(INDEX, 'w', encoding='utf-8').write(new)
    print(f'wrote {len(data)} templates')


if __name__ == '__main__':
    main()
