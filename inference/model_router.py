from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODELS = {
    "rgb_v11": ROOT / "models" / "satquery_rgb_v11.onnx",
    "rgb_v1": ROOT / "models" / "eurosat_mobilenet.onnx",
    "spectral": ROOT / "models" / "satquery_spectral.onnx",
}
CHECKPOINTS = {
    "rgb_v11": ROOT / "models" / "satquery_rgb_v11.pt",
    "rgb_v1": ROOT / "models" / "eurosat_mobilenet_best.pt",
    "spectral": ROOT / "models" / "satquery_spectral_best.pt",
}


def route(path, band_count=None, band_map=None):
    suffix = Path(path).suffix.lower()
    if suffix in {".jpg", ".jpeg", ".png"}:
        return {"input_type": "rgb_image", "model_type": "rgb", "gis": False}
    if suffix in {".tif", ".tiff"}:
        if band_count == 3 and not band_map:
            return {"input_type": "multiband_raster", "model_type": None, "gis": True}
        if band_count >= 3 and set(band_map) >= {"B02", "B03", "B04"}:
            return {"input_type": "multiband_raster", "model_type": "rgb", "gis": True}
        if band_count == 1:
            return {"input_type": "single_band_raster", "model_type": None, "gis": True}
        return {
            "input_type": "multispectral",
            "model_type": "spectral" if band_count == 13 and band_map else None,
            "gis": True,
        }
    return {"input_type": "unsupported", "model_type": None, "gis": False}


def select_model(model_type):
    if model_type == "rgb":
        candidates = ("rgb_v11", "rgb_v1")
    elif model_type == "spectral":
        candidates = ("spectral",)
    else:
        return None
    return next((MODELS[key] for key in candidates if MODELS[key].is_file()), None)


def available_models():
    models = {}
    for key, onnx_path in MODELS.items():
        checkpoint = CHECKPOINTS[key]
        models[key] = {
            "available": onnx_path.is_file(),
            "path": str(onnx_path.relative_to(ROOT)) if onnx_path.is_file() else None,
            "checkpoint_available": checkpoint.is_file(),
            "checkpoint_path": str(checkpoint.relative_to(ROOT)) if checkpoint.is_file() else None,
            "backend": "onnxruntime" if onnx_path.is_file() else None,
        }
    return models
