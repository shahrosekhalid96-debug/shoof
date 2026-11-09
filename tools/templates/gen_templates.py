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
import json, math, os, re, sys  # noqa

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
      ('Bebas Neue', True): 0.47, ('Bebas Neue', False): 0.47, ('Playfair Display', True): 0.58, ('Playfair Display', False): 0.53}


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
    longest = max(len(w) for w in re.split(r'[ \n]+', text) if w)
    size = min(size, width / (longest * CW[(font, bold)] * 1.1))
    while size > 10 and lines(text, font, size, width, bold) > max_lines:
        size *= 0.94
    return round(size)


# ------------------------------------------------------------------ element helpers
def R(x, y, w, h, fill, **kw): return dict(type='rect', x=round(x), y=round(y), width=round(w), height=round(h), fill=fill, **kw)
def E(x, y, w, h, fill, **kw): return dict(type='ellipse', x=round(x), y=round(y), width=round(w), height=round(h), fill=fill, **kw)
def S(kind, x, y, w, h, fill, **kw): return dict(type=kind, x=round(x), y=round(y), width=round(w), height=round(h), fill=fill, **kw)
def I(name, x, y, sz, color, sw=2, fill=''): return dict(type='icon', icon=name, x=round(x), y=round(y), width=round(sz), height=round(sz), stroke=color, strokeWidth=sw, fill=fill)
def PAT(kind, x, y, w, h, fill, opacity, spacing, **kw): return dict(type='pattern', pattern=kind, x=round(x), y=round(y), width=round(w), height=round(h), fill=fill, opacity=opacity, spacing=round(spacing), **kw)


# subtle texture per recipe: gives posters depth without competing with the text
def deco(recipe, W, H, P):
    s = min(W, H) / 1080
    return {
        'bold':   lambda: PAT('dotsRadial', W * 0.52, H - W * 0.5, W * 0.62, W * 0.62, P['accent'], 0.28, 26 * s),
        'center': lambda: PAT('dotsEdges', 0, 0, W, H, P['ink'], 0.08, 24 * s),
        'story':  lambda: PAT('waves', 0, H * 0.55, W, H * 0.45, P['accent'], 0.14, 26 * s),
        'promo':  lambda: PAT('dotGrid', 0, 0, W, H * 0.6, P['ink'], 0.12, 30 * s),
        'quote':  lambda: PAT('contours', W * 0.5, H * 0.5, W * 0.8, W * 0.8, P['accent'], 0.18, 30 * s),
        'photo':  lambda: PAT('dotsFade', W * 0.55, 0, W * 0.45, H * 0.3, P['accent'], 0.22, 22 * s),
        'event':  lambda: PAT('dotsArrow', W * 0.64, H * 0.07, W * 0.28, W * 0.28, P['accent'], 0.4, 20 * s),
        'list':   lambda: PAT('stripesFade', W * 0.7, 0, W * 0.3, H * 0.32, P['accent'], 0.14, 18 * s),
        'slide':  lambda: PAT('dotsRing', W * 0.6, H * 0.06, H * 0.88, H * 0.88, P['ink'], 0.12, 22 * s),
    }.get(recipe, lambda: None)()


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
    els.append(R(46 * s, 46 * s, W - 92 * s, H - 92 * s, '', radius=round(36 * s), stroke=P['accent'], strokeWidth=round(4 * s), opacity=0.55))
    y = m + 50 * s
    if c.get('icon'):
        els += [E(W / 2 - 90 * s, y - 20 * s, 180 * s, 180 * s, P['surface'], shadowColor='#000000', shadowBlur=round(24 * s), shadowY=round(8 * s), shadowOpacity=0.1),
                I(c['icon'], W / 2 - 55 * s, y + 15 * s, 110 * s, P['accent'], sw=1.75)]; y += 210 * s
    f = Flow(m, y, W - 2 * m, 'center')
    if c.get('kicker'): f.text(c['kicker'].upper(), B, 30 * s, P['accent'], bold=True, max_lines=1, gap=24 * s, ls=round(4 * s))
    f.text(c['title'], D, (160 if D == 'Bebas Neue' else 104) * s, P['ink'], bold=D != 'Bebas Neue', lh=1.05, max_lines=c['title'].count('\n') + 1 if '\n' in c['title'] else 3, gap=30 * s)
    if c.get('sub'): f.text(c['sub'], B, 38 * s, P['muted'], lh=1.4, max_lines=2)
    els += f.els
    if c.get('cta'):
        p, h, _ = pill(W / 2, max(H - m - 110 * s, f.y + 40 * s), c['cta'], B, 32 * s, P['accent'], P['on'], align='center'); els += p
    return els


def r_photo(W, H, P, F, c):
    """Photo frame on top, text below; the photo shrinks if the text needs room above the bottom pill."""
    s = W / 1080; m = 80 * s; D, B = F
    ph = H * (0.5 if H > W else 0.46)
    bottom = H - m - 90 * s - 30 * s if c.get('cta') else H - m
    for _ in range(3):
        f = Flow(m, m + ph + 60 * s, W - 2 * m)
        if c.get('kicker'): f.text(c['kicker'].upper(), B, 28 * s, P['accent'], bold=True, max_lines=1, gap=18 * s, ls=round(3 * s))
        f.text(c['title'], D, (120 if D == 'Bebas Neue' else 84) * s, P['ink'], bold=D != 'Bebas Neue', lh=1.05, max_lines=2, gap=22 * s)
        if c.get('sub'): f.text(c['sub'], B, 34 * s, P['muted'], lh=1.4, max_lines=2)
        over = f.y - bottom
        if over <= 0: break
        ph = max(H * 0.28, ph - over)
    els = [R(m + 26 * s, m + 26 * s, W - 2 * m, ph, '', radius=round(36 * s), stroke=P['accent'], strokeWidth=round(4 * s)) if not c.get('mask') else E(m + 26 * s, m + 26 * s, W - 2 * m, ph, P['accent2'], opacity=0.5),
           PH(m, m, W - 2 * m, ph, P['accent2'], radius=round(36 * s), **({'mask': c['mask']} if c.get('mask') else {}))]
    els += f.els
    if c.get('price'):
        dd = 210 * s
        els += [E(W - m - dd + 30 * s, m + ph - dd * 0.6, dd, dd, P['accent'], shadowColor='#000000', shadowBlur=round(20 * s), shadowY=round(6 * s), shadowOpacity=0.15)]
        fsz = fit(c['price'], B, 44 * s, dd * 0.78, True, 2)
        els.append(dict(type='text', text=c['price'], x=round(W - m - dd + 30 * s + dd * 0.11), y=round(m + ph - dd * 0.6 + dd / 2 - lines(c['price'], B, fsz, dd * 0.78, True) * fsz * 0.6), width=round(dd * 0.78), fontFamily=B, fontSize=fsz, bold=True, fill=P['on'], align='center', lineHeight=1.2))
        if c.get('cta'):
            p, h, _ = pill(m, H - m - 90 * s, c['cta'], B, 30 * s, P['ink'], P['bg']); els += p
    elif c.get('cta'):
        p, h, _ = pill(m, H - m - 90 * s, c['cta'], B, 30 * s, P['ink'], P['bg']); els += p
    return els


