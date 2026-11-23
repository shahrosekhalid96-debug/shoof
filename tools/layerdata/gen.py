#!/usr/bin/env python3
"""Shoof layer-data generator (driver).

Serves the repo locally, opens the editor in headless Chromium, injects tools/layerdata/sample.js and saves one folder
per design:  <out>/<seed>/composite.png, 00.png, 01.png ... (paint order, bottom first), meta.json
meta.json = {seed, src, w, h, layers:[{file, type, box, ...text: words/font/size/align/colour; shadow: of}]}

  python3 tools/layerdata/gen.py --out /tmp/ld --n 200 [--start 0] [--size 512] [--photos DIR] [--sheet sheet.png]

--photos: a folder of CC0 jpg/png photos to use inside designs (else photo-like pictures are drawn).
Runs the same on Kaggle (CPU notebook) and locally. Needs: pip install playwright pillow && playwright install chromium
"""
import argparse, base64, functools, http.server, json, os, random, socketserver, sys, threading, time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def serve():
    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    h = functools.partial(Q, directory=ROOT)
    srv = socketserver.ThreadingTCPServer(('127.0.0.1', 0), h)
    srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv.server_address[1]


def b64file(path, data_url):
    with open(path, 'wb') as f:
        f.write(base64.b64decode(data_url.split(',', 1)[1]))


def save_layer(path, data_url, m):
    """layers are stored cropped to their box (box.x/y = where the crop sits on the page); the background stays full size"""
    import io
    from PIL import Image
    im = Image.open(io.BytesIO(base64.b64decode(data_url.split(',', 1)[1])))
    b = m.get('box')
    if b and m.get('type') != 'bg':
        im = im.crop((b['x'], b['y'], b['x'] + b['w'], b['y'] + b['h']))
    im.save(path, 'WEBP', lossless=True, method=4)


def compose(folder, upto=None):
    """rebuild the flat picture from the layers (exact 'over' blending, same as the browser); upto = only the first n layers"""
    from PIL import Image
    m = json.load(open(os.path.join(folder, 'meta.json')))
    out = Image.new('RGBA', (m['w'], m['h']), (255, 255, 255, 255))
    for L in m['layers'][:upto]:
        im = Image.open(os.path.join(folder, L['file'])).convert('RGBA')
        b = L.get('box') if L['type'] != 'bg' else None
        out.alpha_composite(im, (b['x'], b['y']) if b else (0, 0))
    return out


