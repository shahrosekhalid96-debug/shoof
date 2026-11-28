# Layer model data + training

Teaches Magic layers to take any poster apart into layers (LayerD idea, ICCV 2025: find the layers nothing covers, lift them, fill behind, repeat).

| File | What |
|---|---|
| `sample.js` | Runs inside the editor: builds a random design with Shoof's own engine and returns every layer as an exact RGBA picture + metadata (text words, font, size, weight, alignment, colour, spacing; drop shadows/glows as their own layer under the item). |
| `gen.py` | Driver: headless Chromium, many designs, layers saved cropped as lossless WebP + `meta.json`; `compose()` rebuilds the flat picture (matches the browser within ~0.2/255). |
| `photos.py` | Free CC0 / public-domain photos from Openverse for the designs (sources in `SOURCES.tsv`). |
| `train.py` | MobileNetV3 U-Net (~5M weights) → 3 masks: top-layer matte, their shadows, which are text. Exports `shoof-layers.onnx` (16 MB) and `-fp16` (8 MB). |
| `kaggle/1-make-data.ipynb`, `kaggle/2-train-model.ipynb` | Run on Kaggle (CPU for data, GPU T4 for training). |

Content: only Shoof templates / generated layouts, OFL fonts, Lucide icons and CC0 photos. Never scraped designs.

## Photos (round 2, 2026-11-24)
The first model saw only flat designs, so on photos it treated the whole picture as one layer. Round 2 adds photo posters:
- `cutouts.py` cuts people / animals / objects out of free CC0 photos with IS-Net (Shoof's background remover model), keeps only clean cut-outs (one main blob, crisp edge), cleans the old background colour off soft edges, and remembers where each sat (`<name>.json`).
- `photo_gen.py` builds posters with exact layers: photo background (colour graded) → cut-outs with their own drop shadow or rim light → text with glow / drop shadow / outline / gradient (glow and shadow are their own layers) → sometimes a flat badge. A third are **real** photos (`"real": true`): the original photo plus its own subject layer at the exact spot; the trainer only uses their first peel. Seeds start at 1,000,000 so they never clash with `gen.py`.
- Kaggle: `kaggle/3-make-photo-data.ipynb` (CPU, Internet on) → `lp-*.tar`; `2-train-model.ipynb` takes `ld-*.tar` and `lp-*.tar` together.
Shary's two test pictures are never used for training.

## Fill model (2026-11-28)
`train_fill.py` trains Shoof's own fill model (`shoof-fill-fp16.onnx`, ~20 MB): paints what was behind lifted layers. Ground truth comes for free from the layered data (picture at peel k → picture at peel k+1, exact); real photos add made-up holes (object outlines + brush strokes). Gated-conv U-Net with a dilated bottleneck, L1 + VGG perceptual + PatchGAN. Kaggle: `kaggle/4-train-fill.ipynb` (GPU, inputs = step 1 + step 1b, stops after 10.5 h). Plan in the app: Magic layers peels with the layer model and fills with this model, round after round, as one click; MI-GAN / PatchMatch stay as the fallback.

## Extra material from Shary (2026-11-28)
`extras.py` splits contact sheets into training material: `extra/photos/` (16 photos from his object grid, name pills cropped off; used as backgrounds) and `extra/cuts/` (22 objects from his cut-out sheet; the drawn checkerboard is removed with `dechecker`; headphones and mug dropped because their holes kept checker specks). Notebook 3 copies them in (cut-outs ×3).
