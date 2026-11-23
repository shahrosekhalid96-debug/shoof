#!/usr/bin/env python3
"""Train Shoof's "top layer" model on data from tools/layerdata/gen.py (LayerD-style decomposition, ICCV 2025).

Idea (same as LayerD): a design is taken apart by repeatedly finding the layers that nothing covers ("top layers"),
lifting them off, filling what was behind them, and repeating. This model does the finding. For every training
example we pick a random point in that peeling process, rebuild the picture exactly from the layers, and ask for
3 masks of the current top layers:
  0 = top-layer matte (soft edges kept)      1 = their drop shadows / glows      2 = which of them are text
The model is small enough for the browser (MobileNetV3 U-Net, ~5M weights): exported to ONNX fp32 + fp16.

  python3 tools/layerdata/train.py --data /tmp/ld --out /tmp/run --epochs 12 --batch 24 [--size 512] [--pretrained]
"""
import argparse, glob, io, json, math, os, random, time
import numpy as np
from PIL import Image, ImageFilter

OCC = 0.06          # alpha above this covers what is underneath
OVERLAP = 0.004     # a layer is not on top if more than this share of it is covered


# ---------------------------------------------------------------- data
def load_design(folder):
    m = json.load(open(os.path.join(folder, 'meta.json')))
    W, H = m['w'], m['h']
    L = []
    for i, l in enumerate(m['layers']):
        im = np.asarray(Image.open(os.path.join(folder, l['file'])).convert('RGBA'), dtype=np.float32) / 255.0
        if l['type'] == 'bg':
            x, y = 0, 0
        else:
            x, y = l['box']['x'], l['box']['y']
        L.append(dict(m=l, im=im, x=x, y=y))
    return W, H, L


def full(l, W, H):
    a = np.zeros((H, W, 4), np.float32)
    h, w = l['im'].shape[:2]
    a[l['y']:l['y'] + h, l['x']:l['x'] + w] = l['im'][:max(0, min(h, H - l['y'])), :max(0, min(w, W - l['x']))]
    return a


def compose(layers, W, H):
    out = np.ones((H, W, 3), np.float32)
    for l in layers:
        h, w = l['im'].shape[:2]
        h2, w2 = min(h, H - l['y']), min(w, W - l['x'])
        if h2 <= 0 or w2 <= 0:
            continue
        s = l['im'][:h2, :w2]
        a = s[..., 3:4]
        r = out[l['y']:l['y'] + h2, l['x']:l['x'] + w2]
        out[l['y']:l['y'] + h2, l['x']:l['x'] + w2] = s[..., :3] * a + r * (1 - a)
    return out


def top_set(rem, W, H):
    """indexes (into rem) of layers nothing covers; a shadow counts with the item that casts it"""
    owner = {l['m'].get('id'): i for i, l in enumerate(rem) if l['m'].get('id')}
    occ = np.zeros((H, W), bool)          # everything above, built from the top down
    top = set()
    for i in range(len(rem) - 1, -1, -1):
        l = rem[i]
        if l['m']['type'] == 'bg':
            continue
        h, w = l['im'].shape[:2]
        h2, w2 = min(h, H - l['y']), min(w, W - l['x'])
        if h2 <= 0 or w2 <= 0:
            continue
        mine = l['im'][:h2, :w2, 3] > OCC
        n = mine.sum()
        cov = (mine & occ[l['y']:l['y'] + h2, l['x']:l['x'] + w2]).sum()
        if l['m']['type'] == 'shadow':
            o = owner.get(l['m'].get('of'))
            if o is not None and o in top:
                # covered only by its own item is fine
                oo = rem[o]
                oh, ow = oo['im'].shape[:2]
                own = np.zeros((H, W), bool)
                own[oo['y']:oo['y'] + oh, oo['x']:oo['x'] + ow] = oo['im'][:min(oh, H - oo['y']), :min(ow, W - oo['x']), 3] > OCC
                other = occ & ~own
                if (mine & other[l['y']:l['y'] + h2, l['x']:l['x'] + w2]).sum() <= max(4, OVERLAP * n):
                    top.add(i)
        elif n and cov <= max(4, OVERLAP * n):
            top.add(i)
        occ[l['y']:l['y'] + h2, l['x']:l['x'] + w2] |= mine
    return top


