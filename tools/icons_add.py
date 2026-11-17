#!/usr/bin/env python3
"""Add Lucide icons to Shoof's bundled icon set (ICON_SET / ICON_TAGS in index.html).

Lucide (ISC licence, vendor/LUCIDE-LICENSE.txt) ships each icon as a few SVG shapes. Shoof keeps
one path string per icon, every sub-path starting with an absolute M, so the editor, the exports
and the landing page can all draw it the same way. This tool does that conversion.

  cd /tmp && npm i lucide-static          (once; any folder)
  python3 tools/icons_add.py /tmp/node_modules/lucide-static name1 name2 ...
  python3 tools/icons_add.py /tmp/node_modules/lucide-static @tools/icons_wanted.txt

Names already bundled are skipped, unknown names are reported. Run the tests afterwards
(elements_panel checks every icon draws) and update the icon count in the About credit.
"""
import json, math, os, re, sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
NUM = r'[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?'


def f(v):
    v = round(float(v), 3)
    return str(int(v)) if v == int(v) else str(v)


def abs_start(d):
    """A path element may start with a relative 'm'; once paths are joined that would be relative to the
    previous shape, so make the first move absolute (it is absolute by definition at the start of a path)."""
    d = d.strip()
    if not d.startswith('m'):
        return d
    m = re.match(r'm\s*(%s)[\s,]*(%s)' % (NUM, NUM), d)
    rest = d[m.end():]
    more = re.match(r'[\s,]*(?=[-+.\d])', rest)   # numbers straight after the move are relative line-tos
    return 'M%s %s%s' % (m.group(1), m.group(2), ('l' + rest[more.end():]) if more and rest[more.end():] else rest)


def shape(tag, a):
    g = lambda k, d=0: float(a.get(k, d))
    if tag == 'path':
        return abs_start(a['d'])
    if tag == 'circle':
        cx, cy, r = g('cx'), g('cy'), g('r')
        return 'M%s %sa%s %s 0 1 0 %s 0a%s %s 0 1 0 %s 0Z' % (f(cx - r), f(cy), f(r), f(r), f(2 * r), f(r), f(r), f(-2 * r))
    if tag == 'ellipse':
        cx, cy, rx, ry = g('cx'), g('cy'), g('rx'), g('ry')
        return 'M%s %sa%s %s 0 1 0 %s 0a%s %s 0 1 0 %s 0Z' % (f(cx - rx), f(cy), f(rx), f(ry), f(2 * rx), f(rx), f(ry), f(-2 * rx))
    if tag == 'line':
        return 'M%s %sL%s %s' % (f(g('x1')), f(g('y1')), f(g('x2')), f(g('y2')))
    if tag in ('polyline', 'polygon'):
        n = [f(x) for x in re.findall(NUM, a['points'])]
        pts = ['%s %s' % (n[i], n[i + 1]) for i in range(0, len(n) - 1, 2)]
        return 'M' + 'L'.join(pts) + ('Z' if tag == 'polygon' else '')
    if tag == 'rect':
        x, y, w, h = g('x'), g('y'), g('width'), g('height')
        rx = min(float(a.get('rx', a.get('ry', 0))), w / 2); ry = min(float(a.get('ry', a.get('rx', 0))), h / 2)
        if not rx and not ry:
            return 'M%s %sh%sv%sh%sZ' % (f(x), f(y), f(w), f(h), f(-w))
        arc = lambda dx, dy: 'a%s %s 0 0 1 %s %s' % (f(rx), f(ry), f(dx), f(dy))
        return 'M%s %sh%s%sv%s%sh%s%sv%s%sZ' % (f(x + rx), f(y), f(w - 2 * rx), arc(rx, ry), f(h - 2 * ry), arc(-rx, ry), f(-(w - 2 * rx)), arc(-rx, -ry), f(-(h - 2 * ry)), arc(rx, -ry))
    raise ValueError('unknown shape ' + tag)


def main():
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(2)
    lib = sys.argv[1]; names = []
    for a in sys.argv[2:]:
        names += open(a[1:], encoding='utf-8').read().split() if a.startswith('@') else [a]
    nodes = json.load(open(os.path.join(lib, 'icon-nodes.json'), encoding='utf-8'))
    tags = json.load(open(os.path.join(lib, 'tags.json'), encoding='utf-8'))
    p = os.path.join(ROOT, 'index.html'); s = open(p, encoding='utf-8').read()
    i = s.index('const ICON_SET=') + len('const ICON_SET='); icons, n = json.JSONDecoder().raw_decode(s[i:])
    j = s.index('ICON_TAGS=', i + n) + len('ICON_TAGS='); tg, m = json.JSONDecoder().raw_decode(s[j:])
    added, missing = [], []
    for name in dict.fromkeys(names):
        if name in icons:
            continue
        if name not in nodes:
            missing.append(name); continue
        d = ''.join(shape(t, a) for t, a in nodes[name])
        assert d.startswith('M') and '<' not in d and '"' not in d, name
        icons[name] = d
        tg[name] = ' '.join(dict.fromkeys(w for w in ' '.join(tags.get(name, [])).lower().replace('-', ' ').split() if re.fullmatch(r'[a-z0-9]+', w)))[:160]
        added.append(name)
    dump = lambda o: json.dumps(o, ensure_ascii=False, separators=(',', ':'))
    s = s[:i] + dump(icons) + s[i + n:j] + dump(tg) + s[j + m:]
    open(p, 'w', encoding='utf-8').write(s)
    print('added %d (now %d icons)' % (len(added), len(icons)))
    if missing:
        print('not in this Lucide version:', ' '.join(missing))


if __name__ == '__main__':
    main()
