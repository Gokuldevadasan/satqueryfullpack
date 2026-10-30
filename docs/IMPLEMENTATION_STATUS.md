# SatQuery Medium implementation status

## Existing components found

FastAPI (`backend/app.py`), a Next.js dashboard, MobileNetV3 RGB/spectral
inference, GeoTIFF reading, training scripts, ONNX export, and dataset
inspection utilities were present. Existing model and dataset files were not
removed or overwritten.

## Problems identified and corrected

- The previous router classified every TIFF with three or fewer bands as RGB.
  A one-band `B03.tif` can no longer reach the RGB classifier.
- Band recognition now uses filenames and TIFF descriptions, and returns the
  identified bands, nodata, and georeferencing state.
- Spectral indices require explicitly identified Sentinel-2 bands. Their
  response includes an exact missing-band reason and safe, nodata-aware
  statistics (min/max/mean/median/valid pixels).
- NDWI water, NDVI vegetation, and NDBI built-up coverage are explicitly
  threshold-based estimates. Projected-grid areas are reported in metres;
  degree-grid areas are rejected rather than mislabelled as square metres.
- Weather and coordinate failures are isolated from imagery analysis. Weather
  is labelled air temperature, never land-surface temperature.
- Uploads are bounded by `SATQUERY_MAX_UPLOAD_BYTES` (100 MiB by default).

## Remaining external requirements

Reverse geocoding is not configured in this repository. Spectral scene
classification only runs with a compatible ONNX model and explicit band order.
No supervised pixel-segmentation dataset/masks were found, so no segmentation
claim is made. ZIP/multi-file scene assembly is not yet exposed by `/analyze`;
upload an aligned, explicitly described stacked GeoTIFF instead.

## Verification

Run `python -m unittest discover -s tests -v` and `python -m compileall backend gis inference` from the repository root. Results must be recorded from the actual environment; no training was initiated.
