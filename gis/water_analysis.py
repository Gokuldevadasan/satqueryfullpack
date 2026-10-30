from .spectral_indices import ndwi
from .area_calculator import area_from_pixels
def analyze_water(data, pixel_size=None, crs=None, threshold=0.0, bands=None, classification=None):
    index, stats=ndwi(data,bands,threshold); mask=index>threshold; count=int(mask.sum())
    return {"water_detected":bool(count),"water_percentage":float(mask.mean()*100),"water_pixel_count":count,"water_area":area_from_pixels(count,pixel_size,crs),"ndwi":stats,"classification_hint":classification}
