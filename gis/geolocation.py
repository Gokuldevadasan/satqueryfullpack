"""Metadata-first location extraction; never infers a location from imagery."""
import math
from pathlib import Path

def valid_coordinates(latitude, longitude):
    return latitude is not None and longitude is not None and all(math.isfinite(float(x)) for x in (latitude, longitude)) and -90 <= float(latitude) <= 90 and -180 <= float(longitude) <= 180

def _exif_gps(path):
    from PIL import Image, ExifTags
    with Image.open(path) as image:
        raw=image.getexif(); gps=raw.get_ifd(ExifTags.IFD.GPSInfo) if raw else {}
    if not gps: return None
    names={ExifTags.GPSTAGS.get(key,key): value for key,value in gps.items()}
    def degrees(value):
        return float(value[0]) + float(value[1])/60 + float(value[2])/3600
    try:
        lat=degrees(names['GPSLatitude']); lon=degrees(names['GPSLongitude'])
        if names.get('GPSLatitudeRef')=='S': lat=-lat
        if names.get('GPSLongitudeRef')=='W': lon=-lon
        return (lat,lon) if valid_coordinates(lat,lon) else None
    except (KeyError, TypeError, ValueError, ZeroDivisionError): return None

def extract_geolocation(path, geo=None):
    path=Path(path)
    if path.suffix.lower() not in {'.tif','.tiff'}:
        coords=_exif_gps(path)
        if not coords: return {"latitude":None,"longitude":None,"place":None,"source":"unavailable","location_status":"unavailable","location_reason":"Image contains no GPS metadata"}
        return {"latitude":coords[0],"longitude":coords[1],"place":None,"source":"exif_gps","location_status":"coordinates_available","location_reason":None}
    if not geo or not geo.get('georeferenced'):
        return {"latitude":None,"longitude":None,"place":None,"source":"unavailable","location_status":"unavailable","location_reason":"Missing georeferencing"}
    try:
        from pyproj import Transformer
        b=geo['bounds']; x=(b[0]+b[2])/2; y=(b[1]+b[3])/2
        lon,lat=Transformer.from_crs(geo['crs'],'EPSG:4326',always_xy=True).transform(x,y)
        if not valid_coordinates(lat,lon): raise ValueError('Invalid transformed coordinates')
        return {"latitude":float(lat),"longitude":float(lon),"place":None,"source":"geotiff_center","location_status":"coordinates_available","location_reason":None,"crs":geo['crs'],"pixel_size_x":geo['pixel_size'][0] if geo.get('pixel_size') else None,"pixel_size_y":geo['pixel_size'][1] if geo.get('pixel_size') else None}
    except Exception as exc: return {"latitude":None,"longitude":None,"place":None,"source":"unavailable","location_status":"unavailable","location_reason":f"Location unavailable: {exc}"}