def make_example(folder, rnd):
    W, H, L = load_design(folder)
    rem = list(L)
    rounds = []
    while True:
        t = top_set(rem, W, H)
        if not t:
            break
        rounds.append(t)
        rem = [l for i, l in enumerate(rem) if i not in t]
        if len(rounds) > 12:
            break
    k = rnd.randrange(len(rounds)) if rounds else 0
    rem = list(L)
    for _ in range(k):
        t = top_set(rem, W, H)
        rem = [l for i, l in enumerate(rem) if i not in t]
    t = top_set(rem, W, H)
    img = compose(rem, W, H)
    tgt = np.zeros((H, W, 3), np.float32)
    for i in t:
        l = rem[i]
        a = full(l, W, H)[..., 3]
        c = 1 if l['m']['type'] == 'shadow' else 0
        tgt[..., c] = np.maximum(tgt[..., c], a)
        if l['m']['type'] == 'text':
            tgt[..., 2] = np.maximum(tgt[..., 2], (a > 0.3).astype(np.float32))
    return img, tgt


def augment(img, tgt, size, rnd):
    """letterbox to a square, random scale/crop, JPEG + blur noise on the input only"""
    H, W = img.shape[:2]
    s = size / max(H, W) * rnd.uniform(0.85, 1.25)
    nw, nh = max(8, int(W * s)), max(8, int(H * s))
    im = Image.fromarray((img * 255).astype(np.uint8)).resize((nw, nh), Image.BICUBIC)
    tg = [Image.fromarray((tgt[..., c] * 255).astype(np.uint8)).resize((nw, nh), Image.BILINEAR) for c in range(3)]
    canvas = Image.new('RGB', (size, size), tuple(int(v) for v in np.asarray(im)[0, 0]))
    ox = rnd.randint(min(0, size - nw), max(0, size - nw))
    oy = rnd.randint(min(0, size - nh), max(0, size - nh))
    canvas.paste(im, (ox, oy))
    tcs = []
    for t in tg:
        c = Image.new('L', (size, size), 0)
        c.paste(t, (ox, oy))
        tcs.append(np.asarray(c, np.float32) / 255.0)
    if rnd.random() < 0.6:
        b = io.BytesIO()
        canvas.save(b, 'JPEG', quality=rnd.randint(55, 95))
        canvas = Image.open(b).convert('RGB')
    if rnd.random() < 0.15:
        canvas = canvas.filter(ImageFilter.GaussianBlur(rnd.uniform(0.3, 1.0)))
    x = np.asarray(canvas, np.float32) / 255.0
    return x, np.stack(tcs, -1)


# ---------------------------------------------------------------- model
def build_model(pretrained):
    import torch, torch.nn as nn, torchvision
    w = torchvision.models.MobileNet_V3_Large_Weights.IMAGENET1K_V2 if pretrained else None
    enc = torchvision.models.mobilenet_v3_large(weights=w).features
    taps = [1, 3, 6, 12, 16]                 # strides 2, 4, 8, 16, 32
    chs = [16, 24, 40, 112, 960]

    class Up(nn.Module):
        def __init__(s, cin, cskip, cout):
            super().__init__()
            s.c = nn.Sequential(nn.Conv2d(cin + cskip, cout, 3, padding=1, bias=False), nn.BatchNorm2d(cout), nn.ReLU(inplace=True),
                                nn.Conv2d(cout, cout, 3, padding=1, bias=False), nn.BatchNorm2d(cout), nn.ReLU(inplace=True))

        def forward(s, x, skip):
            x = nn.functional.interpolate(x, size=skip.shape[-2:], mode='bilinear', align_corners=False)
            return s.c(torch.cat([x, skip], 1))

    class Net(nn.Module):
        def __init__(s):
            super().__init__()
            s.enc = enc
            s.mid = nn.Sequential(nn.Conv2d(960, 192, 1, bias=False), nn.BatchNorm2d(192), nn.ReLU(inplace=True))
            s.u4 = Up(192, 112, 128)
            s.u3 = Up(128, 40, 96)
            s.u2 = Up(96, 24, 64)
            s.u1 = Up(64, 16, 48)
            s.u0 = Up(48, 3, 32)              # full resolution, sees the picture itself for sharp edges
            s.head = nn.Conv2d(32, 3, 1)
            s.register_buffer('mean', torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1))
            s.register_buffer('std', torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1))

        def forward(s, x):                     # x: N,3,H,W in 0..1 -> N,3,H,W logits
            z = (x - s.mean) / s.std
            f = []
            for i, m in enumerate(s.enc):
                z = m(z)
                if i in taps:
                    f.append(z)
            y = s.mid(f[4])
            y = s.u4(y, f[3])
            y = s.u3(y, f[2])
            y = s.u2(y, f[1])
            y = s.u1(y, f[0])
            y = s.u0(y, x)
            return s.head(y)

    return Net()


