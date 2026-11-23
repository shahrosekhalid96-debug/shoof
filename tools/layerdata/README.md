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
