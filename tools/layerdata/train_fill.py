#!/usr/bin/env python3
"""Shoof fill model: paints what was behind a layer after it is lifted out.

Why our own: the training designs and photo posters are built from exact layers, so for every peel we KNOW the
true picture behind the lifted items (round k -> round k+1). Real photos add ordinary photo filling (random masks,
the original photo is the answer). Same data as train.py (ld-* designs + lp-* photo posters).

Generator: U-Net with gated convolutions and a dilated bottleneck (large view, small file), input = picture with
the hole cleared + the hole mask; output = the filled picture (only the hole is replaced).
Loss: L1 (hole weighted) + VGG perceptual + hinge PatchGAN (switched on after the first epoch), so the fill is sharp,
not a blurry average. Exports shoof-fill.onnx (fp32) and shoof-fill-fp16.onnx (<= 25 MB for Cloudflare).

  python3 tools/layerdata/train_fill.py --data /kaggle/temp/ld --out /kaggle/working --epochs 10 --size 512
"""
import argparse, json, math, os, random, sys, time
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from train import load_design, compose, top_set, full, REAL

# ---------------------------------------------------------------- data
def peel_pair(folder, rnd):
    """(picture, hole mask, true picture behind) for one random peel of a design / photo poster"""
    W, H, L = load_design(folder)
    rem = list(L)
    rounds = []
    while len(rounds) < 12:
        t = top_set(rem, W, H)
        if not t:
            break
        rounds.append((list(rem), t))
        rem = [l for i, l in enumerate(rem) if i not in t]
    if not rounds:
        return None
    rem, t = rnd.choice(rounds)
    # lifting only some of the top items is also a real use (Lift one object)
    keep = [i for i in t if rnd.random() < 0.7] or [rnd.choice(sorted(t))]
    img = compose(rem, W, H)
    after = [l for i, l in enumerate(rem) if i not in keep]
    tgt = compose(after, W, H)
    m = np.zeros((H, W), np.float32)
    for i in keep:
        m = np.maximum(m, full(rem[i], W, H)[..., 3])
    return img, (m > 0.02).astype(np.float32), tgt