# ---------------------------------------------------------------- training
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--epochs', type=int, default=12)
    ap.add_argument('--batch', type=int, default=24)
    ap.add_argument('--size', type=int, default=512)
    ap.add_argument('--lr', type=float, default=1e-3)
    ap.add_argument('--workers', type=int, default=4)
    ap.add_argument('--pretrained', action='store_true')
    ap.add_argument('--limit', type=int, default=0, help='use only this many designs (quick tests)')
    a = ap.parse_args()
    import torch, torch.nn as nn
    from torch.utils.data import Dataset, DataLoader
    os.makedirs(a.out, exist_ok=True)
    dirs = sorted(d for d in glob.glob(os.path.join(a.data, '**', 'meta.json'), recursive=True))
    dirs = [os.path.dirname(d) for d in dirs]
    random.Random(0).shuffle(dirs)
    if a.limit:
        dirs = dirs[:a.limit]
    nval = max(1, len(dirs) // 50)
    val, tr = dirs[:nval], dirs[nval:]
    print(f'{len(tr)} training designs, {len(val)} for checking', flush=True)

    class DS(Dataset):
        def __init__(s, ds, train):
            s.ds, s.train = ds, train

        def __len__(s):
            return len(s.ds)

        def __getitem__(s, i):
            rnd = random.Random() if s.train else random.Random(i)
            try:
                img, tgt = make_example(s.ds[i], rnd)
                x, y = augment(img, tgt, a.size, rnd)
            except Exception:
                x, y = np.ones((a.size, a.size, 3), np.float32), np.zeros((a.size, a.size, 3), np.float32)
            return torch.from_numpy(x).permute(2, 0, 1), torch.from_numpy(y).permute(2, 0, 1)

    dev = 'cuda' if torch.cuda.is_available() else 'cpu'
    net = build_model(a.pretrained).to(dev)
    print(f'{sum(p.numel() for p in net.parameters()) / 1e6:.1f}M weights on {dev}', flush=True)
    dl = DataLoader(DS(tr, True), batch_size=a.batch, shuffle=True, num_workers=a.workers, drop_last=True, persistent_workers=a.workers > 0)
    vl = DataLoader(DS(val, False), batch_size=a.batch, num_workers=a.workers)
    opt = torch.optim.AdamW(net.parameters(), lr=a.lr, weight_decay=1e-4)
    steps = a.epochs * max(1, len(dl))
    sch = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=a.lr, total_steps=steps, pct_start=0.1)
    scaler = torch.amp.GradScaler(enabled=dev == 'cuda')
    bce = nn.BCEWithLogitsLoss()

    def loss_fn(lo, y):
        p = torch.sigmoid(lo)
        inter = (p * y).sum((2, 3))
        dice = 1 - (2 * inter + 1) / (p.sum((2, 3)) + y.sum((2, 3)) + 1)
        # edges: weight the matte where the target changes, so letters keep crisp outlines
        gy = (y[:, :, 1:] - y[:, :, :-1]).abs()
        gp = (p[:, :, 1:] - p[:, :, :-1]).abs()
        return bce(lo, y) + dice.mean() + (p - y).abs().mean() + (gp - gy).abs().mean()

    def evaluate():
        net.eval()
        tot, ious, n = 0.0, np.zeros(3), 0
        with torch.no_grad():
            for x, y in vl:
                x, y = x.to(dev), y.to(dev)
                lo = net(x)
                tot += loss_fn(lo, y).item() * len(x)
                p = (torch.sigmoid(lo) > 0.5).float()
                yb = (y > 0.5).float()
                inter = (p * yb).sum((2, 3))
                uni = ((p + yb) > 0).float().sum((2, 3))
                ious += ((inter + 1) / (uni + 1)).sum(0).cpu().numpy()
                n += len(x)
        net.train()
        return tot / max(1, n), ious / max(1, n)

    best, t0, step = 9e9, time.time(), 0
    for ep in range(a.epochs):
        for x, y in dl:
            x, y = x.to(dev, non_blocking=True), y.to(dev, non_blocking=True)
            with torch.autocast(dev, enabled=dev == 'cuda'):
                lo = net(x)
            l = loss_fn(lo.float(), y)
            opt.zero_grad(set_to_none=True)
            scaler.scale(l).backward()
            scaler.step(opt)
            scaler.update()
            sch.step()
            step += 1
            if step % 50 == 0:
                print(f'epoch {ep + 1} step {step}/{steps} loss {l.item():.4f} {time.time() - t0:.0f}s', flush=True)
        vloss, iou = evaluate()
        print(f'== epoch {ep + 1}: check loss {vloss:.4f}  IoU top {iou[0]:.3f} shadow {iou[1]:.3f} text {iou[2]:.3f}', flush=True)
        if vloss < best:
            best = vloss
            torch.save(net.state_dict(), os.path.join(a.out, 'best.pt'))
    net.load_state_dict(torch.load(os.path.join(a.out, 'best.pt'), map_location=dev))
    export(net.cpu().eval(), a.out, a.size)
    preview(net, val[:6], a.out, a.size)
    json.dump({'best_check_loss': best, 'designs': len(dirs), 'epochs': a.epochs, 'size': a.size}, open(os.path.join(a.out, 'report.json'), 'w'))
    print('done', flush=True)


