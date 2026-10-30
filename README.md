# SatQuery AI — overnight MVP

This is a practical edge-deployment baseline for the SatQuery AI challenge. It does **not** attempt to train a billion-parameter remote-sensing VLM overnight. Instead it:

1. Fine-tunes a small visual model (MobileNetV3-Small) on EuroSAT, an open remote-sensing dataset.
2. Exports the adapted visual component to ONNX for Raspberry Pi CPU inference.
3. Runs an agentic router that selects VQA, captioning, change detection, or optical–SAR fusion.
4. Returns structured evidence, confidence, execution trace, and generated change-map visuals to an existing UI.

The challenge text explicitly permits adaptation using open-source training data and requires single-image VQA, one extra single-image task, bi-temporal change analysis, optical–SAR analysis, and agentic tool/model orchestration.

## 1. Train on laptop / Colab

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements_train.txt
python train/train_eurosat.py --epochs 5 --batch 64
```

## SatQuery Medium (laptop/PC training only)

Run these commands from the repository root. Do not train on the Raspberry Pi. First inspect and validate the actual datasets:

```powershell
python scripts/inspect_datasets.py
python scripts/verify_datasets.py
```

Then train the RGB fine-tune or 13-band model, export ONNX, evaluate, and benchmark:

```powershell
python -m training.train_rgb_v11 --epochs 15 --batch-size 64 --lr 0.0003 --patience 7
python -m training.train_spectral --epochs 30 --batch-size 64 --lr 0.001 --patience 7
python -m scripts.export_onnx
python -m scripts.evaluate_model --checkpoint models/satquery_spectral_best.pt
python -m scripts.benchmark_models
```

For an ultra-fast rehearsal:

```bash
python train/train_eurosat.py --epochs 2 --batch 64 --limit 6000
```

The output will contain:

- `models/eurosat_mobilenet.onnx`
- `models/classes.json`
- `models/eurosat_mobilenet_best.pt`

## Run the SatQuery Medium application locally

From the repository root, start the canonical API:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload
```

In another terminal, start the frontend. Set its API URL before Next.js starts:

```powershell
$env:NEXT_PUBLIC_BACKEND_URL = "http://127.0.0.1:8000"
Set-Location frontend
npm.cmd run dev
```

The frontend sends each image to `POST /analyze` and displays the returned
terrain, GIS, spectral, water, vegetation, built-up, weather, and model values.
Verify the running API and analyze a real EuroSAT sample with:

```powershell
Set-Location ..
.\.venv\Scripts\python.exe scripts\test_satquery_medium.py
```

## 2. Copy these to Raspberry Pi

Copy the `backend/`, `models/`, and `outputs/` directories plus `requirements_pi.txt`.

On the Pi:

```bash
sudo apt update
sudo apt install -y python3-venv libgdal-dev
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements_pi.txt
```

Start the server:

```bash
uvicorn backend.app:app --host 0.0.0.0 --port 8000
```

Test:

```bash
curl http://127.0.0.1:8000/health
```

The analysis endpoint accepts one uploaded image at a time:

`http://<RASPBERRY_PI_IP>:8000/analyze`

with multipart fields:

- `image`: one GeoTIFF/TIFF/PNG/JPEG image

The structured response reports unavailable metadata and measurements as
`null`; it does not infer coordinates or spectral indices for ordinary RGB
images.

## 3. UI response

The dashboard displays the `satquery_version`, `input`, `terrain`,
`top_predictions`, `location`, `gis`, `water`, `vegetation`, `built_up`,
`spectral`, `weather`, and `model` fields returned by `/analyze`.

## 4. Recommended demo queries

Single image:
- `Describe the land-cover and major objects visible in this image.`
- `Is there water in this image?`
- `What is the dominant land-cover type?`

Two dates:
- `What changed between these two dates, and where did the change occur?`

Optical + SAR:
- `Use the optical and SAR images together to identify built-up and water-covered regions.`

## 5. Important limitations

- The EuroSAT classifier is a remote-sensing adaptation baseline, not a substitute for the challenge's final BigEarthNet/ISRO evaluation model.
- Optical index band positions must be configured for the actual dataset. Do not assume Cartosat band ordering.
- SAR backscatter thresholds are sensor- and preprocessing-dependent. The fusion code intentionally calls its result a heuristic/evidence estimate.
- The bi-temporal change detector is an image-difference tool, not a trained CDVQA model.
- For a production-quality submission, add BigEarthNet.txt/RSVQA/CDVQA fine-tuning and proper geospatial masks after the deadline.

## Medium safety notes

`POST /analyze` inspects band metadata before inference. A lone `B03.tif` is
reported as a single-band green raster and never duplicated into fake RGB.
NDVI needs B04+B08, NDWI needs B03+B08, and NDBI needs B11+B08. Coverage is a
configurable threshold-based estimate, not segmentation ground truth.

The current API accepts a single JPEG, PNG, TIFF, or GeoTIFF. For a Sentinel-2
scene, create an aligned stacked GeoTIFF whose band descriptions explicitly
name its bands; ZIP/multiple-file assembly is intentionally not inferred yet.
The default upload cap is 100 MiB and can be changed with
`SATQUERY_MAX_UPLOAD_BYTES`. On Raspberry Pi OS 64-bit, run one Uvicorn worker
and keep only the ONNX files plus `requirements_pi.txt`; do not install the
training requirements or run training on the Pi.
"# satqueryfullpack" 
