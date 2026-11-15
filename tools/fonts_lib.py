#!/usr/bin/env python3
"""Font library: fonts/lib/lib.json -> FONT_LIB_RAW block in index.html (between /*@fontlib*/ markers).
Usage: python3 tools/fonts_lib.py          rewrite the block
       python3 tools/fonts_lib.py --check  exit 1 if the block or the font files are out of step
Add a font: copy @fontsource/<slug> latin 400 (and 700) woff2 into fonts/lib as <slug>-400.woff2 / <slug>-700.woff2,
add a row to fonts/lib/lib.json (name, cat sans|serif|display|script|mono, tags, w, license) and a line to fonts/lib/LICENSES.txt."""
import json, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAT = {'sans': 's', 'serif': 'r', 'display': 'd', 'script': 'h', 'mono': 'm'}
def build():
    lib = json.load(open(os.path.join(ROOT, 'fonts/lib/lib.json')))
    rows, errs = [], []
    lic = open(os.path.join(ROOT, 'fonts/lib/LICENSES.txt')).read()
    for x in lib:
        n = x['name']; slug = n.lower().replace(' ', '-')
        if not re.fullmatch(r'[A-Za-z0-9 ]{2,32}', n): errs.append('bad name ' + n)
        if not re.fullmatch(r'[a-z0-9 -]{2,60}', x['tags']): errs.append('bad tags ' + n)
        if x['license'] not in ('OFL-1.1', 'Apache-2.0'): errs.append('licence ' + n)
        if ('\n' + n + ' — ') not in lic: errs.append('no licence line ' + n)
        for w in x['w']:
            if not os.path.exists(os.path.join(ROOT, 'fonts/lib', f'{slug}-{w}.woff2')): errs.append(f'missing file {slug}-{w}')
        rows.append(f"{n}:{CAT[x['cat']]}:{x['tags']}:{'7' if 700 in x['w'] else '4'}")
    return "/*@fontlib*/const FONT_LIB_RAW='" + ';'.join(rows) + "';/*@/fontlib*/", errs
def main():
    p = os.path.join(ROOT, 'index.html'); s = open(p).read(); block, errs = build()
    m = re.search(r'/\*@fontlib\*/.*?/\*@/fontlib\*/', s, re.S)
    if not m: sys.exit('markers not found')
    if '--check' in sys.argv:
        if errs or m.group(0) != block: print('\n'.join(errs) or 'block out of date'); sys.exit(1)
        print('font library in sync'); return
    if errs: sys.exit('\n'.join(errs))
    open(p, 'w').write(s[:m.start()] + block + s[m.end():]); print('font library written')
if __name__ == '__main__': main()