def r_promo(W, H, P, F, c):
    """Big offer number, a round product photo with a star sticker, and a colour band with the message and button."""
    s = W / 1080; m = 80 * s; D, B = F
    tall = H > W * 1.2
    split = 0.6 if tall else 0.6
    d = (420 if tall else 400) * s
    els = [R(0, H * split, W, H * (1 - split), P['accent2']),
           E(W - m - d + 30 * s, H * split - d - 6 * s, d, d, '', stroke=P['accent'], strokeWidth=round(4 * s)),
           PH(W - m - d, H * split - d - 30 * s, d, d, P['surface'], mask='circle'),
           S('star', W - m - d - 40 * s, H * split - d - 70 * s, 200 * s, 200 * s, P['accent']),
           dict(type='text', text=c.get('sticker', 'HOT'), x=round(W - m - d - 40 * s), y=round(H * split - d - 70 * s + 76 * s), width=round(200 * s), fontFamily='Bebas Neue', fontSize=round(50 * s), fill=P['on'], align='center', lineHeight=1.0)]
    f = Flow(m, m, W - 2 * m - d - 20 * s)
    if c.get('kicker'): f.text(c['kicker'].upper(), B, 32 * s, P['ink'], bold=True, max_lines=1, gap=14 * s, ls=round(4 * s))
    f.text(c['big'].replace(' ', '\u00a0') if len(c['big']) <= 8 and not tall else c['big'], 'Bebas Neue', (380 if tall else 250) * s, P['accent'], lh=0.92, max_lines=2, gap=0)
    els += f.els
    f2 = Flow(m, H * split + 60 * s, W - 2 * m)
    f2.text(c['title'], D, (110 if D == 'Bebas Neue' else 76) * s, P['ink'], bold=D != 'Bebas Neue', lh=1.05, max_lines=2, gap=18 * s)
    if c.get('sub'): f2.text(c['sub'], B, 32 * s, P['muted'], lh=1.4, max_lines=2)
    els += f2.els
    if c.get('cta'):
        p, h, w = pill(W - m, H * split - 36 * s, c['cta'], B, 30 * s, P['ink'], P['bg']); p[0]['x'] = round(W - m - w); p[1]['x'] = round(W - m - w); els += p
    return els


def r_quote(W, H, P, F, c):
    """Floating card with a quote mark badge, serif quote, avatar slot and name; contour texture behind."""
    s = W / 1080; m = 70 * s; D, B = F
    els = [PAT('contours', W * 0.35, -W * 0.25, W * 0.95, W * 0.95, P['accent'], 0.22, 30 * s),
           R(m, m, W - 2 * m, H - 2 * m, P['surface'], radius=round(44 * s), shadowColor='#000000', shadowBlur=round(40 * s), shadowY=round(14 * s), shadowOpacity=0.12),
           R(m, m + 120 * s, 14 * s, 260 * s, P['accent'], radius=round(7 * s)),
           E(m + 80 * s, m + 70 * s, 130 * s, 130 * s, P['accent']),
           I('quote', m + 113 * s, m + 103 * s, 64 * s, P['on'], sw=1.5, fill=P['on'])]
    f = Flow(m + 80 * s, m + 250 * s, W - 2 * m - 160 * s)
    f.text(c['title'], 'Playfair Display', 70 * s, P['ink'], lh=1.3, max_lines=6)
    els += f.els
    ay = max(f.y + 60 * s, H - m - 210 * s)
    els += [PH(m + 80 * s, ay, 120 * s, 120 * s, P['accent2'], mask='circle'),
            dict(type='text', x=round(m + 230 * s), y=round(ay + 22 * s), width=round(W - 2 * m - 320 * s), text=c['sub'], fontFamily=B, fontSize=round(34 * s), bold=True, fill=P['ink'], align='left', lineHeight=1.2)]
    if c.get('body'):
        els.append(dict(type='text', x=round(m + 230 * s), y=round(ay + 70 * s), width=round(W - 2 * m - 320 * s), text=c['body'], fontFamily=B, fontSize=round(26 * s), fill=P['muted'], align='left', lineHeight=1.2))
    return els


