#!/usr/bin/env python3
"""Measure every bundled Latin font for Magic layers' font matching and write the FONT_FEAT block in index.html.

Per family and weight (400 / 700) we store, as thousandths of the cap height:
  cap/em, x-height/cap, average lowercase advance, average uppercase advance, average digit advance, space advance,
  ink density of "Hnoe" (glyph area / (advance * cap height)).
Run:  python3 tools/font_features.py          (writes the block)
      python3 tools/font_features.py --check  (fails if the block is out of date)
Needs: pip install fonttools brotli
"""
import json, os, re, sys
from fontTools.ttLib import TTFont
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.boundsPen import BoundsPen

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(ROOT, 'index.html')
MARK = '/*@fontfeat*/'


def feats(path):
    f = TTFont(path)
    gs = f.getGlyphSet()
    cmap = f.getBestCmap()
    upm = f['head'].unitsPerEm

    def g(ch):
        n = cmap.get(ord(ch))
        return gs[n] if n and n in gs else None

    def bounds(ch):
        gl = g(ch)
        if not gl:
            return None
        p = BoundsPen(gs)
        gl.draw(p)
        return p.bounds

    def adv(ch):
        gl = g(ch)
        return gl.width if gl else None

    bh = bounds('H')
    if not bh:
        return None
    cap = bh[3]
    if cap <= 0:
        return None
    bx = bounds('x')
    xh = (bx[3] if bx else cap * 0.7) / cap

    def avg(chars):
        v = [adv(c) for c in chars]
        v = [x for x in v if x]
        return sum(v) / len(v) / cap if v else 0.6

    dens = []
    for ch in 'Hnoe':
        gl = g(ch)
        if not gl or not gl.width:
            continue
        p = AreaPen(gs)
        gl.draw(p)
        dens.append(abs(p.value) / (gl.width * cap))
    d = sum(dens) / len(dens) if dens else 0.3
    vals = [cap / upm, xh, avg('abcdefghijklmnopqrstuvwxyz'), avg('ABCDEFGHIJKLMNOPQRSTUVWXYZ'), avg('0123456789'), (adv(' ') or cap * 0.3) / cap, d]
    return ','.join(str(round(v * 1000)) for v in vals)


def collect():
    out = {}
    css = open(os.path.join(ROOT, 'fonts', 'fonts.css')).read()
    for blk in re.findall(r'@font-face\s*{([^}]*)}', css):
        fam = re.search(r"font-family:\s*'([^']+)'", blk)
        w = re.search(r'font-weight:\s*(\d+)', blk)
        src = re.search(r'url\(\./?([^)]+)\)', blk)
        if not (fam and w and src) or 'latin' not in src.group(1) or 'ext' in src.group(1):
            continue
        p = os.path.join(ROOT, 'fonts', src.group(1))
        if os.path.exists(p):
            fe = feats(p)
            if fe:
                out.setdefault(fam.group(1), {})[w.group(1)] = fe
    lib = json.load(open(os.path.join(ROOT, 'fonts', 'lib', 'lib.json')))
    for x in lib:
        slug = x['name'].lower().replace(' ', '-')
        for w in x['w']:
            p = os.path.join(ROOT, 'fonts', 'lib', f'{slug}-{w}.woff2')
            if os.path.exists(p):
                fe = feats(p)
                if fe:
                    out.setdefault(x['name'], {})[str(w)] = fe
    # compact: Name=400feats|700feats (missing weight empty)
    rows = []
    for name in sorted(out):
        v = out[name]
        rows.append(f"{name}={v.get('400', '')}|{v.get('700', '')}")
    return ';'.join(rows)


def block(raw):
    return f"{MARK}const FONT_FEAT_RAW='{raw}';{MARK}"


def main():
    raw = collect()
    src = open(INDEX).read()
    i = src.find(MARK)
    if i < 0:
        print('marker missing in index.html'); sys.exit(1)
    j = src.find(MARK, i + len(MARK))
    new = src[:i] + block(raw) + src[j + len(MARK):]
    if '--check' in sys.argv:
        if new != src:
            print('FONT_FEAT block is out of date: run python3 tools/font_features.py'); sys.exit(1)
        print('font features in sync:', raw.count(';') + 1, 'families'); return
    open(INDEX, 'w').write(new)
    print('wrote', raw.count(';') + 1, 'families,', len(raw), 'chars')


if __name__ == '__main__':
    main()
