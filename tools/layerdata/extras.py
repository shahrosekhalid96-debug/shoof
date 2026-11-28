#!/usr/bin/env python3
"""Split contact-sheet pictures Shary supplied into training material.

  photo grid  (photos separated by light gutters, a name pill in the top-left corner)
      -> extra/photos/<sheet>-<n>.webp   (the name pill is cropped off, so no unlabelled text enters training)
  cut-out grid (objects on a drawn grey/white checkerboard, light gutters)
      -> extra/cuts/<sheet>-<n>.png      (real transparency from IS-Net, edge colour cleaned)

  python3 tools/layerdata/extras.py --photos grid1.png --cuts grid2.png
"""
import argparse, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def runs(flags, min_len):
    """[start, end) spans where flags is False and long enough = tiles between gutters"""
    out, s = [], None
    for i, f in enumerate(list(flags) + [True]):
        if not f and s is None:
            s = i
        elif f and s is not None:
            if i - s >= min_len:
                out.append((s, i))
            s = None
    return out


def tiles(a, thr, frac):
    light = a.min(2) > thr
    rows = runs(light.mean(1) > frac, 60)
    out = []
    for y0, y1 in rows:
        cols = runs(light[y0:y1].mean(0) > frac, 60)
        out += [(x0, y0, x1, y1) for x0, x1 in cols]
    return out


def dechecker(rgb, m):
    """the sheet's 'transparent' background is a DRAWN light checkerboard; IS-Net keeps specks of it.
    Checker = light, colourless pixels joined to the tile edge. Keep IS-Net's object minus those,
    plus IS-Net's confident interior (so white mugs / planes on white squares are not eaten)."""
    from scipy import ndimage
    sat = rgb.max(2) - rgb.min(2)
    light = (sat <= 14) & (rgb.min(2) >= 205)
    lab, n = ndimage.label(light)
    edge = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    bg = np.isin(lab, list(edge))
    keep = ((m > 0.5) & ~bg) | ndimage.binary_erosion(m > 0.9, iterations=4)
    keep = ndimage.binary_opening(keep, iterations=1)
    lab, n = ndimage.label(keep)
    if n:
        sz = ndimage.sum(keep, lab, range(1, n + 1))
        keep = np.isin(lab, [i + 1 for i, v in enumerate(sz) if v >= 0.02 * sz.max()])
    filled = ndimage.binary_fill_holes(keep)
    hl, hn = ndimage.label(filled & ~keep)        # enclosed gaps: a mug handle / headphone band shows checker
    for i in range(1, hn + 1):
        h = hl == i
        if h.sum() > 30 and light[h].mean() > 0.6:
            filled[h] = False
    keep = filled
    soft = ndimage.gaussian_filter(keep.astype(np.float32), 0.8)
    return np.clip(soft, 0, 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--photos', nargs='*', default=[])
    ap.add_argument('--cuts', nargs='*', default=[])
    ap.add_argument('--out', default=os.path.join(HERE, 'extra'))
    a = ap.parse_args()
    os.makedirs(os.path.join(a.out, 'photos'), exist_ok=True)
    os.makedirs(os.path.join(a.out, 'cuts'), exist_ok=True)
    for k, f in enumerate(a.photos):
        im = Image.open(f).convert('RGB')
        boxes = tiles(np.asarray(im).astype(int), 225, 0.75)
        for i, (x0, y0, x1, y1) in enumerate(boxes):
            t = im.crop((x0 + 2, y0 + 2, x1 - 2, y1 - 2))
            t = t.crop((0, int(t.height * 0.2), t.width, t.height))      # drop the name pill
            t.save(os.path.join(a.out, 'photos', f'grid{k}-{i:02d}.webp'), quality=92)
        print(f, len(boxes), 'photos')
    if a.cuts:
        from cutouts import session, matte, clean, decontaminate
        s = session()
        for k, f in enumerate(a.cuts):
            im = Image.open(f).convert('RGB')
            boxes = tiles(np.asarray(im).astype(int), 248, 0.85)
            n = 0
            for i, (x0, y0, x1, y1) in enumerate(boxes):
                t = im.crop((x0 + 3, y0 + 3, x1 - 3, y1 - 3))
                m = matte(s, t)
                if m is None:
                    continue
                m = clean(m)
                m = dechecker(np.asarray(t).astype(int), m)
                ys, xs = np.where(m > 0.05)
                if len(xs) < 50:
                    continue
                rgba = np.dstack([decontaminate(np.asarray(t, np.float32), m), (m * 255).astype(np.uint8)])
                Image.fromarray(rgba).crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)).save(
                    os.path.join(a.out, 'cuts', f'sheet{k}-{i:02d}.png'), optimize=True)
                n += 1
            print(f, len(boxes), 'tiles,', n, 'cut-outs')


if __name__ == '__main__':
    main()