def r_list(W, H, P, F, c):
    """Coloured header band with a watermark icon, then floating cards with number (or check) badges on a connector line."""
    s = W / 1080; m = 80 * s; D, B = F
    tall = H > W * 1.4
    band = H * (0.30 if tall else 0.40)
    on = P['on']
    els = [R(0, 0, W, band, P['accent']),
           PAT('dotGrid', 0, 0, W, band, on, 0.16, 28 * s),
           I(c.get('icon', 'sparkles'), W - m - 300 * s, band - 330 * s, 300 * s, on, sw=1.25)]
    els[-1]['opacity'] = 0.22
    f = Flow(m, m + 10 * s, W - 2 * m - 200 * s)
    if c.get('kicker'): f.text(c['kicker'].upper(), B, 28 * s, on, bold=True, max_lines=1, gap=18 * s, ls=round(4 * s))
    f.text(c['title'], D, (130 if D == 'Bebas Neue' else 80) * s, on, bold=D != 'Bebas Neue', lh=1.05, max_lines=2)
    over = f.y - (band - 70 * s)
    if over > 0:
        band += over; els[0]['height'] = round(band); els[1]['height'] = round(band); els[2]['y'] = round(band - 330 * s)
    els += f.els
    items = c['items']; n = len(items)
    foot_h = 90 * s if c.get('foot') else 0
    top = band - 50 * s
    avail = H - top - m - foot_h - 20 * s
    gap = 22 * s
    ch = min((avail - gap * (n - 1)) / n, (280 if tall else 150) * s)
    if tall and n > 1: gap = min(70 * s, max(gap, (avail - n * ch) / (n - 1)))
    d = min(ch * 0.56, (110 if tall else 84) * s)
    els.append(S('line', m + 34 * s + d / 2 - 3 * s, top + ch / 2, 6 * s, (n - 1) * (ch + gap), P['accent2']))
    for k, it in enumerate(items):
        y = top + k * (ch + gap)
        els.append(R(m, y, W - 2 * m, ch, P['surface'], radius=round(26 * s), shadowColor='#000000', shadowBlur=round(28 * s), shadowY=round(8 * s), shadowOpacity=0.1))
        bx, by = m + 34 * s, y + (ch - d) / 2
        if c.get('checks'):
            els += [E(bx, by, d, d, P['accent']), I('check', bx + d * 0.2, by + d * 0.2, d * 0.6, on, sw=3)]
        else:
            els += [E(bx, by, d, d, P['accent']), dict(type='text', x=round(bx), y=round(by + d * 0.2), width=round(d), text=str(k + 1), fontFamily=B, fontSize=round(d * 0.5), bold=True, fill=on, align='center', lineHeight=1.2)]
        tx = bx + d + 30 * s; tw = W - m - 30 * s - tx
        fs = fit(it, B, (54 if tall else 36) * s, tw, True, 2); nl = lines(it, B, fs, tw, True)
        els.append(dict(type='text', x=round(tx), y=round(y + ch / 2 - nl * fs * 1.25 / 2), width=round(tw), text=it, fontFamily=B, fontSize=fs, bold=True, fill=P['ink'], align='left', lineHeight=1.25))
    if c.get('foot'):
        p, h, w = pill(W / 2, H - m - foot_h + 10 * s, c['foot'], B, 28 * s, P['accent2'], P['ink'], align='center'); els += p
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
    """Big headline up top, then a floating card (tilted card behind it) holding the message and the button."""
    s = W / 1080; m = 90 * s; D, B = F
    els = [E(-W * 0.3, -W * 0.25, W * 0.9, W * 0.9, P['accent2'])]
    y = 230 * s
    if c.get('badge'):
        p, h, _ = pill(m, y, c['badge'], B, 26 * s, P['accent'], P['on']); els += p; y += h + 50 * s
    f = Flow(m, y, W - 2 * m)
    f.text(c['title'], D, (250 if D == 'Bebas Neue' else 150) * s, P['ink'], bold=D != 'Bebas Neue', lh=1.0, max_lines=4, gap=60 * s)
    els += f.els
    card_y = f.y
    if c.get('photo'):
        ph = min(560 * s, H - card_y - 760 * s)
        els += [R(m + 30 * s, card_y + 24 * s, W - 2 * m, ph, P['accent'], radius=round(40 * s), rotation=3), PH(m, card_y, W - 2 * m, ph, P['accent2'], radius=round(40 * s))]
        card_y += ph + 70 * s
    f2 = Flow(m + 60 * s, 0, W - 2 * m - 120 * s)
    if c.get('sub'): f2.text(c['sub'], B, 46 * s, P['ink'], lh=1.4, max_lines=4)
    ch = f2.y + 120 * s + (190 * s if c.get('cta') else 0)
    card_y = card_y + max(0, (H - 160 * s - card_y - ch) / 2)
    els.append(RR(W / 2, card_y + ch / 2 + 20 * s, W - 2 * m - 40 * s, ch, -4, P['accent'], radius=round(40 * s), opacity=0.35))
    els.append(R(m, card_y, W - 2 * m, ch, P['surface'], radius=round(40 * s), shadowColor='#000000', shadowBlur=round(40 * s), shadowY=round(14 * s), shadowOpacity=0.12))
    for e in f2.els: e['y'] = round(e['y'] + card_y + 60 * s)
    els += f2.els
    if c.get('cta'):
        p, h, w = pill(m + 60 * s, card_y + ch - 160 * s, c['cta'], B, 40 * s, P['accent'], P['on']); els += p
        els += [E(W - m - 160 * s, card_y + ch - 165 * s, 100 * s, 100 * s, P['ink']), I('arrow-right', W - m - 135 * s, card_y + ch - 140 * s, 50 * s, P['bg'], sw=2.5)]
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


# ------------------------------------------------------------------ editorial posters (hand-composed, original)
def TX(text, x, y, w, font, size, color, bold=False, align='left', lh=1.15, ls=0, **kw):
    e = dict(type='text', text=text, x=round(x), y=round(y), width=round(w), fontFamily=font, fontSize=round(size), bold=bold, fill=color, align=align, lineHeight=lh)
    if ls: e['letterSpacing'] = ls
    e.update(kw); return e


def RR(cx, cy, w, h, deg, fill, **kw):
    """rect rotated about its own centre (Shoof rotates about the top-left corner)"""
    a = math.radians(deg)
    x = cx - (w / 2 * math.cos(a) - h / 2 * math.sin(a)); y = cy - (w / 2 * math.sin(a) + h / 2 * math.cos(a))
    return R(x, y, w, h, fill, rotation=deg, **kw)


def GR(a, b, angle=45, kind='linear'):
    g = dict(type=kind, stops=[dict(offset=0, color=a), dict(offset=1, color=b)])
    if kind == 'linear': g['angle'] = angle
    return g


def p_editorial(W, H, P, F, c):
    red = '#c8374c'; ink = '#161616'
    return [R(560, 900, 1360, 1900, red),
            E(330, 600, 900, 900, '#888888', fillGradient=GR('#2e2e2e', '#ffffff', 300)),
            PH(700, 520, 1080, 2520, '#d8d4d5'),
            E(1330, 2330, 520, 520, '#888888', fillGradient=GR('#ffffff', '#2e2e2e', 300)),
            RR(1240, 1760, 330, 3700, 33, red, opacity=0.9),
            TX('WEAR\nTHE\nCOLOUR', 300, 1180, 1900, 'Poppins', 300, '', bold=True, lh=1.0, ls=12, stroke=ink, strokeWidth=7),
            TX('INSTAGRAM\n@YOURSTUDIO', 120, 110, 900, 'Poppins', 46, ink, bold=True, lh=1.15, ls=4),
            TX('STUDIO', 1660, 120, 700, 'Bebas Neue', 96, ink, align='right', ls=10),
            I('x', 300, 1520, 70, red, sw=3), I('x', 2080, 2560, 70, red, sw=3),
            R(400, 360, 150, 46, '', stroke=ink, strokeWidth=4), R(2100, 2920, 46, 150, '', stroke=ink, strokeWidth=4),
            TX('WWW.YOURWEBSITE.COM', 120, 2600, 1300, 'Poppins', 40, ink, bold=True, ls=10, rotation=-90),
            TX('WWW.YOURWEBSITE.COM', 2360, 900, 1300, 'Poppins', 40, ink, bold=True, ls=10, rotation=90),
            TX('PEOPLE · VOL 4', 120, 3290, 1200, 'Poppins', 64, ink, ls=8),
            TX('02', 1960, 3270, 400, 'Poppins', 96, ink, bold=True, align='right')]


def p_passion(W, H, P, F, c):
    teal = '#3f9fb5'
    els = [R(0, 1300, W, 620, teal)]
    for i in range(3): els.append(RR(60 + i * 150, 120 + i * 40, 70, 1100, 40, '#ffffff'))
    for i in range(4): els.append(RR(780 + i * 140, 1580 + i * 20, 70, 1200, 40, '#ffffff'))
    els += [TX('Do it with', 90, 560, 900, 'Inter', 72, '#ffffff', align='center', ls=8),
            TX('passion', 90, 670, 900, 'Playfair Display', 190, teal, bold=True, align='center', lh=1.05, italic=True),
            TX('or not at all', 90, 900, 900, 'Inter', 72, '#ffffff', align='center', ls=8)]
    return els


