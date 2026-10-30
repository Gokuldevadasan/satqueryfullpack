import json

import cv2
import numpy as np

from .model_router import ROOT, select_model
from .model_loader import load_session

CLASSES_PATH = ROOT / "models" / "spectral_classes.json"


def predict_spectral(data):
    model_path = select_model("spectral")
    if model_path is None:
        return None

    session = load_session("spectral")
    input_shape = session.get_inputs()[0].shape
    height = input_shape[-2] if isinstance(input_shape[-2], int) else 64
    width = input_shape[-1] if isinstance(input_shape[-1], int) else 64
    resized = np.stack(
        [
            cv2.resize(band.astype(np.float32), (width, height), interpolation=cv2.INTER_LINEAR)
            for band in data
        ]
    )
    logits = session.run(
        None, {session.get_inputs()[0].name: resized[None].astype(np.float32)}
    )[0][0]
    probabilities = np.exp(logits - logits.max())
    probabilities /= probabilities.sum()
    classes = json.loads(CLASSES_PATH.read_text(encoding="utf-8"))
    if len(classes) != len(probabilities):
        raise ValueError("Spectral model output does not match the configured class labels.")
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
