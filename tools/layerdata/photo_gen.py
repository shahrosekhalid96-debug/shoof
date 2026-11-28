#!/usr/bin/env python3
"""Photo training data for the layer model (adds to gen.py's flat designs).

Every sample is a photo poster built from exact layers, saved in the same format as gen.py:
  background photo (bg) -> people / objects cut out of other photos (image), each with its own soft shadow or
  rim light (shadow) -> headline / words with glow, drop shadow, outline or gradient (text + its shadow layer)
  -> sometimes a flat badge behind a word (shape).
About a third are REAL photos: the background is the original photo and the subject layer is its own cut-out
sitting exactly where it was, so the picture is a genuine photo, not a paste-up. Those are marked "real":
the trainer only asks for their first peel (the subject is still in the background underneath).

  python3 tools/layerdata/photo_gen.py --bgs photos_bg --cuts cuts --subj photos_subj --out /tmp/lp --n 20000 --start 1000000
"""
import argparse, glob, io, json, os, random, sys, time
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORDS = ('vs sale new open now live today grand opening summer winter coffee studio festival music night city future '
         'battle game day week deal free limited offer join us hiring book event launch match final edition '
         'season art club fresh style tech ai human dream bold black friday shop explore discover the big show').split()
FORMATS = [(1, 1), (4, 5), (16, 9), (9, 16), (3, 2), (2, 3), (1.91, 1)]


# ---------------------------------------------------------------- fonts
def font_files(cache):
    """every Latin font in Shoof, converted from woff2 to ttf once (PIL can't read woff2)"""
    from fontTools.ttLib import TTFont
    os.makedirs(cache, exist_ok=True)
    src = [f for f in glob.glob(os.path.join(ROOT, 'fonts', '*.woff2')) if 'arabic' not in f]
    src += glob.glob(os.path.join(ROOT, 'fonts', 'lib', '*.woff2'))
    out = []
    for f in sorted(src):
        t = os.path.join(cache, os.path.basename(f)[:-6] + '.ttf')
        if not os.path.exists(t):
            try:
                ft = TTFont(f)
                ft.flavor = None
                ft.save(t)
            except Exception:
                continue
        out.append(t)
    return out


def fam(path):
    n = os.path.basename(path)[:-4].replace('-latin', '').replace('-normal', '')
    bold = n.endswith('-700')
    n = n.rsplit('-', 1)[0]
    return ' '.join(w.capitalize() for w in n.split('-')), bold


# ---------------------------------------------------------------- helpers
def cover(im, W, H, rnd):
    w, h = im.size
    s = max(W / w, H / h) * rnd.uniform(1.0, 1.25)
    im = im.resize((max(W, int(w * s + 0.5)), max(H, int(h * s + 0.5))), Image.BICUBIC)
    x = rnd.randint(0, im.width - W)
    y = rnd.randint(0, im.height - H)
    return im.crop((x, y, x + W, y + H))


def grade(im, rnd):
    """colour grade a background (dark/blue/warm/neon looks like real posters)"""
    a = np.asarray(im, np.float32) / 255.0
    r = rnd.random()
    if r < 0.3:
        a = a * rnd.uniform(0.35, 0.7)
    if rnd.random() < 0.35:
        tint = np.array([rnd.uniform(0.4, 1.2) for _ in range(3)], np.float32)
        a = a * (1 - 0.35) + a * tint * 0.35
    if rnd.random() < 0.25:
        yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]]
        d = ((xx / a.shape[1] - .5) ** 2 + (yy / a.shape[0] - .5) ** 2) ** .5
        a = a * (1 - np.clip(d - 0.3, 0, 1)[..., None] * rnd.uniform(0.5, 1.2))
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))


def place(layers, im, x, y, W, H, meta):
    """clip an RGBA layer to the page and store it with its box"""
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + im.width), min(H, y + im.height)
    if x1 - x0 < 2 or y1 - y0 < 2:
        return False
    c = im.crop((x0 - x, y0 - y, x1 - x, y1 - y))
    if np.asarray(c)[..., 3].max() < 16:
        return False
    meta['box'] = {'x': x0, 'y': y0, 'w': x1 - x0, 'h': y1 - y0}
    layers.append((c, meta))
    return True