def p_cinematic(W, H, P, F, c):
    gold = '#e9d8b8'
    return [PH(0, 0, W, H, '#2a2e35'),
            R(0, 0, W, H, '#0d0f12', fillGradient=GR('#0d0f1200', '#0d0f12ff', 90), opacity=0.95),
            R(0, 0, W, 900, '#0d0f12', fillGradient=GR('#0d0f12cc', '#0d0f1200', 90)),
            TX('WHAT YOU\nLEAVE BEHIND\nFOLLOWS YOU', 340, 330, 1800, 'Bebas Neue', 200, '#ffffff', align='center', lh=0.95, ls=6),
            TX('ECHOES', 140, 2560, 2200, 'Playfair Display', 400, gold, align='center', lh=1.0, ls=60),
            TX('A FILM BY YOUR NAME', 140, 3070, 2200, 'Inter', 56, gold, bold=True, align='center', ls=24),
            TX('IN CINEMAS THIS WINTER', 140, 3190, 2200, 'Inter', 40, '#a9a39a', align='center', ls=16)]


def p_swiss(W, H, P, F, c):
    ink = '#111111'
    names = ['Lina Haddad', 'Omar Siddiqui', 'Mei Tanaka', 'Jonas Berg', 'Amira Nasser', 'Carlos Rivera', 'Sara Lindqvist', 'Yusuf Kaya']
    return [TX('TYPE\nFACE\nFEST', 150, 200, 2300, 'Inter', 800, ink, bold=True, lh=0.84, ls=-30),
            TX('A weekend of type,\nposters and print', 1480, 2330, 900, 'Inter', 70, ink, bold=True, lh=1.15),
            TX('14–15 March 2026\n10:00 – 18:00', 1480, 2550, 900, 'Inter', 60, ink, lh=1.25),
            TX('\n'.join(names), 1480, 2770, 900, 'Inter', 44, ink, bold=True, lh=1.22),
            TX('Main Hall\nCity Design School\n\nFree entry\nRegister online', 150, 2900, 700, 'Inter', 38, ink, bold=True, lh=1.25),
            R(150, 2780, 120, 14, '#ff3b1f')]


def p_geo(W, H, P, F, c):
    return [R(0, 0, W, H, '#202227', fillGradient=GR('#5a5d68', '#16171b', 0, 'radial')),
            PAT('contours', -300, 1200, 1800, 1800, '#ffffff', 0.08, 40),
            S('triangle', -200, 1650, 1700, 1500, '#3a3d46', fillGradient=GR('#6b6f7c', '#1c1d22', 90)),
            S('triangle', 1000, 1350, 1700, 1800, '#2f323a', fillGradient=GR('#8a8e9b', '#16171b', 90)),
            E(780, 380, 960, 960, '#ffffff', opacity=0.14),
            E(1350, 820, 520, 520, '#ffffff', opacity=0.22),
            E(1180, 120, 160, 160, '', stroke='#ffffff', strokeWidth=5),
            dict(type='icon', icon='moon-star', x=1210, y=150, width=100, height=100, stroke='#ffffff', strokeWidth=1.5, fill=''),
            *[E(1235, 760 + i * 110, 50 - i * 8, 50 - i * 8, '#ffffff') for i in range(4)],
            E(230, 1250, 240, 240, '#111216', stroke='#ffffff', strokeWidth=4),
            TX('18+', 230, 1320, 240, 'Poppins', 80, '#ffffff', bold=True, align='center', lh=1.2),
            E(1990, 1720, 300, 300, '#111216', stroke='#ffffff', strokeWidth=4),
            TX('$15\nTICKETS', 1990, 1790, 300, 'Poppins', 54, '#ffffff', bold=True, align='center', lh=1.15),
            TX('NIGHTFALL', 140, 2450, 2200, 'Poppins', 240, '#ffffff', align='center', lh=1.1, ls=40),
            R(540, 2770, 1400, 6, '#ffffff'),
            TX('SATURDAY 5 JULY · 10 PM – LATE', 140, 2820, 2200, 'Poppins', 70, '#ffffff', bold=True, align='center', ls=6),
            TX('Line-up: DJ Nova · Sahara Sound · The Lows · Echo Park', 140, 2990, 2200, 'Inter', 50, '#d6d7dc', align='center'),
            TX('Rooftop 21, King Road · Tickets at the door or online', 140, 3290, 2200, 'Inter', 38, '#a9abb3', align='center')]


def p_halftone(W, H, P, F, c):
    ink = '#111111'
    return [R(0, 0, W, H, '#ffd23f'),
            PAT('dotsRadial', 140, 760, 2200, 2200, ink, 0.9, 64),
            E(640, 1260, 1200, 1200, '#ffd23f'),
            TX('LOUD\nSUMMER', 640, 1480, 1200, 'Bebas Neue', 360, ink, align='center', lh=0.9, ls=6),
            TX('MUSIC FESTIVAL · 2026', 140, 200, 2200, 'Poppins', 90, ink, bold=True, align='center', ls=20),
            TX('20–22 JUNE · CITY PARK · ALL DAY', 140, 3200, 2200, 'Poppins', 70, ink, bold=True, align='center', ls=8)]


# ------------------------------------------------------------------ pitch decks (1920×1080, several slides)
def d_swiss():
    ink, red, mut, bg = '#111111', '#ff3b1f', '#6b6b6b', '#f4f3f0'
    lab = lambda t, x=120: TX(t, x, 90, 900, 'Inter', 24, ink, bold=True, ls=6)
    foot = lambda n: [TX('YOUR COMPANY', 120, 980, 600, 'Inter', 20, mut, bold=True, ls=6), TX(f'{n:02d}', 1700, 975, 100, 'Inter', 22, mut, bold=True, align='right')]
    s1 = [lab('SERIES A PITCH'), TX('01', 1280, 70, 520, 'Inter', 300, red, bold=True, align='right', lh=1.0),
          TX('Scaling the', 120, 560, 1200, 'Inter', 120, ink, lh=1.0), TX('future of', 120, 680, 1200, 'Inter', 120, red, lh=1.0), TX('everyday work.', 120, 800, 1300, 'Inter', 120, ink, lh=1.0), *foot(1)]
    s2 = [lab('THE PROBLEM'), TX('Teams lose nine hours a week to busywork.', 120, 220, 1500, 'Inter', 96, ink, lh=1.05),
          *[x for i, (h, b) in enumerate([('01', 'Scattered tools and tabs'), ('02', 'Manual copy and paste'), ('03', 'No single source of truth')]) for x in
            (R(120 + i * 570, 600, 500, 4, ink), TX(h, 120 + i * 570, 640, 500, 'Inter', 64, red, bold=True), TX(b, 120 + i * 570, 740, 480, 'Inter', 40, ink, lh=1.25))], *foot(2)]
    s3 = [lab('YEAR IN REVIEW'), TX('2025', 120, 180, 600, 'Inter', 120, ink), TX('→', 760, 190, 120, 'Inter', 110, red),
          TX('12%', 120, 430, 800, 'Inter', 300, red, lh=1.0), TX('Net revenue growth, quarter on quarter', 130, 760, 700, 'Inter', 34, mut, lh=1.3),
          TX('8.4M', 1000, 430, 800, 'Inter', 300, ink, lh=1.0), TX('Tasks automated for our customers', 1010, 760, 700, 'Inter', 34, mut, lh=1.3), *foot(3)]
    s4 = [lab('OUR SOLUTION'), TX('One calm workspace that does the busywork for you.', 120, 220, 860, 'Inter', 84, ink, lh=1.08),
          TX('Connect your tools once. Shoof-style automations handle the rest, securely and from day one.', 120, 640, 760, 'Inter', 36, mut, lh=1.4),
          PH(1060, 200, 740, 700, '#e3e1dc'), *foot(4)]
    s5 = [lab('ROADMAP'), TX('2026', 120, 170, 600, 'Inter', 160, ink, lh=1.0), R(120, 600, 1680, 4, ink),
          *[x for i, (q, b) in enumerate([('Q1', 'Launch teams plan'), ('Q2', 'Mobile apps'), ('Q3', 'Partner integrations'), ('Q4', 'Enterprise controls')]) for x in
            (E(120 + i * 440, 584, 36, 36, red), TX(q, 120 + i * 440, 660, 400, 'Inter', 56, ink, bold=True), TX(b, 120 + i * 440, 750, 380, 'Inter', 34, mut, lh=1.3))], *foot(5)]
    s6 = [lab('THANK YOU'), TX('Join us in building', 120, 330, 1600, 'Inter', 120, ink, lh=1.0), TX('what comes next.', 120, 460, 1600, 'Inter', 120, red, lh=1.0),
          TX('hello@yourcompany.com  ·  yourcompany.com', 120, 700, 1400, 'Inter', 38, ink, bold=True), *foot(6)]
    return [(bg, x) for x in (s1, s2, s3, s4, s5, s6)]