def stroke_mask(W, H, rnd):
    """free-form brush strokes + blobs (what people paint with the magic eraser)"""
    im = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(im)
    for _ in range(rnd.randint(1, 4)):
        x, y = rnd.randint(0, W), rnd.randint(0, H)
        wd = rnd.randint(max(4, W // 40), max(6, W // 8))
        for _ in range(rnd.randint(2, 8)):
            a = rnd.uniform(0, 2 * math.pi)
            ln = rnd.randint(W // 20, W // 4)
            x2, y2 = int(x + ln * math.cos(a)), int(y + ln * math.sin(a))
            d.line((x, y, x2, y2), fill=255, width=wd)
            d.ellipse((x2 - wd // 2, y2 - wd // 2, x2 + wd // 2, y2 + wd // 2), fill=255)
            x, y = x2, y2
    if rnd.random() < 0.5:
        w, h = rnd.randint(W // 8, W // 2), rnd.randint(H // 8, H // 2)
        x, y = rnd.randint(0, W - w), rnd.randint(0, H - h)
        d.ellipse((x, y, x + w, y + h), fill=255) if rnd.random() < 0.5 else d.rectangle((x, y, x + w, y + h), fill=255)
    return np.asarray(im, np.float32) / 255.0


def shape_mask(W, H, rnd, shapes):
    """the outline of a real object (from another sample's layer), placed somewhere on this picture"""
    if not shapes:
        return stroke_mask(W, H, rnd)
    a = rnd.choice(shapes)
    s = rnd.uniform(0.25, 0.8) * min(W / a.width, H / a.height)
    a = a.resize((max(4, int(a.width * s)), max(4, int(a.height * s))))
    out = Image.new('L', (W, H), 0)
    out.paste(a, (rnd.randint(0, max(0, W - a.width)), rnd.randint(0, max(0, H - a.height))))
    return np.asarray(out, np.float32) / 255.0


def photo_pair(folder, rnd, shapes):
    """real photo with a made-up hole: the photo itself is the answer"""
    m = json.load(open(os.path.join(folder, 'meta.json')))
    bg = [l for l in m['layers'] if l['type'] == 'bg'][0]
    img = np.asarray(Image.open(os.path.join(folder, bg['file'])).convert('RGB'), np.float32) / 255.0
    H, W = img.shape[:2]
    mk = shape_mask(W, H, rnd, shapes) if rnd.random() < 0.6 else stroke_mask(W, H, rnd)
    return img, (mk > 0.5).astype(np.float32), img


def dilate(m, px):
    if px <= 0:
        return m
    im = Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(px * 2 + 1))
    return np.asarray(im, np.float32) / 255.0


def crop_pair(img, m, tgt, size, rnd):
    """scale so the short side ~ size (sometimes smaller = more context), crop a size x size window over the hole"""
    H, W = m.shape
    s = size / min(H, W) * rnd.uniform(0.8, 1.3)
    nw, nh = max(size, int(W * s)), max(size, int(H * s))
    f = lambda a, mode: np.asarray(Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).resize((nw, nh), mode), np.float32) / 255.0
    img, tgt, m = f(img, Image.BICUBIC), f(tgt, Image.BICUBIC), (f(m, Image.BILINEAR) > 0.3).astype(np.float32)
    ys, xs = np.where(m > 0)
    if len(xs) and rnd.random() < 0.85:
        cx, cy = int(rnd.choice(xs)), int(rnd.choice(ys))
        x0 = min(max(0, cx - rnd.randint(size // 4, 3 * size // 4)), nw - size)
        y0 = min(max(0, cy - rnd.randint(size // 4, 3 * size // 4)), nh - size)
    else:
        x0, y0 = rnd.randint(0, nw - size), rnd.randint(0, nh - size)
    c = lambda a: a[y0:y0 + size, x0:x0 + size]
    return c(img), c(m), c(tgt)


class FillData:
    def __init__(s, dirs, size, seed=0):
        s.dirs, s.size, s.seed = dirs, size, seed
        s.shapes = []

    def __len__(s):
        return len(s.dirs)

    def __getitem__(s, i):
        import torch
        rnd = random.Random(s.seed * 1000003 + i * 7 + int(time.time() * 1000) % 997)
        for tries in range(6):
            d = s.dirs[(i + tries * 7919) % len(s.dirs)]
            try:
                meta = json.load(open(os.path.join(d, 'meta.json')))
                if meta.get('real') or (meta.get('src') == 'photo' and rnd.random() < 0.3):
                    p = photo_pair(d, rnd, s.shapes)
                else:
                    p = peel_pair(d, rnd)
                    if p is not None and len(s.shapes) < 400 and p[1].mean() > 0.01:
                        s.shapes.append(Image.fromarray((p[1] * 255).astype(np.uint8)).crop(Image.fromarray((p[1] * 255).astype(np.uint8)).getbbox()))
                if p is None or p[1].sum() < 16:
                    continue
                img, m, tgt = p
                m = dilate(m, rnd.randint(1, 6))          # Shoof grows holes a little before filling
                img, m, tgt = crop_pair(img, m, tgt, s.size, rnd)
                if m.mean() < 0.003 or m.mean() > 0.7:
                    continue
                t = lambda a: torch.from_numpy(np.ascontiguousarray(a)).permute(2, 0, 1).float()
                return t(img), torch.from_numpy(m)[None].float(), t(tgt)
            except Exception:
                continue
        z = np.zeros((s.size, s.size, 3), np.float32)
        mm = np.zeros((1, s.size, s.size), np.float32); mm[:, :8, :8] = 1
        import torch
        return torch.from_numpy(z).permute(2, 0, 1), torch.from_numpy(mm), torch.from_numpy(z).permute(2, 0, 1)


# ---------------------------------------------------------------- model
def build_gen(base=32):
    import torch, torch.nn as nn

    class Gated(nn.Module):
        def __init__(s, cin, cout, k=3, st=1, dil=1):
            super().__init__()
            p = dil * (k - 1) // 2
            s.f = nn.Conv2d(cin, cout, k, st, p, dilation=dil)
            s.g = nn.Conv2d(cin, cout, k, st, p, dilation=dil)
            s.n = nn.InstanceNorm2d(cout, affine=True)

        def forward(s, x):
            return s.n(nn.functional.elu(s.f(x)) * torch.sigmoid(s.g(x)))

    class Res(nn.Module):
        def __init__(s, c, dil):
            super().__init__()
            s.a, s.b = Gated(c, c, 3, 1, dil), Gated(c, c, 3, 1, 1)

        def forward(s, x):
            return x + s.b(s.a(x))

    class Up(nn.Module):
        def __init__(s, cin, cskip, cout):
            super().__init__()
            s.c = Gated(cin + cskip, cout)

        def forward(s, x, skip):
            x = nn.functional.interpolate(x, size=skip.shape[-2:], mode='nearest')
            return s.c(torch.cat([x, skip], 1))

    class G(nn.Module):
        def __init__(s):
            super().__init__()
            b = base
            s.e0 = Gated(4, b, 5)                 # 1
            s.e1 = Gated(b, b * 2, 3, 2)          # 1/2
            s.e2 = Gated(b * 2, b * 4, 3, 2)      # 1/4
            c = b * 6                             # 192: keeps the fp16 file well under 25 MB
            s.e3 = Gated(b * 4, c, 3, 2)          # 1/8
            s.e4 = Gated(c, c, 3, 2)              # 1/16
            s.mid = nn.Sequential(*[Res(c, d) for d in (2, 4, 8, 16, 4)])
            s.u3 = Up(c, c, c)
            s.u2 = Up(c, b * 4, b * 4)
            s.u1 = Up(b * 4, b * 2, b * 2)
            s.u0 = Up(b * 2, b, b)
            s.out = nn.Conv2d(b, 3, 3, 1, 1)

        def forward(s, img, mask):
            """img 0..1 (B,3,H,W), mask 1 = hole (B,1,H,W); H, W multiples of 16"""
            x = torch.cat([img * (1 - mask) * 2 - 1, mask], 1)
            e0 = s.e0(x); e1 = s.e1(e0); e2 = s.e2(e1); e3 = s.e3(e2); e4 = s.mid(s.e4(e3))
            y = s.u0(s.u1(s.u2(s.u3(e4, e3), e2), e1), e0)
            y = (torch.tanh(s.out(y)) + 1) / 2
            return img * (1 - mask) + y * mask

    return G()


def build_disc(base=48):
    import torch.nn as nn
    sn = nn.utils.spectral_norm
    L = []
    c = 4
    for i, o in enumerate((base, base * 2, base * 4, base * 8)):
        L += [sn(nn.Conv2d(c, o, 4, 2 if i < 3 else 1, 1)), nn.LeakyReLU(0.2, True)]
        c = o
    L += [sn(nn.Conv2d(c, 1, 4, 1, 1))]
    return nn.Sequential(*L)


class VGGLoss:
    def __init__(s, dev):
        import torch, torchvision
        try:
            v = torchvision.models.vgg16(weights=torchvision.models.VGG16_Weights.IMAGENET1K_V1).features[:23].to(dev).eval()
        except Exception:
            v = None                               # no internet: perceptual loss off
        s.v = v
        if v is not None:
            for p in v.parameters():
                p.requires_grad = False
        s.mu = torch.tensor([0.485, 0.456, 0.406], device=dev).view(1, 3, 1, 1)
        s.sd = torch.tensor([0.229, 0.224, 0.225], device=dev).view(1, 3, 1, 1)

    def __call__(s, a, b):
        import torch
        if s.v is None:
            return a.new_zeros(())
        x, y = (a - s.mu) / s.sd, (b - s.mu) / s.sd
        loss = 0
        for i, layer in enumerate(s.v):
            x, y = layer(x), layer(y)
            if i in (3, 8, 15, 22):
                loss = loss + torch.nn.functional.l1_loss(x, y)
        return loss


# ---------------------------------------------------------------- train
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--epochs', type=int, default=10)
    ap.add_argument('--batch', type=int, default=12)
    ap.add_argument('--size', type=int, default=512)
    ap.add_argument('--lr', type=float, default=2e-4)
    ap.add_argument('--workers', type=int, default=4)
    ap.add_argument('--limit', type=int, default=0)
    ap.add_argument('--hours', type=float, default=10.5, help='stop and export before Kaggle\'s 12 h limit')
    a = ap.parse_args()
    import torch
    os.makedirs(a.out, exist_ok=True)
    dev = 'cuda' if torch.cuda.is_available() else 'cpu'
    dirs = sorted(os.path.join(a.data, d) for d in os.listdir(a.data) if os.path.exists(os.path.join(a.data, d, 'meta.json')))
    random.Random(0).shuffle(dirs)
    if a.limit:
        dirs = dirs[:a.limit]
    nval = max(8, len(dirs) // 100)
    val, tr = dirs[:nval], dirs[nval:]
    print(len(tr), 'train,', len(val), 'check', dev, flush=True)
    G, D = build_gen().to(dev), build_disc().to(dev)
    print('generator', sum(p.numel() for p in G.parameters()) / 1e6, 'M params')
    if torch.cuda.device_count() > 1:
        Gp, Dp = torch.nn.DataParallel(G), torch.nn.DataParallel(D)
    else:
        Gp, Dp = G, D
    og = torch.optim.AdamW(G.parameters(), a.lr, betas=(0.5, 0.9))
    od = torch.optim.AdamW(D.parameters(), a.lr, betas=(0.5, 0.9))
    vgg = VGGLoss(dev)
    dl = torch.utils.data.DataLoader(FillData(tr, a.size, 1), batch_size=a.batch, shuffle=True, num_workers=a.workers, drop_last=True, persistent_workers=a.workers > 0)
    vdl = torch.utils.data.DataLoader(FillData(val, a.size, 99), batch_size=a.batch, num_workers=0)
    t0, best, step = time.time(), 1e9, 0
    for ep in range(a.epochs):
        G.train(); D.train()
        adv_on = ep >= 1
        for img, m, tgt in dl:
            img, m, tgt = img.to(dev), m.to(dev), tgt.to(dev)
            out = Gp(img, m)
            if adv_on:
                od.zero_grad()
                dr = Dp(torch.cat([tgt, m], 1)); df = Dp(torch.cat([out.detach(), m], 1))
                ld = torch.relu(1 - dr).mean() + torch.relu(1 + df).mean()
                ld.backward(); od.step()
            og.zero_grad()
            hole = (torch.abs(out - tgt) * m).sum() / (m.sum() * 3 + 1)
            valid = (torch.abs(out - tgt) * (1 - m)).mean()
            lg = 6 * hole + valid + 0.1 * vgg(out, tgt)
            if adv_on:
                lg = lg + 0.01 * (-Dp(torch.cat([out, m], 1)).mean())
            lg.backward(); og.step()
            step += 1
            if step % 200 == 0:
                print(f'ep {ep} step {step} hole L1 {hole.item():.4f} {(time.time() - t0) / 3600:.2f} h', flush=True)
            if time.time() - t0 > a.hours * 3600:
                break
        G.eval()
        with torch.no_grad():
            err = []
            for img, m, tgt in vdl:
                img, m, tgt = img.to(dev), m.to(dev), tgt.to(dev)
                out = G(img, m)
                err.append(((torch.abs(out - tgt) * m).sum() / (m.sum() * 3 + 1)).item())
        e = float(np.mean(err))
        print(f'== epoch {ep}: hole error {e:.4f} (lower is better)', flush=True)
        torch.save(G.state_dict(), os.path.join(a.out, 'fill-last.pt'))
        if e < best:
            best = e
            torch.save(G.state_dict(), os.path.join(a.out, 'fill-best.pt'))
        if time.time() - t0 > a.hours * 3600:
            print('time limit reached, exporting')
            break
    # the adversarial phase can raise L1 a little while looking sharper: export the last one, keep best too
    G.load_state_dict(torch.load(os.path.join(a.out, 'fill-last.pt'), map_location=dev))
    export(G.cpu().eval(), a.out)
    preview(G, vdl, a.out)
    json.dump({'best_hole_error': best, 'epochs_done': ep + 1, 'train': len(tr)}, open(os.path.join(a.out, 'fill-report.json'), 'w'), indent=1)
    print('done')


def export(G, out):
    import torch
    x = torch.rand(1, 3, 512, 512); m = torch.zeros(1, 1, 512, 512); m[..., 200:300, 200:300] = 1
    p = os.path.join(out, 'shoof-fill.onnx')
    torch.onnx.export(G, (x, m), p, input_names=['image', 'mask'], output_names=['filled'], opset_version=17,
                      dynamic_axes={'image': {2: 'h', 3: 'w'}, 'mask': {2: 'h', 3: 'w'}, 'filled': {2: 'h', 3: 'w'}}, dynamo=False)
    try:
        import onnx
        from onnxconverter_common import float16
        mm = float16.convert_float_to_float16(onnx.load(p), keep_io_types=True)
        onnx.save(mm, os.path.join(out, 'shoof-fill-fp16.onnx'))
    except Exception as ex:
        print('fp16 skipped', ex)
    print('saved', p, os.path.getsize(p) // 1024, 'KB')


def preview(G, vdl, out):
    import torch
    rows = []
    dev = next(G.parameters()).device
    with torch.no_grad():
        for img, m, tgt in vdl:
            o = G(img.to(dev), m.to(dev)).cpu()
            for k in range(min(6, img.shape[0])):
                holed = img[k] * (1 - m[k]) + m[k] * torch.tensor([1., 0, 1]).view(3, 1, 1)
                rows.append(torch.cat([holed, o[k], tgt[k]], 2))
            break
    if rows:
        g = torch.cat(rows, 1).permute(1, 2, 0).numpy()
        Image.fromarray((np.clip(g, 0, 1) * 255).astype(np.uint8)).save(os.path.join(out, 'fill-preview.png'))


if __name__ == '__main__':
    main()
