def pixel_area_m2(pixel_size, crs=None):
    if not pixel_size or not crs or not str(crs).upper().startswith("EPSG:"): return None
    # Units are only certainly metres for projected CRS. Geographic degrees must not be guessed.
    code=str(crs).split(":")[-1]
    if code in {"4326","4269"}: return None
    return abs(pixel_size[0]*pixel_size[1])
def area_from_pixels(pixel_count, pixel_size, crs=None):
    per=pixel_area_m2(pixel_size,crs)
    if per is None: return {"square_meters":None,"hectares":None,"square_kilometers":None}
    m2=float(pixel_count*per); return {"square_meters":m2,"hectares":m2/10000,"square_kilometers":m2/1e6}