def d_soft():
    ink, mut = '#141414', '#5a4f48'
    BG = lambda: R(0, 0, 1920, 1080, '#fbe3d0', fillGradient=GR('#ffd2a8', '#fff3ea', 0, 'radial'))
    top = lambda t: [TX('YOUR COMPANY', 100, 70, 600, 'Inter', 20, ink, bold=True, ls=5), TX(t, 1220, 70, 600, 'Inter', 20, ink, bold=True, align='right', ls=5)]
    circ = lambda x, y, d, big, small: [E(x, y, d, d, ink), TX(big, x, y + d * 0.30, d, 'Poppins', d * 0.2, '#ffffff', bold=True, align='center', lh=1.2), TX(small, x, y + d * 0.58, d, 'Inter', d * 0.075, '#e8e2dc', align='center', lh=1.2)]
    s1 = [BG(), *top('PITCH DECK 2026'), TX('INVESTOR\nPITCH DECK', 100, 560, 1100, 'Poppins', 150, ink, lh=1.0), TX('Building the simplest way for small teams to grow.', 100, 900, 900, 'Inter', 34, mut, lh=1.3),
          PH(1180, 170, 640, 640, '#f1d9c6', mask='circle'), S('star', 1120, 140, 90, 90, ink)]
    s2 = [BG(), *top('MARKET'), TX('Market\nopportunity', 100, 180, 800, 'Poppins', 96, ink, lh=1.05), TX('A large, fast-growing market of small businesses that still run on spreadsheets.', 100, 480, 640, 'Inter', 32, mut, lh=1.45),
          *circ(880, 200, 420, '$9B', 'Total market'), *circ(1340, 120, 300, '$3B', 'Serviceable'), *circ(1360, 560, 260, '$450M', 'Our 5-year goal')]
    s3 = [BG(), *top('STRATEGY'), TX('Growth\nstrategy', 100, 180, 700, 'Poppins', 96, ink, lh=1.05),
          *[x for i, (h, b, ic) in enumerate([('Product-led', 'Free plan that invites the whole team.', 'rocket'), ('Partners', 'Bundled with accounting and payroll tools.', 'handshake'), ('Content', 'Templates and guides that rank and convert.', 'book-open')]) for x in
            (E(900, 170 + i * 270, 120, 120, ink), I(ic, 935, 205 + i * 270, 50, '#ffffff', sw=2), TX(h, 1060, 180 + i * 270, 700, 'Poppins', 48, ink, bold=True), TX(b, 1060, 250 + i * 270, 700, 'Inter', 32, mut, lh=1.35))]]
    s4 = [BG(), *top('FINANCIALS'), TX('Revenue\nstreams', 100, 180, 700, 'Poppins', 96, ink, lh=1.05), TX('Subscriptions grow every quarter while churn keeps falling.', 100, 480, 620, 'Inter', 32, mut, lh=1.45),
          dict(type='chart', chartType='bar', values=[1.2, 1.8, 2.6, 3.4, 4.9], labels=['Q1', 'Q2', 'Q3', 'Q4', 'Q5'], fill=ink, textColor=ink, showLabels=True, x=860, y=170, width=960, height=760)]
    s5 = [BG(), *top('TEAM'), TX('Our team', 100, 150, 1000, 'Poppins', 96, ink, lh=1.05),
          *[x for i, (n, r) in enumerate([('Your Name', 'CEO'), ('Team Member', 'CTO'), ('Team Member', 'COO'), ('Team Member', 'Advisor')]) for x in
            (R(100 + i * 440, 360, 400, 600, '#ffffff', radius=28), PH(124 + i * 440, 384, 352, 300, '#f1d9c6', radius=18), TX(n, 124 + i * 440, 720, 352, 'Poppins', 38, ink, bold=True, align='center'), TX(r, 124 + i * 440, 780, 352, 'Inter', 30, mut, align='center'),
             TX('One line about their experience.', 134 + i * 440, 840, 332, 'Inter', 24, mut, align='center', lh=1.35))]]
    s6 = [BG(), *top('THANK YOU'), TX('Thank you', 100, 380, 1200, 'Poppins', 170, ink, lh=1.0), TX('hello@yourcompany.com', 100, 620, 900, 'Inter', 40, mut), S('star', 1500, 380, 220, 220, ink)]
    return [('#fff3ea', x) for x in (s1, s2, s3, s4, s5, s6)]