def load_photos(folder, limit=300, side=1024):
    if not folder:
        return []
    from PIL import Image
    import io
    out = []
    names = [n for n in sorted(os.listdir(folder)) if n.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
    random.Random(1).shuffle(names)
    for n in names[:limit]:
        try:
            im = Image.open(os.path.join(folder, n)).convert('RGB')
            im.thumbnail((side, side))
            b = io.BytesIO()
            im.save(b, 'JPEG', quality=88)
            out.append('data:image/jpeg;base64,' + base64.b64encode(b.getvalue()).decode())
        except Exception:
            pass
    return out


def contact_sheet(out, seeds, path, per=6):
    from PIL import Image, ImageDraw
    rows = []
    for s in seeds:
        d = os.path.join(out, str(s))
        m = json.load(open(os.path.join(d, 'meta.json')))
        th = 160
        def tile(p, checker=False, box=None):
            im = Image.open(p).convert('RGBA')
            if box:
                full = Image.new('RGBA', (m['w'], m['h']), (0, 0, 0, 0))
                full.paste(im, (box['x'], box['y']))
                im = full
            im.thumbnail((th, th))
            bg = Image.new('RGBA', (th, th), (255, 255, 255, 255))
            if checker:
                dr = ImageDraw.Draw(bg)
                for y in range(0, th, 10):
                    for x in range(0, th, 10):
                        if (x // 10 + y // 10) % 2:
                            dr.rectangle([x, y, x + 9, y + 9], fill=(215, 215, 215, 255))
            bg.alpha_composite(im, ((th - im.width) // 2, (th - im.height) // 2))
            return bg
        flat = os.path.join(d, '_flat.png')
        compose(d).convert('RGB').save(flat)
        tiles = [tile(flat)] + [tile(os.path.join(d, L['file']), True, L.get('box') if L['type'] != 'bg' else None) for L in m['layers'][:per]]
        row = Image.new('RGBA', (th * (per + 1) + 4 * per, th + 18), (40, 40, 48, 255))
        dr = ImageDraw.Draw(row)
        for i, t in enumerate(tiles):
            row.alpha_composite(t, (i * (th + 4), 18))
            lab = 'flat' if i == 0 else m['layers'][i - 1]['type'] + (' ' + str(m['layers'][i - 1].get('font', '')) if m['layers'][i - 1]['type'] == 'text' else '')
            dr.text((i * (th + 4) + 3, 3), lab[:26], fill=(230, 230, 240, 255))
        rows.append(row)
    sheet = Image.new('RGBA', (rows[0].width, sum(r.height + 6 for r in rows)), (24, 24, 30, 255))
    y = 0
    for r in rows:
        sheet.alpha_composite(r, (0, y))
        y += r.height + 6
    sheet.convert('RGB').save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--n', type=int, default=100)
    ap.add_argument('--start', type=int, default=0)
    ap.add_argument('--size', type=int, default=512)
    ap.add_argument('--photos', default='')
    ap.add_argument('--sheet', default='')
    ap.add_argument('--workers', type=int, default=1)
    ap.add_argument('--composite', action='store_true', help='also save the browser-rendered flat picture (for checking compose())')
    a = ap.parse_args()
    if a.workers > 1:
        import subprocess
        per = (a.n + a.workers - 1) // a.workers
        ps = [subprocess.Popen([sys.executable, __file__, '--out', a.out, '--n', str(min(per, a.n - i * per)), '--start', str(a.start + i * per), '--size', str(a.size)] + (['--photos', a.photos] if a.photos else []) + (['--composite'] if a.composite else [])) for i in range(a.workers) if a.n - i * per > 0]
        for p in ps:
            p.wait()
        if a.sheet:
            contact_sheet(a.out, sorted(int(x) for x in os.listdir(a.out) if x.isdigit())[:8], a.sheet)
        return
    from playwright.sync_api import sync_playwright
    os.makedirs(a.out, exist_ok=True)
    photos = load_photos(a.photos)
    port = serve()
    js = open(os.path.join(ROOT, 'tools', 'layerdata', 'sample.js'), encoding='utf-8').read()
    done, t0 = [], time.time()
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={'width': 1280, 'height': 800})
        pg.add_init_script("try{localStorage.setItem('shoof.tips','1');localStorage.setItem('shoof.buddy','off')}catch(e){}")
        pg.goto(f'http://127.0.0.1:{port}/index.html')
        pg.wait_for_function('typeof dgBuild==="function"&&typeof TEMPLATES==="object"&&typeof doc!=="undefined"&&doc', timeout=60000)
        pg.add_script_tag(content=js)
        pg.evaluate('p=>{window.LD_PHOTOS=p}', photos)
        for seed in range(a.start, a.start + a.n):
            try:
                r = pg.evaluate('([s,z])=>LD_sample(s,{size:z,photos:window.LD_PHOTOS})', [seed, a.size])
            except Exception as ex:
                print('skip', seed, str(ex)[:120], file=sys.stderr)
                continue
            d = os.path.join(a.out, str(seed))
            os.makedirs(d, exist_ok=True)
            if a.composite:
                b64file(os.path.join(d, 'composite.png'), r['composite'])
            layers = []
            for i, L in enumerate(r['layers']):
                fn = f'{i:02d}.webp'
                m = dict(L['meta'], file=fn)
                save_layer(os.path.join(d, fn), L['png'], m)
                layers.append(m)
            json.dump({'seed': seed, 'src': r['src'], 'w': r['w'], 'h': r['h'], 'layers': layers}, open(os.path.join(d, 'meta.json'), 'w'))
            done.append(seed)
            if len(done) % 50 == 0:
                print(f'{len(done)} designs, {len(done) / (time.time() - t0):.2f}/s', flush=True)
        b.close()
    print(f'done: {len(done)} designs in {time.time() - t0:.0f}s -> {a.out}')
    if a.sheet and done:
        contact_sheet(a.out, done[:8], a.sheet)


if __name__ == '__main__':
    main()