def export(net, out, size):
    import torch
    x = torch.rand(1, 3, size, size)
    p = os.path.join(out, 'shoof-layers.onnx')
    torch.onnx.export(net, x, p, input_names=['image'], output_names=['masks'], opset_version=17,
                      dynamic_axes={'image': {2: 'h', 3: 'w'}, 'masks': {2: 'h', 3: 'w'}}, dynamo=False)
    try:
        import onnx
        from onnxconverter_common import float16
        m = float16.convert_float_to_float16(onnx.load(p), keep_io_types=True)
        onnx.save(m, os.path.join(out, 'shoof-layers-fp16.onnx'))
    except Exception as ex:
        print('fp16 export skipped:', ex)
    print('saved', p, os.path.getsize(p) // 1024, 'KB', flush=True)


def preview(net, dirs, out, size):
    import torch
    rows = []
    for d in dirs:
        img, tgt = make_example(d, random.Random(1))
        x, y = augment(img, tgt, size, random.Random(2))
        with torch.no_grad():
            p = torch.sigmoid(net(torch.from_numpy(x).permute(2, 0, 1)[None]))[0].permute(1, 2, 0).numpy()
        tiles = [x] + [np.repeat(y[..., c:c + 1], 3, -1) for c in range(3)] + [np.repeat(p[..., c:c + 1], 3, -1) for c in range(3)]
        rows.append(np.concatenate(tiles, 1))
    Image.fromarray((np.concatenate(rows, 0) * 255).astype(np.uint8)).save(os.path.join(out, 'preview.png'))


if __name__ == '__main__':
    main()
