"""Exercise the running SatQuery Medium API with real dataset imagery."""
import argparse
import json
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[1]


def find_rgb_sample():
    candidates = sorted(
        path
        for path in (ROOT / "data" / "EuroSAT").rglob("*")
        if path.is_file() and path.suffix.lower() in {".jpg", ".jpeg", ".png"}
    )
    if not candidates:
        raise FileNotFoundError("No RGB images were found under data/EuroSAT.")
    return candidates[0]


def analyze(base_url, image_path, timeout):
    with image_path.open("rb") as image_file:
        response = requests.post(
            f"{base_url.rstrip('/')}/analyze",
            files={"image": (image_path.name, image_file)},
            timeout=timeout,
        )
    response.raise_for_status()
    return response.json()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--image", type=Path, help="RGB test image; defaults to a EuroSAT RGB sample.")
    parser.add_argument("--spectral-image", type=Path, help="Optional 13-band GeoTIFF test image.")
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args()
    image_path = args.image or find_rgb_sample()

    health = requests.get(f"{args.base_url.rstrip('/')}/health", timeout=5)
    health.raise_for_status()
    model_info = requests.get(f"{args.base_url.rstrip('/')}/model-info", timeout=5)
    model_info.raise_for_status()
    result = analyze(args.base_url, image_path, args.timeout)
    output = {
        "health": health.json(),
        "model_info": model_info.json(),
        "image": str(image_path),
        "analysis": result,
    }
    if args.spectral_image:
        output["spectral_analysis"] = analyze(
            args.base_url, args.spectral_image, args.timeout
        )

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