def d_warm():
    o1, o2, wh, ink, mut = '#ff8a3d', '#e8455a', '#ffffff', '#3a1d14', '#7a5a50'
    BG = lambda: R(0, 0, 1920, 1080, o1, fillGradient=GR(o1, o2, 135))
    hd = lambda t, c=o2: TX(t, 120, 110, 1200, 'Poppins', 84, c, lh=1.05)
    s1 = [BG(), TX('2026', 640, 150, 1180, 'Poppins', 360, '', bold=True, align='right', lh=1.0, stroke='#ffffffaa', strokeWidth=5),
          TX('YOUR COMPANY', 120, 110, 700, 'Inter', 24, wh, bold=True, ls=5), TX('Pitch Deck\nPresentation', 120, 380, 1000, 'Poppins', 120, wh, lh=1.05),
          TX('Turning ideas into scalable business opportunities', 120, 680, 900, 'Inter', 34, '#ffe9df', lh=1.35),
          R(120, 820, 420, 84, wh, radius=42), TX('Start presentation  →', 120, 846, 420, 'Poppins', 30, o2, bold=True, align='center')]
    s2 = [hd('Executive summary'), TX('We help growing teams plan, launch and measure their work in one place.', 120, 260, 760, 'Inter', 38, mut, lh=1.45),
          *[x for i, (h, b, ic) in enumerate([('Vision', 'Make great work simple for every team.', 'target'), ('Mission', 'Remove busywork with smart automation.', 'rocket'), ('Values', 'Clarity, care and craft in everything.', 'heart')]) for x in
            (R(1000, 200 + i * 260, 800, 220, '#fff4ee', radius=28), E(1040, 250 + i * 260, 120, 120, o1, fillGradient=GR(o1, o2, 135)), I(ic, 1075, 285 + i * 260, 50, wh, sw=2),
             TX(h, 1200, 240 + i * 260, 560, 'Poppins', 44, ink, bold=True), TX(b, 1200, 306 + i * 260, 560, 'Inter', 28, mut, lh=1.35))]]
    s3 = [hd('The problem'), PH(120, 280, 760, 640, '#ffe1d3', radius=32),
          *[x for i, (n, b) in enumerate([('68%', 'of teams miss deadlines'), ('45%', 'of time spent on admin'), ('$2.6M', 'lost per year, per 100 staff')]) for x in
            (TX(n, 1000, 270 + i * 230, 700, 'Poppins', 110, o2, bold=True, lh=1.0), TX(b, 1000, 400 + i * 230, 760, 'Inter', 34, mut))]]
    s4 = [hd('Traction & milestones'),
          *[x for i, (q, h, b) in enumerate([('Q1', '1,000 users', 'Public launch'), ('Q2', '$50K MRR', 'First paid plans'), ('Q3', '3 partners', 'Integrations live'), ('Q4', '20K users', 'Series A ready')]) for x in
            (R(120 + i * 430, 300, 390, 560, '#fff4ee', radius=28), R(120 + i * 430, 300, 390, 150, o1, radius=28, fillGradient=GR(o1, o2, 135)), TX(q, 150 + i * 430, 340, 330, 'Poppins', 56, wh, bold=True),
             TX(h, 150 + i * 430, 520, 330, 'Poppins', 46, ink, bold=True, lh=1.15), TX(b, 150 + i * 430, 640, 330, 'Inter', 30, mut, lh=1.35))]]
    s5 = [BG(), PH(1060, 140, 740, 800, '#ffb08a', radius=40), TX("Let's build\nthe future\ntogether", 120, 300, 900, 'Poppins', 110, wh, lh=1.05),
          TX('hello@yourcompany.com  ·  +966 50 000 0000', 120, 760, 900, 'Inter', 32, '#ffe9df')]
    return [(o1, s1), ('#ffffff', s2), ('#ffffff', s3), ('#ffffff', s4), (o1, s5)]


def d_pastel():
    ink, pink, lil = '#141414', '#ffcfc4', '#b9a8ff'
    blob = lambda x, y, w, h, a, b: dict(type='blob', x=x, y=y, width=w, height=h, fill=a, fillGradient=GR(a, b, 45))
    s1 = [blob(1180, -160, 900, 1100, '#ffb3a7', '#9fb6ff'), blob(820, -120, 330, 300, '#ffc6b8', '#a9b8ff'),
          TX('Company Name', 120, 110, 700, 'Inter', 28, ink), TX('Scale-up\nPitch Deck', 120, 380, 1000, 'Inter', 150, ink, lh=1.0),
          TX('Short tagline about your unique selling point.', 120, 900, 700, 'Inter', 26, '#4a4a4a')]
    cols = [['Mission and vision', 'Problem statement', 'Product overview'], ['Business model', 'Market overview', 'Financial projections'], ['Team overview', 'Funding request', 'Call to action']]
    s2 = [blob(980, 120, 1100, 1100, lil, '#d6ccff'), S('star', 1460, 120, 300, 300, ink),
          TX('Key elements of\na pitch deck', 120, 140, 1200, 'Inter', 110, ink, lh=1.05),
          *[TX('\n'.join('•  ' + t for t in col), 120 + i * 560, 560, 520, 'Inter', 38, ink, lh=1.7) for i, col in enumerate(cols)]]
    s3 = [blob(-200, 600, 700, 700, '#ffb3a7', lil), TX('Thank you', 520, 400, 1300, 'Inter', 170, ink, lh=1.0), TX('hello@company.com', 530, 640, 900, 'Inter', 40, '#4a4a4a')]
    return [('#f1ecff', s1), (pink, s2), ('#f1ecff', s3)]


CUSTOM = dict(editorial=p_editorial, passion=p_passion, cinematic=p_cinematic, swiss=p_swiss, geo=p_geo, halftone=p_halftone)
DECKS = dict(swiss=d_swiss, soft=d_soft, warm=d_warm, pastel=d_pastel)
RECIPES = dict(bold=r_bold, center=r_center, photo=r_photo, promo=r_promo, quote=r_quote, list=r_list, event=r_event,
               story=r_story, card=r_card, logo=r_logo, slide=r_slide)
SIZE = dict(sq=(1080, 1080), story=(1080, 1920), a4=(2480, 3508), card=(1050, 600), logo=(1000, 1000), slide=(1920, 1080), wide=(1200, 630))

