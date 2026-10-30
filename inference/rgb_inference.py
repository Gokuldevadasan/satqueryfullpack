import json

import numpy as np
from PIL import Image

from backend.rs_ops import make_preview
from .model_router import ROOT, select_model
from .model_loader import load_session

CLASSES_PATH = ROOT / "models" / "classes.json"


def predict_rgb(path, raster_data=None):
    model_path = select_model("rgb")
    if model_path is None:
        return None

    if raster_data is None:
        with Image.open(path) as source:
            image = source.convert("RGB").resize((224, 224), Image.Resampling.BILINEAR)
            rgb = np.asarray(image)
    else:
        # Callers pass an already ordered B04/B03/B02 composite.  Do not make
        # an arbitrary preview from the first three raster bands here.
        rgb = raster_data if raster_data.ndim == 3 and raster_data.shape[-1] == 3 else make_preview(raster_data)
        rgb = np.asarray(
            Image.fromarray(rgb).resize((224, 224), Image.Resampling.BILINEAR)
        )

    x = rgb.astype(np.float32) / 255.0
    x = (x - np.array([0.485, 0.456, 0.406], dtype=np.float32)) / np.array(
        [0.229, 0.224, 0.225], dtype=np.float32
    )
    x = np.transpose(x, (2, 0, 1))[None].astype(np.float32)

    session = load_session("rgb_v11" if model_path.name == "satquery_rgb_v11.onnx" else "rgb_v1")
    logits = session.run(None, {session.get_inputs()[0].name: x})[0][0]
    probabilities = np.exp(logits - logits.max())
    probabilities /= probabilities.sum()
    classes = json.loads(CLASSES_PATH.read_text(encoding="utf-8"))
    if len(classes) != len(probabilities):
        raise ValueError("RGB model output does not match the configured class labels.")
    order = np.argsort(probabilities)[::-1][:3]
    return {
        "label": classes[int(order[0])],
        "confidence": float(probabilities[order[0]]),
        "top_predictions": [
            {"class": classes[int(index)], "confidence": float(probabilities[index])}
            for index in order
        ],
        "model_path": str(model_path.relative_to(ROOT)),
        "backend": "onnxruntime",
    }