def halo(alpha, color, blur, spread, opacity, dx=0, dy=0):
    """shadow / glow layer from an alpha mask: returns (rgba, offset)"""
    pad = int(blur * 3 + spread + abs(dx) + abs(dy) + 4)
    a = Image.new('L', (alpha.width + 2 * pad, alpha.height + 2 * pad), 0)
    a.paste(alpha, (pad + dx, pad + dy))
    if spread:
        a = a.filter(ImageFilter.MaxFilter(spread * 2 + 1))
    a = a.filter(ImageFilter.GaussianBlur(blur))
    a = a.point(lambda v: int(v * opacity))
    out = Image.new('RGBA', a.size, color + (0,))
    out.putalpha(a)
    return out, pad


def harmonize(sub, bg_region, k):
    s = np.asarray(sub, np.float32)
    rgb, al = s[..., :3], s[..., 3:]
    m = al[..., 0] > 128
    if m.sum() < 10:
        return sub
    b = np.asarray(bg_region.convert('RGB'), np.float32).reshape(-1, 3)
    mu_s, mu_b = rgb[m].mean(0), b.mean(0)
    rgb = rgb + (mu_b - mu_s) * k
    return Image.fromarray(np.dstack([np.clip(rgb, 0, 255), al]).astype(np.uint8), 'RGBA')


def vivid(rnd):
    pal = [(93, 207, 255), (255, 79, 216), (168, 85, 247), (34, 211, 238), (255, 200, 60), (255, 255, 255),
           (255, 90, 60), (120, 255, 160)]
    return rnd.choice(pal)