# ------------------------------------------------------------------ content table (50 original templates)
# key, name, categories, keywords, size, recipe, palette, fonts, content
T = [
 # promo (6)
 ('summer_sale', 'Summer sale', ['promo', 'social'], 'sale discount summer offer', 'sq', 'promo', 'coral', 'modern', dict(cta='Shop now', kicker='Summer sale', big='50% OFF', title='Everything must go', sub='This weekend only, in store and online.')),
 ('flash_sale', 'Flash sale', ['promo', 'social'], 'flash sale discount hours deal', 'sq', 'bold', 'black', 'loud', dict(badge='TODAY ONLY', title='FLASH SALE\n24 HOURS', sub='Up to 70% off selected items', cta='Shop now', shape='star')),
 ('new_arrivals', 'New arrivals', ['promo', 'social', 'photo'], 'new arrivals collection fashion shop', 'sq', 'photo', 'sand', 'classic', dict(kicker='Just landed', title='The autumn collection', sub='Soft fabrics, warm colours, made to last.', cta='Explore')),
 ('bogo', 'Buy one get one', ['promo', 'social'], 'buy one get one free bogo offer deal', 'sq', 'center', 'lemon', 'loud', dict(icon='gift', kicker='Limited offer', title='BUY ONE\nGET ONE FREE', sub='On all drinks, every Tuesday.', cta='Visit us')),
 ('free_delivery', 'Free delivery', ['promo', 'story'], 'free delivery shipping order online', 'story', 'story', 'sky', 'modern', dict(badge='THIS WEEK', title='Free delivery on every order', sub='No minimum spend. Order before 9 pm for next-day delivery.', cta='Order now')),
 ('opening_offer', 'Grand opening offer', ['promo', 'poster'], 'grand opening launch store discount', 'a4', 'promo', 'violet', 'modern', dict(cta='Visit us', kicker='Grand opening', big='30% OFF', title='Our new store is open', sub='Opening week offers on everything. See you there.')),
 # events (5)
 ('workshop', 'Workshop', ['event', 'social'], 'workshop class training learn event', 'sq', 'event', 'violet', 'modern', dict(month='MAR', day='14', kicker='Free workshop', title='Design basics for beginners', info=[('clock', '6:00 – 8:00 pm'), ('map-pin', 'Community Hall, Room 2')], cta='Register')),
 ('webinar', 'Webinar', ['event', 'social'], 'webinar online live talk zoom', 'sq', 'event', 'navy', 'modern', dict(month='APR', day='02', kicker='Live webinar', title='Grow your small business online', info=[('monitor', 'Online · 45 minutes'), ('users', 'Free for everyone')], cta='Save your seat')),
 ('music_night', 'Music night', ['event', 'poster'], 'music concert live night party gig', 'a4', 'bold', 'black', 'loud', dict(badge='LIVE MUSIC', title='ACOUSTIC\nNIGHT', sub='Friday · 8 pm · Free entry', body='Local artists, warm drinks and a cosy crowd. Bring a friend.', cta='See the line-up')),
 ('conference', 'Conference', ['event', 'story'], 'conference summit talks speakers tech', 'story', 'story', 'night', 'modern', dict(badge='MAY 20–21', title='Future of Work Summit', sub='Two days of talks, workshops and new connections.', cta='Get tickets')),
 ('meetup', 'Community meetup', ['event', 'social'], 'meetup community club gathering', 'sq', 'center', 'mint', 'modern', dict(icon='users', kicker='Community meetup', title='Coffee and good conversation', sub='First Saturday of every month. Everyone welcome.', cta='Join us')),
 # hiring (4)
 ('hiring_designer', 'Hiring: designer', ['hiring', 'social'], 'job hiring designer vacancy career', 'sq', 'bold', 'violet', 'modern', dict(badge='WE ARE HIRING', title='Graphic designer', sub='Full-time · Riyadh or remote', body='You love clean layouts, bold colour and working with a friendly team.', cta='Apply now')),
 ('hiring_drivers', 'Hiring: drivers', ['hiring', 'social'], 'job hiring driver delivery vacancy', 'sq', 'center', 'lemon', 'loud', dict(icon='truck', kicker='Now hiring', title='DELIVERY DRIVERS', sub='Flexible shifts, weekly pay and fuel support.', cta='Apply today')),
 ('internship', 'Internship', ['hiring', 'social'], 'internship students graduate program job', 'sq', 'list', 'sky', 'modern', dict(icon='graduation-cap', kicker='Summer internship', title='What you will get', items=['Real projects from day one', 'A mentor who has your back', 'A paid 10-week program'], foot='Apply by 30 April')),
 ('join_team_story', 'Join our team (story)', ['hiring', 'story'], 'job hiring team career story', 'story', 'story', 'mint', 'modern', dict(badge='CAREERS', title='Join our team', sub='We are looking for friendly people to help our customers every day.', cta='Apply now', photo=True)),
 # quotes (4)
 ('quote_motivation', 'Motivational quote', ['quote', 'social'], 'quote motivation inspiration', 'sq', 'quote', 'sand', 'classic', dict(title='Small steps every day add up to big results.', sub='Your name', body='@yourhandle')),
 ('testimonial', 'Customer testimonial', ['quote', 'social'], 'testimonial customer review feedback quote', 'sq', 'quote', 'violet', 'modern', dict(title='Fast delivery, friendly team and great quality. We will order again.', sub='Customer name', body='Company or city')),
 ('monday_quote', 'Monday motivation', ['quote', 'social'], 'monday motivation quote week', 'sq', 'center', 'pink', 'classic', dict(icon='sun', kicker='Monday motivation', title='Start where you are. Use what you have.', sub='Have a great week, everyone.')),
 ('founder_quote', 'Founder quote', ['quote', 'social'], 'founder ceo quote leadership', 'sq', 'quote', 'navy', 'classic', dict(title='We started with one idea: make good design free for everyone.', sub='Founder name', body='Founder, Your Company')),
 # tips (5)
 ('tips_productivity', '5 productivity tips', ['tips', 'social'], 'tips productivity list advice', 'sq', 'list', 'mint', 'modern', dict(icon='zap', kicker='Work smarter', title='5 productivity tips', items=['Plan tomorrow tonight', 'Do the hardest task first', 'Batch your emails', 'Take short breaks', 'Say no more often'])),
 ('how_to', 'How-to steps', ['tips', 'social'], 'how to steps guide tutorial', 'sq', 'list', 'violet', 'modern', dict(icon='coffee', kicker='Quick guide', title='How to brew better coffee', items=['Use freshly ground beans', 'Heat water to 93 °C', 'Brew for four minutes'], foot='Save this for later')),
 ('did_you_know', 'Did you know?', ['tips', 'social'], 'did you know fact trivia', 'sq', 'center', 'sky', 'modern', dict(icon='lightbulb', kicker='Did you know?', title='Honey never spoils.', sub='Archaeologists have found pots of honey over 3,000 years old that are still good to eat.')),
 ('checklist', 'Checklist', ['tips', 'social'], 'checklist todo list tasks', 'sq', 'list', 'lemon', 'modern', dict(icon='clipboard-list', kicker='Before you post', title='Your social checklist', items=['Clear headline', 'One call to action', 'Brand colours', 'Proofread twice'], checks=True)),
 ('faq', 'FAQ', ['tips', 'story'], 'faq questions answers help', 'story', 'list', 'coral', 'modern', dict(icon='message-circle', kicker='You asked', title='Frequently asked questions', items=['Do you deliver? Yes, citywide.', 'Opening hours? 9 am – 11 pm daily.', 'Can I return items? Within 14 days.', 'Gift cards? Available in store.'], foot='More questions? Send us a message')),
 # food (5)
 ('menu_special', 'Menu special', ['food', 'social', 'photo'], 'menu special dish restaurant food', 'sq', 'photo', 'coral', 'classic', dict(kicker="Chef's special", title='Grilled salmon bowl', sub='Fresh salmon, rice, avocado and sesame dressing.', price='45 SAR')),
 ('coffee_promo', 'Coffee promo', ['food', 'social'], 'coffee cafe drink promo latte', 'sq', 'center', 'sand', 'classic', dict(icon='coffee', kicker='Morning deal', title='Any coffee + croissant', sub='Only 18 SAR before 11 am.', cta='See you soon')),
 ('new_dish', 'New on the menu', ['food', 'story', 'photo'], 'new dish menu restaurant food story', 'story', 'story', 'forest', 'classic', dict(badge='NEW', title='Something new on the menu', sub='Slow-cooked lamb with saffron rice. Try it this week.', cta='Book a table', photo=True)),
 ('breakfast', 'Breakfast deal', ['food', 'social'], 'breakfast deal morning restaurant', 'sq', 'promo', 'lemon', 'modern', dict(cta='Book a table', kicker='Breakfast deal', big='2 FOR 1', title='Weekend breakfast', sub='Saturday and Sunday, 8 am to noon.')),
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
 ('ramadan_hours', 'Ramadan hours', ['seasonal', 'story'], 'ramadan opening hours timings iftar suhoor', 'story', 'list', 'night', 'modern', dict(icon='moon-star', kicker='Ramadan', title='Our opening hours', items=['Sat – Thu: 8 pm – 2 am', 'Friday: 9 pm – 3 am', 'Iftar boxes: order by 4 pm'], foot='Ramadan Kareem from our team')),
 ('eid_mubarak', 'Eid Mubarak', ['seasonal', 'social'], 'eid mubarak greeting celebration', 'sq', 'center', 'forest', 'classic', dict(icon='sparkles', kicker='Eid Mubarak', title='Joy, peace and togetherness', sub='Wishing you and your family a happy Eid.')),
 ('national_day', 'Saudi National Day', ['seasonal', 'social'], 'saudi national day september celebration ksa', 'sq', 'center', 'green', 'modern', dict(icon='star', kicker='23 September', title='Happy Saudi National Day', sub='Proud of our home. Celebrating together.')),
 ('white_friday', 'White Friday sale', ['seasonal', 'promo', 'social'], 'white friday black friday sale november', 'sq', 'promo', 'black', 'loud', dict(cta='Shop the sale', kicker='White Friday', big='UP TO 70%', title='Our biggest sale of the year', sub='Starts Thursday at midnight. While stocks last.')),
 ('new_year', 'Happy New Year', ['seasonal', 'social'], 'new year celebration greeting', 'sq', 'center', 'night', 'loud', dict(icon='party-popper', kicker='Hello, 2027', title='HAPPY NEW YEAR', sub='Thank you for an amazing year.')),
 # product / announcements (3)
 ('product_launch', 'Product launch', ['promo', 'social', 'photo'], 'product launch new release', 'sq', 'photo', 'sky', 'modern', dict(kicker='Introducing', title='The new Shoof bottle', sub='Keeps drinks cold for 24 hours.', price='79 SAR', mask='blob')),
 ('coming_soon', 'Coming soon', ['promo', 'story'], 'coming soon launch teaser countdown', 'story', 'story', 'black', 'loud', dict(badge='STAY TUNED', title='SOMETHING NEW IS COMING', sub='Turn on notifications so you don’t miss it.', cta='Follow us')),
 ('giveaway', 'Giveaway', ['promo', 'social'], 'giveaway contest win prize', 'sq', 'list', 'pink', 'modern', dict(icon='gift', kicker='Giveaway', title='Win a gift box worth 500 SAR', items=['Follow our account', 'Like this post', 'Tag two friends'], foot='Winner announced Friday')),
 # editorial posters (6)
 ('poster_editorial', 'Editorial fashion poster', ['poster', 'photo'], 'editorial fashion magazine model portrait diagonal', 'a4', 'custom:editorial', 'violet', 'modern', dict(bg='#ffffff')),
 ('poster_passion', 'Diagonal quote poster', ['poster', 'quote', 'story'], 'quote passion motivation diagonal stripes', 'story', 'custom:passion', 'coral', 'modern', dict(bg='#ffc477')),
 ('poster_cinematic', 'Cinematic movie poster', ['poster', 'photo'], 'movie film cinema dark dramatic', 'a4', 'custom:cinematic', 'black', 'classic', {}),
 ('poster_swiss', 'Swiss type poster', ['poster', 'event'], 'swiss typography festival bold type minimal', 'a4', 'custom:swiss', 'black', 'modern', dict(bg='#f2f1ee')),
 ('poster_geo', 'Geometric night poster', ['poster', 'event'], 'party night club music geometric triangles', 'a4', 'custom:geo', 'black', 'modern', {}),
 ('poster_halftone', 'Halftone festival poster', ['poster', 'event'], 'festival music halftone dots yellow bold', 'a4', 'custom:halftone', 'lemon', 'loud', {}),
 # pitch decks (4)
 ('deck_swiss', 'Pitch deck: Swiss (6 slides)', ['deck', 'business'], 'pitch deck presentation slides investor startup minimal', 'slide', 'deck:swiss', 'black', 'modern', {}),
 ('deck_soft', 'Pitch deck: soft gradient (6 slides)', ['deck', 'business'], 'pitch deck presentation slides investor gradient', 'slide', 'deck:soft', 'sand', 'modern', {}),
 ('deck_warm', 'Pitch deck: warm (5 slides)', ['deck', 'business'], 'pitch deck presentation slides orange gradient', 'slide', 'deck:warm', 'coral', 'modern', {}),
 ('deck_pastel', 'Pitch deck: pastel (3 slides)', ['deck', 'business'], 'pitch deck presentation slides pastel blob', 'slide', 'deck:pastel', 'violet', 'modern', {}),
]

