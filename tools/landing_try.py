#!/usr/bin/env python3
"""Live "Try it" preview on the landing page (welcome.html).

The landing page redraws three real templates with plain HTML so a visitor can type a
headline and watch it change. This tool copies those templates out of the editor
(index.html, GEN_TEMPLATES) into the block between the /*@try*/ markers in welcome.html,
so the preview always matches what the editor opens. Patterns are left out (too faint to
matter at preview size); icons carry their own outline.

  python3 tools/landing_try.py           -> rewrite the block
  python3 tools/landing_try.py --check   -> exit 1 if the block is out of date (used by the tests)

To show other templates, change KEYS (square 1080x1080 ones with no curved text, photos
only as an arch frame) and add any new font to the @font-face list in welcome.html.
"""
import json, os, re, sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
KEYS = [('neon_open', 'Neon'), ('big_hiring', 'Bold'), ('min_spa', 'Elegant')]
KEEP = ['type', 'x', 'y', 'width', 'height', 'fill', 'fillGradient', 'stroke', 'strokeWidth', 'radius', 'opacity', 'rotation', 'mask',
        'text', 'fontFamily', 'fontSize', 'bold', 'align', 'lineHeight', 'letterSpacing', 'shadowColor', 'shadowBlur', 'shadowX', 'shadowY', 'shadowOpacity']
MARK = '/*@try*/'


def build():
    s = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
    i = s.index('const GEN_TEMPLATES=') + len('const GEN_TEMPLATES=')
    gen, _ = json.JSONDecoder().raw_decode(s[i:])
    j = s.index('const ICON_SET=') + len('const ICON_SET=')
    icons, _ = json.JSONDecoder().raw_decode(s[j:])
    out = []
    for key, label in KEYS:
        t = next(x for x in gen if x['key'] == key)
        assert t['w'] == 1080 and t['h'] == 1080 and 'els' in t, key + ' must be a one-page square template'
        els = []
        for e in t['els']:
            if e['type'] == 'pattern':
                continue
            assert e['type'] in ('rect', 'ellipse', 'text', 'icon', 'placeholder') and not e.get('curve'), f"{key}: the preview cannot draw {e['type']}"
            d = {k: e[k] for k in KEEP if k in e and e[k] not in ('', None, False)}
            if e['type'] == 'icon':
                d['d'] = icons[e['icon']]
            els.append(d)
        out.append({'k': key, 'n': label, 'els': els})
    return json.dumps(out, ensure_ascii=False, separators=(',', ':'))


def main():
    p = os.path.join(ROOT, 'welcome.html')
    html = open(p, encoding='utf-8').read()
    a = html.index(MARK) + len(MARK); b = html.index(MARK, a)
    new = build()
    if '--check' in sys.argv:
        if html[a:b] != new:
            print('welcome.html: the Try it templates are out of date; run python3 tools/landing_try.py'); sys.exit(1)
        print('landing try-it block: in sync'); return
    open(p, 'w', encoding='utf-8').write(html[:a] + new + html[b:])
    print('landing try-it block written:', len(new), 'bytes')


if __name__ == '__main__':
    main()
