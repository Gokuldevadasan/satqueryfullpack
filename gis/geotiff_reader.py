from pathlib import Path

def read_geotiff(path, read_data=True):
    import rasterio
    with rasterio.open(path) as ds:
        transform = ds.transform
        pixel_size = (abs(transform.a), abs(transform.e)) if transform and not transform.is_identity else None
        return {"path": str(path), "data": ds.read(masked=True) if read_data else None, "crs": str(ds.crs) if ds.crs else None, "transform": transform, "bounds": list(ds.bounds), "width": ds.width, "height": ds.height, "pixel_size": pixel_size, "metadata": ds.tags(), "band_count": ds.count, "nodata": ds.nodata, "descriptions": list(ds.descriptions), "colorinterp": [str(x) for x in ds.colorinterp], "georeferenced": bool(ds.crs and transform and not transform.is_identity)}