CAT_ORDER = ['promo', 'event', 'hiring', 'quote', 'tips', 'food', 'realestate', 'business', 'seasonal']


def with_bg(els, W, H, bg):
    """Every page starts with a background block (role 'bg') so the background can be clicked, recoloured, moved and resized."""
    e = els[0] if els else None
    if e and e['type'] == 'rect' and e['x'] <= 0 and e['y'] <= 0 and e['x'] + e['width'] >= W and e['y'] + e['height'] >= H and not e.get('radius') and not e.get('opacity', 1) < 1:
        e['role'] = 'bg'; return els
    return [R(0, 0, W, H, bg, role='bg')] + els


def build():
    out, keys = [], set()
    for key, name, cats, kw, size, recipe, pal, fonts, content in T:
        assert key not in keys, key; keys.add(key)
        W, H = SIZE[size]; P = PAL[pal]
        if recipe.startswith('deck:'):
            out.append(dict(key=key, name=name, cats=cats, kw=kw, w=W, h=H, pages=[dict(bg=bg, els=with_bg(els, W, H, bg)) for bg, els in DECKS[recipe[5:]]()]))
            continue
        if recipe.startswith('custom:'):
            els = CUSTOM[recipe[7:]](W, H, P, FONTS[fonts], content)
        else:
            els = [e for e in RECIPES[recipe](W, H, P, FONTS[fonts], content)]
            d = None if content.get('plain') else deco(recipe, W, H, P)
            if d: els.insert(0, d)
        bg = content.get('bg', P['bg'])
        out.append(dict(key=key, name=name, cats=cats, kw=kw, w=W, h=H, bg=bg, els=with_bg(els, W, H, bg)))
    return out


def render_block(data):
    js = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    return (START + ' — built by tools/templates/gen_templates.py from its style spec + content table; edit the generator, not this block */\n'
            'const GEN_TEMPLATES=' + js + ';\n' + END)


def main():
    data = build()
    assert len(data) == 60, len(data)
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
