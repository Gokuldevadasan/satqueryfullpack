"""Explicit Sentinel-2 band identification and requirements."""
import re
from pathlib import Path

SENTINEL2 = {
    "B01": ("Coastal aerosol", 60), "B02": ("Blue", 10), "B03": ("Green", 10), "B04": ("Red", 10),
    "B05": ("Vegetation Red Edge", 20), "B06": ("Vegetation Red Edge", 20), "B07": ("Vegetation Red Edge", 20), "B08": ("NIR", 10), "B8A": ("Narrow NIR", 20), "B09": ("Water vapour", 60), "B10": ("Cirrus", 60), "B11": ("SWIR", 20), "B12": ("SWIR", 20),
}
_PATTERN = re.compile(r"(?:^|[^A-Z0-9])(B0[1-9]|B1[0-2]|B8A)(?:$|[^A-Z0-9])", re.I)

def canonical_band(value):
    if not value: return None
    found = _PATTERN.search(str(value).upper())
    return found.group(1).upper() if found else None

def band_details(band):
    name, resolution = SENTINEL2[band]
    return {"id": band, "name": name, "resolution_m": resolution, "sensor": "Sentinel-2"}

def identify_bands(path, descriptions=(), count=0, metadata=None):
    """Description/metadata take priority; a single-band filename is valid evidence."""
    metadata = metadata or {}; names=[]; mapping={}; details=[]; filename_band=canonical_band(Path(path).stem)
    for index in range(count):
        candidates=[descriptions[index] if index < len(descriptions) else None, metadata.get(f"band_{index + 1}"), metadata.get("band_name"), metadata.get("BANDNAME")]
        band=next((canonical_band(item) for item in candidates if canonical_band(item)),None)
        if band is None and count == 1: band=filename_band
        if band: mapping[band]=index; names.append(band); details.append(band_details(band))
        else: names.append(descriptions[index] if index < len(descriptions) and descriptions[index] else f"Band {index + 1}")
    return names,mapping,details

def required_message(index, available):
    required={"NDVI":("B04 (Red)","B08 (NIR)"),"NDWI":("B03 (Green)","B08 (NIR)"),"NDBI":("B11 (SWIR)","B08 (NIR)")}[index]
    missing=[item for item in required if item.split()[0] not in available]; received=", ".join(sorted(available)) or "no identified Sentinel-2 bands"
    return f"{index} unavailable: requires {' and '.join(required)}. Received {received}." if missing else None

def rgb_requirement(available):
    return None if {"B02","B03","B04"} <= set(available) else "RGB terrain classification requires B02 (Blue), B03 (Green), and B04 (Red)."
