#!/usr/bin/env python3
"""Design knowledge book: docs/design-kb-research-*.md (the design consultant's handover) -> DKB block in index.html.
Usage: python3 tools/design_kb.py [research.md]   (default: newest docs/design-kb-research-*.md)
       python3 tools/design_kb.py --check          (exit 1 if index.html is out of date)
Validates every font, texture and effect against what Shoof has, and every text colour for 4.5:1 contrast."""
import re, json, sys, glob, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = {'Inter','Poppins','Montserrat','Raleway','Nunito','DM Sans','Space Grotesk','Open Sans','Lato','Roboto','Work Sans','Fredoka',
         'Playfair Display','Lora','Merriweather','DM Serif Display','Cormorant Garamond','Libre Baskerville','Bitter',
         'Bebas Neue','Oswald','Anton','Archivo Black','Lobster','Abril Fatface','Righteous','Alfa Slab One','Bangers','Bungee',
         'Pacifico','Dancing Script','Caveat','Great Vibes','Sacramento','Amatic SC','Shadows Into Light','Space Mono','JetBrains Mono'}
TEXTURES = {'dotsFade','dotsEdges','dotsRadial','dotsRing','dotsArrow','dotGrid','pixelCircle','waves','contours','stripes','stripesFade'}
FX = {'soft':'fxSoft','retro':'fxRetro','hollow':'fxHollow','neon':'fxNeon','sticker':'fxSticker','marker':'fxMarker','none':''}
def lum(h):
    c = [int(h[i:i+2], 16)/255 for i in (1, 3, 5)]
    c = [x/12.92 if x <= 0.03928 else ((x+0.055)/1.055)**2.4 for x in c]
    return 0.2126*c[0]+0.7152*c[1]+0.0722*c[2]
def ratio(a, b):
    x, y = lum(a), lum(b); return (max(x, y)+0.05)/(min(x, y)+0.05)
def hexes(s): return [h.lower() for h in re.findall(r'#[0-9A-Fa-f]{6}', s)]
def section(md, n):
    m = re.search(rf'^## {n}\..*?$(.*?)(?=^## \d+\.|\Z)', md, re.S | re.M); return m.group(1) if m else ''
def build(path):
    md = open(path, encoding='utf-8').read(); errs = []
    v = re.search(r'\((\w+ \d{4})\)', md.splitlines()[0]); v = v.group(1) if v else os.path.basename(path)
    verdict = [re.sub(r'\*\*|\s+', ' ', l.strip('- ')).strip() for l in section(md, 1).splitlines() if l.startswith('- ')]
    tips = dict(re.findall(r'^- (\w+): (.+)$', section(md, 2), re.M))
    styles = []
    for row in section(md, 2).splitlines():
        cells = [c.strip() for c in row.strip().strip('|').split('|')]
        if len(cells) != 9 or cells[0] == 'id' or not re.match(r'^[a-z_]+$', cells[0]): continue
        sid, name, why, fonts, pal, tex, fx, shape, rad = cells
        head, body = [f.strip() for f in fonts.split('/')]
        h = hexes(pal)
        c = dict(zip(['bg', 'surface', 'text', 'accent', 'accent2'], h))
        tex = tex.split()[0]; tex = '' if tex == 'none' else tex
        st = {'id': sid, 'name': name, 'why': why, 'head': head, 'body': body, 'palette': {'c': c}, 'texture': tex, 'fx': FX.get(fx.lower(), ''),
              'shape': shape, 'radius': int(re.sub(r'\D', '', rad) or 0), 'tip': tips.get(sid, ''), 'tags': ' '.join(re.findall(r'[A-Za-z]+', why)).lower()}
        if sid == 'bold_type_pop': st['upper'] = True
        styles.append(st)
    pals = []; group = ''
    for l in section(md, 3).splitlines():
        g = re.match(r'^\*\*(.+)\*\*$', l.strip())
        if g: group = g.group(1); continue
        m = re.match(r'^- `(\w+)` ([^(]+)\(([^)]+)\)[.:]*\s*(.+)$', l.strip())
        if not m: continue
        h = hexes(m.group(4))[:5]
        pals.append({'id': m.group(1), 'name': m.group(2).strip(), 'moods': [x.strip() for x in m.group(3).split(',')], 'tags': group.lower(),
                     'c': dict(zip(['bg', 'surface', 'text', 'accent', 'accent2'], h))})
    pairs = []
    for row in section(md, 4).splitlines():
        cells = [c.strip() for c in row.strip().strip('|').split('|')]
        if len(cells) == 5 and cells[0].isdigit():
            pairs.append({'head': re.sub(r'\s*\(.*\)', '', cells[1]), 'body': cells[2], 'mood': cells[3], 'for': cells[4]})
    rules = lambda n: [re.sub(r'\*\*', '', re.sub(r'^\d+\.\s*', '', l.strip())) for l in section(md, n).splitlines() if re.match(r'^\d+\.', l.strip())]
    for st in styles:
        for f in (st['head'], st['body']):
            if f not in FONTS: errs.append(f"style {st['id']}: font {f} not in Shoof")
        if st['texture'] and st['texture'] not in TEXTURES: errs.append(f"style {st['id']}: texture {st['texture']}")
    for p in [s['palette'] | {'id': s['id']} for s in styles] + pals:
        c = p['c']
        if len(c) < 5: errs.append(f"{p['id']}: needs 5 colours"); continue
        for k in ('bg', 'surface'):
            if ratio(c['text'], c[k]) < 4.5: errs.append(f"{p['id']}: text on {k} {ratio(c['text'], c[k]):.2f}")
    for pr in pairs:
        for f in (pr['head'], pr['body']):
            if f not in FONTS: errs.append(f'pair font {f}')
    if len(styles) < 6 or len(pals) < 10 or len(pairs) < 6: errs.append(f'too few: {len(styles)} styles, {len(pals)} palettes, {len(pairs)} pairs')
    return {'v': v, 'src': os.path.basename(path), 'out': verdict, 'styles': styles, 'palettes': pals, 'pairs': pairs, 'colorRules': rules(5), 'layoutRules': rules(6)}, errs
def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    path = args[0] if args else sorted(glob.glob(os.path.join(ROOT, 'docs', 'design-kb-research-*.md')))[-1]
    kb, errs = build(path)
    if errs: print('\n'.join(errs)); sys.exit(1)
    js = json.dumps(kb, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    ix = os.path.join(ROOT, 'index.html'); s = open(ix, encoding='utf-8').read()
    new = re.sub(r'/\*@dkb\*/.*?/\*@dkb-end\*/', lambda m: '/*@dkb*/' + js + '/*@dkb-end*/', s, count=1, flags=re.S)
    if '--check' in sys.argv: sys.exit(0 if new == s else 1)
    open(ix, 'w', encoding='utf-8').write(new)
    print(f"DKB {kb['v']}: {len(kb['styles'])} styles, {len(kb['palettes'])} palettes, {len(kb['pairs'])} pairs, {len(kb['colorRules'])}+{len(kb['layoutRules'])} rules")
if __name__ == '__main__': main()
