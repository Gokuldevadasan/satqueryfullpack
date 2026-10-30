"""Area calculations that reject degree grids instead of treating degrees as metres."""
import numpy as np

def masked_area(mask, transform, crs):
    if transform is None or not crs:
        return {"square_meters": None, "square_kilometers": None, "reason": "Missing georeferencing"}
    try:
        from rasterio.crs import CRS
        parsed = CRS.from_user_input(crs)
        if parsed.is_geographic:
            return {"square_meters": None, "square_kilometers": None, "reason": "Geographic CRS requires geodesic area calculation"}
        # Projected CRS linear units are normally metres; conversion_factor handles feet too.
        unit = parsed.linear_units_factor[1] if parsed.linear_units_factor else 1.0
        pixel_m2 = abs(transform.a * transform.e) * unit * unit
        m2 = float(np.count_nonzero(mask) * pixel_m2)
        return {"square_meters": m2, "square_kilometers": m2 / 1_000_000, "reason": None}
    except Exception as exc:
        return {"square_meters": None, "square_kilometers": None, "reason": f"Area unavailable: {exc}"}