# ---------------------------------------------------------------- text
def text_layers(layers, W, H, fonts, rnd, uid, dark_bg):
    n = rnd.choice([0, 1, 1, 1, 2, 2, 3])
    for k in range(n):
        words = ' '.join(rnd.choice(WORDS) for _ in range(rnd.choice([1, 1, 1, 2, 2, 3])))
        if rnd.random() < 0.6:
            words = words.upper()
        fpath = rnd.choice(fonts)
        family, bold = fam(fpath)
        size = int(min(W, H) * (rnd.uniform(0.12, 0.3) if k == 0 else rnd.uniform(0.04, 0.1)))
        try:
            f = ImageFont.truetype(fpath, size)
        except Exception:
            continue
        stroke = rnd.choice([0, 0, 0, max(1, size // 30)])
        box = f.getbbox(words, stroke_width=stroke)
        tw, th = box[2] - box[0], box[3] - box[1]
        if tw < 4 or th < 4 or tw > W * 0.95:
            continue
        mask = Image.new('L', (tw + 4, th + 4), 0)
        ImageDraw.Draw(mask).text((2 - box[0], 2 - box[1]), words, font=f, fill=255, stroke_width=stroke, stroke_fill=255)
        fill = (255, 255, 255) if dark_bg else (20, 20, 30)
        if rnd.random() < 0.5:
            fill = vivid(rnd)
        rgb = Image.new('RGB', mask.size, fill)
        if rnd.random() < 0.3:   # vertical gradient
            f2 = vivid(rnd)
            g = np.linspace(0, 1, mask.height)[:, None, None]
            rgb = Image.fromarray((np.array(fill) * (1 - g) + np.array(f2) * g).repeat(mask.width, 1).astype(np.uint8))
        if stroke and rnd.random() < 0.6:   # outline in another colour: the letters inside the outline
            inner = Image.new('L', mask.size, 0)
            ImageDraw.Draw(inner).text((2 - box[0], 2 - box[1]), words, font=f, fill=255)
            oc = Image.new('RGB', mask.size, vivid(rnd))
            oc.paste(rgb, (0, 0), inner)
            rgb = oc
        im = rgb.convert('RGBA')
        im.putalpha(mask)
        align = rnd.choice(['left', 'center', 'center', 'right'])
        x = {'left': int(W * rnd.uniform(0.04, 0.1)), 'center': (W - im.width) // 2,
             'right': W - im.width - int(W * rnd.uniform(0.04, 0.1))}[align] + rnd.randint(-W // 20, W // 20)
        y = rnd.randint(int(H * 0.04), max(int(H * 0.05), H - im.height - int(H * 0.04)))
        tid = f't{uid}{k}'
        fx = rnd.random()
        if fx < 0.4:     # glow
            col = vivid(rnd)
            h, pad = halo(mask, col, size * rnd.uniform(0.08, 0.25), rnd.randint(0, 3), rnd.uniform(0.7, 1.0))
            place(layers, h, x - pad, y - pad, W, H, {'type': 'shadow', 'of': tid, 'kind': 'glow', 'color': list(col)})
        elif fx < 0.65:  # drop shadow
            d = max(1, int(size * rnd.uniform(0.03, 0.1)))
            h, pad = halo(mask, (0, 0, 0), size * rnd.uniform(0.02, 0.12), 0, rnd.uniform(0.35, 0.8), d, d)
            place(layers, h, x - pad, y - pad, W, H, {'type': 'shadow', 'of': tid, 'kind': 'drop'})
        if rnd.random() < 0.15:  # flat badge behind small words
            pw, ph = im.width + size, im.height + size // 2
            b = Image.new('RGBA', (pw, ph), (0, 0, 0, 0))
            ImageDraw.Draw(b).rounded_rectangle((0, 0, pw - 1, ph - 1), radius=rnd.choice([0, ph // 4, ph // 2]), fill=vivid(rnd) + (255,))
            place(layers, b, x - size // 2, y - size // 4, W, H, {'type': 'shape', 'id': tid + 'b'})
        place(layers, im, x, y, W, H, {'type': 'text', 'id': tid, 'text': words, 'font': family, 'bold': bold,
                                         'size': size, 'align': align, 'fill': list(fill), 'stroke': stroke})


# ---------------------------------------------------------------- one sample
def sample(seed, a, bgs, cuts, fonts):
    rnd = random.Random(seed * 7919 + 17)
    long = a.size
    paired = [c for c in cuts if os.path.exists(c[:-4] + '.json')]   # cut-outs that know their source photo
    real = bool(paired and a.subj) and rnd.random() < 0.33
    layers = []
    if real:
        c = rnd.choice(paired)
        info = json.load(open(c[:-4] + '.json'))
        photo = Image.open(os.path.join(a.subj, info['photo'])).convert('RGB')
        s = long / max(photo.size)
        W, H = max(64, int(photo.width * s)), max(64, int(photo.height * s))
        bg = photo.resize((W, H), Image.BICUBIC)
        sub = Image.open(c).convert('RGBA')
        x0, y0, x1, y1 = info['box']
        sw, sh = max(2, int((x1 - x0) * s)), max(2, int((y1 - y0) * s))
        sub = sub.resize((sw, sh), Image.BICUBIC)
        # the subject's own pixels, exactly as in the photo (only the matte comes from the cut-out)
        al = sub.getchannel('A')
        sub = bg.crop((int(x0 * s), int(y0 * s), int(x0 * s) + sw, int(y0 * s) + sh)).convert('RGBA')
        sub.putalpha(al)
        layers.append((bg.convert('RGBA'), {'type': 'bg'}))
        place(layers, sub, int(x0 * s), int(y0 * s), W, H, {'type': 'image', 'id': 's0', 'kind': 'subject'})
        dark = np.asarray(bg).mean() < 110
    else:
        fw, fh = rnd.choice(FORMATS)
        W, H = (long, int(long * fh / fw)) if fw >= fh else (int(long * fw / fh), long)
        bg = grade(cover(Image.open(rnd.choice(bgs)).convert('RGB'), W, H, rnd), rnd)
        layers.append((bg.convert('RGBA'), {'type': 'bg'}))
        dark = np.asarray(bg).mean() < 110
        n = rnd.choice([0, 1, 1, 2, 2, 2, 3]) if cuts else 0
        slots = rnd.sample([0, 1, 2], n) if n <= 3 else []
        for k, slot in enumerate(slots):
            sub = Image.open(rnd.choice(cuts)).convert('RGBA')
            if rnd.random() < 0.5:
                sub = sub.transpose(Image.FLIP_LEFT_RIGHT)
            hh = int(H * rnd.uniform(0.35, 1.05))
            ww = max(2, int(sub.width * hh / sub.height))
            if ww > W * 0.9:
                ww = int(W * 0.9); hh = max(2, int(sub.height * ww / sub.width))
            sub = sub.resize((ww, hh), Image.BICUBIC)
            cx = int(W * (0.18 + 0.32 * slot + rnd.uniform(-0.1, 0.1)))
            x = cx - ww // 2
            y = H - hh + int(hh * rnd.uniform(0, 0.15)) if rnd.random() < 0.7 else rnd.randint(0, max(0, H - hh))
            reg = bg.crop((max(0, x), max(0, y), max(1, min(W, x + ww)), max(1, min(H, y + hh))))
            sub = harmonize(sub, reg, rnd.uniform(0, 0.25))
            sid = f's{k}'
            r = rnd.random()
            al = sub.getchannel('A')
            if r < 0.3:    # rim light / glow behind
                col = vivid(rnd)
                h, pad = halo(al, col, min(ww, hh) * rnd.uniform(0.02, 0.06), rnd.randint(1, 4), rnd.uniform(0.5, 0.9))
                place(layers, h, x - pad, y - pad, W, H, {'type': 'shadow', 'of': sid, 'kind': 'glow', 'color': list(col)})
            elif r < 0.6:  # soft drop shadow
                d = int(min(ww, hh) * rnd.uniform(0.01, 0.05))
                h, pad = halo(al, (0, 0, 0), min(ww, hh) * rnd.uniform(0.02, 0.06), 0, rnd.uniform(0.3, 0.65), d, d)
                place(layers, h, x - pad, y - pad, W, H, {'type': 'shadow', 'of': sid, 'kind': 'drop'})
            place(layers, sub, x, y, W, H, {'type': 'image', 'id': sid, 'kind': 'subject'})
    text_layers(layers, W, H, fonts, rnd, seed, dark)
    return W, H, layers, real


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--bgs', required=True)
    ap.add_argument('--cuts', default='')
    ap.add_argument('--subj', default='')
    ap.add_argument('--out', required=True)
    ap.add_argument('--n', type=int, default=1000)
    ap.add_argument('--start', type=int, default=1000000)
    ap.add_argument('--size', type=int, default=640)
    ap.add_argument('--fontcache', default='/tmp/shoof-ttf')
    ap.add_argument('--workers', type=int, default=1)
    ap.add_argument('--sheet', default='')
    a = ap.parse_args()
    if a.workers > 1:
        import subprocess
        per = -(-a.n // a.workers)
        font_files(a.fontcache)
        args = [x for x in sys.argv[1:]]
        i = args.index('--workers'); del args[i:i + 2]
        for flag in ('--n', '--start', '--sheet'):
            if flag in args:
                j = args.index(flag); del args[j:j + 2]
        ps = [subprocess.Popen([sys.executable, __file__] + args + ['--n', str(min(per, a.n - w * per)), '--start', str(a.start + w * per)])
              for w in range(a.workers) if a.n - w * per > 0]
        for p in ps:
            p.wait()
        if a.sheet:
            sheet(a.out, a.start, a.sheet)
        return
    bgs = sorted(f for e in ('jpg', 'jpeg', 'png', 'webp') for f in glob.glob(os.path.join(a.bgs, '*.' + e)))
    cuts = sorted(glob.glob(os.path.join(a.cuts, '*.png'))) if a.cuts else []
    fonts = font_files(a.fontcache)
    assert bgs and fonts, 'need background photos and fonts'
    t0, done = time.time(), 0
    for seed in range(a.start, a.start + a.n):
        try:
            W, H, L, real = sample(seed, a, bgs, cuts, fonts)
        except Exception as ex:
            print('skip', seed, ex, file=sys.stderr)
            continue
        d = os.path.join(a.out, str(seed))
        os.makedirs(d, exist_ok=True)
        metas = []
        for i, (im, m) in enumerate(L):
            fn = f'{i:02d}.webp'
            if m['type'] in ('bg', 'image'):
                im.save(os.path.join(d, fn), 'WEBP', quality=90, alpha_quality=100, method=4)
            else:
                im.save(os.path.join(d, fn), 'WEBP', lossless=True, method=4)
            metas.append(dict(m, file=fn))
        json.dump({'seed': seed, 'src': 'photo', 'real': real, 'w': W, 'h': H, 'layers': metas}, open(os.path.join(d, 'meta.json'), 'w'))
        done += 1
        if done % 200 == 0:
            print(f'{done} photo posters, {done / (time.time() - t0):.1f}/s', flush=True)
    print(f'done: {done} photo posters in {time.time() - t0:.0f}s -> {a.out}')
    if a.sheet:
        sheet(a.out, a.start, a.sheet)


def sheet(out, start, path, n=12):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from gen import compose
    ims = []
    for s in range(start, start + n * 3):
        d = os.path.join(out, str(s))
        if os.path.exists(os.path.join(d, 'meta.json')):
            im = compose(d).convert('RGB')
            im.thumbnail((320, 320))
            ims.append(im)
        if len(ims) >= n:
            break
    if not ims:
        return
    S = Image.new('RGB', (4 * 320, -(-len(ims) // 4) * 320), (40, 40, 40))
    for i, im in enumerate(ims):
        S.paste(im, ((i % 4) * 320, (i // 4) * 320))
    S.save(path)


if __name__ == '__main__':
    main()
