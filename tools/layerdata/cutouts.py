#!/usr/bin/env python3
"""Cut the main subject out of free photos with IS-Net (the same model Shoof's background remover uses) -> RGBA PNGs.
Only clean cut-outs are kept (one main blob, crisp edges, 4-75 % of the picture), so photo_gen.py has real people,
animals and objects to place on real photo backgrounds.
  python3 tools/layerdata/cutouts.py --photos photos_subj --out cuts [--max 2000]"""
import argparse, json, os, sys
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def session():
    import onnxruntime as ort
    b = b''.join(open(os.path.join(ROOT, 'vendor', 'ai', f), 'rb').read() for f in ('isnet.0', 'isnet.1'))
    prov = [p for p in ('CUDAExecutionProvider', 'CPUExecutionProvider') if p in ort.get_available_providers()]
    return ort.InferenceSession(b, providers=prov)


def matte(s, im):
    S = 1024
    x = np.asarray(im.convert('RGB').resize((S, S), Image.BICUBIC), np.float32) / 255.0 - 0.5
    m = s.run(None, {s.get_inputs()[0].name: x.transpose(2, 0, 1)[None]})[0].reshape(S, S)
    lo, hi = m.min(), m.max()
    if hi - lo < 0.05:
        return None
    v = np.clip(((m - lo) / (hi - lo) - 0.08) / 0.8, 0, 1)
    return np.asarray(Image.fromarray((v * 255).astype(np.uint8)).resize(im.size, Image.BILINEAR), np.float32) / 255.0


def good(a):
    """one main blob, mostly solid, crisp edge"""
    from scipy import ndimage
    on = a > 0.5
    share = on.mean()
    if not 0.04 <= share <= 0.75:
        return False
    lab, n = ndimage.label(on)
    if n == 0:
        return False
    sizes = ndimage.sum(on, lab, range(1, n + 1))
    if sizes.max() < 0.85 * on.sum():
        return False
    soft = ((a > 0.1) & (a < 0.9)).sum() / max(1, on.sum())
    main = lab == (int(np.argmax(sizes)) + 1)
    perim = (main ^ ndimage.binary_erosion(main)).sum()
    ragged = perim / (2 * np.sqrt(np.pi * main.sum()))     # 1 = a circle; noisy junk edges score high
    return soft < 0.25 and ragged < 3.5


def clean(a):
    """keep only the main blob (plus a small margin for soft hair), drop faint specks elsewhere"""
    from scipy import ndimage
    lab, n = ndimage.label(a > 0.5)
    sizes = ndimage.sum(a > 0.5, lab, range(1, n + 1))
    keep = ndimage.binary_dilation(lab == (int(np.argmax(sizes)) + 1), iterations=max(3, int(min(a.shape) * 0.02)))
    a = np.where(keep, a, 0)
    return np.where(a < 0.04, 0, a)


def decontaminate(rgb, a):
    """soft edge pixels still carry the old background colour; replace it with the subject's own nearby colour"""
    from scipy import ndimage
    solid = (a > 0.95).astype(np.float32)
    num = np.stack([ndimage.gaussian_filter(rgb[..., c] * solid, 4) for c in range(3)], -1)
    den = ndimage.gaussian_filter(solid, 4)[..., None]
    mean = rgb[a > 0.95].mean(0) if (a > 0.95).any() else rgb.reshape(-1, 3).mean(0)
    inner = np.where(den > 1e-3, num / np.maximum(den, 1e-3), mean)
    w = np.clip((a - 0.6) / 0.35, 0, 1)[..., None]     # keep real pixels where the matte is (nearly) solid
    return np.clip(rgb * w + inner * (1 - w), 0, 255).astype(np.uint8)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--photos', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--max', type=int, default=3000)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    s = session()
    fs = sorted(f for f in os.listdir(a.photos) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')))
    kept = 0
    for i, f in enumerate(fs):
        if kept >= a.max:
            break
        try:
            im = Image.open(os.path.join(a.photos, f)).convert('RGB')
            if min(im.size) < 200:
                continue
            m = matte(s, im)
            if m is None or not good(m):
                continue
            m = clean(m)
            ys, xs = np.where(m > 0.05)
            box = (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)
            rgba = np.dstack([decontaminate(np.asarray(im, np.float32), m), (m * 255).astype(np.uint8)])
            stem = os.path.splitext(f)[0]
            Image.fromarray(rgba).crop(box).save(os.path.join(a.out, stem + '.png'))
            # where the cut-out sat in its photo, so photo_gen.py can rebuild the real photo exactly
            json.dump({'photo': f, 'box': [int(v) for v in box], 'size': list(im.size)}, open(os.path.join(a.out, stem + '.json'), 'w'))
            kept += 1
        except Exception as ex:
            print('skip', f, ex, file=sys.stderr)
        if (i + 1) % 100 == 0:
            print(f'{i + 1} photos read, {kept} cut-outs kept', flush=True)
    print('done', kept, 'cut-outs')


if __name__ == '__main__':
    main()
