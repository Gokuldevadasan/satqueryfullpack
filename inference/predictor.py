from pathlib import Path
import numpy as np
from PIL import Image
from gis.band_registry import identify_bands, required_message, rgb_requirement
from gis.area_analysis import masked_area
from gis.geotiff_reader import read_geotiff
from gis.geolocation import extract_geolocation
from gis.spectral_indices import ndvi, ndwi, ndbi
from weather.weather_service import current_weather
from weather.geocoding_service import reverse_geocode
from .model_router import route

WATER_THRESHOLD = 0.0
VEGETATION_THRESHOLD = 0.2
BUILT_UP_THRESHOLD = 0.0

def _weather_unavailable(error=None):
    result = {"available":False,"temperature_c":None,"apparent_temperature_c":None,"relative_humidity_percent":None,"wind_speed_kmh":None,"weather_code":None,"condition":None,"error":error,"note":"Temperature is air temperature, not land surface temperature."}
    return result

def _location(path, geo, diagnostics):
    loc=extract_geolocation(path,geo)
    if loc.get('latitude') is not None:
        print(f"[LOCATION] lat={loc['latitude']} lon={loc['longitude']}")
        place=reverse_geocode(loc['latitude'],loc['longitude'])
        print(f"[REVERSE GEOCODING] lat={loc['latitude']} lon={loc['longitude']} Place: {place.get('place')}")
        loc.update({key:value for key,value in place.items() if key != 'available'})
        if not place.get('available'):
            loc['location_status']='coordinates_available_reverse_geocode_failed'
            diagnostics.append({"service":"reverse_geocoding", "status":"failed", "message":place.get("error", "Unknown error")})
    return loc

def _prediction(kind,path,data):
    if not kind: return None,{"name":None,"type":None,"backend":None,"path":None,"status":"not_applicable"}
    try:
        if kind=="rgb":
            from .rgb_inference import predict_rgb; out=predict_rgb(path,data)
        else:
            from .spectral_inference import predict_spectral; out=predict_spectral(data)
    except Exception as e: out=None; error=str(e)
    if not out: return None,{"name":"MobileNetV3-Small","type":kind,"backend":None,"path":None,"status":"not_available","message":locals().get("error","No compatible ONNX model is available.")}
    return out,{"name":"MobileNetV3-Small","type":kind,"backend":out["backend"],"path":out["model_path"],"status":"available"}

def _index(name,data,mapping,fn,threshold):
    reason=required_message(name,mapping)
    if reason: return {"available":False,"reason":reason,"statistics":None,"threshold":threshold,"coverage_percent":None,"mask":None}
    bands={"red":mapping["B04"],"green":mapping["B03"],"nir":mapping["B08"],"swir":mapping.get("B11")}
    values,stats=fn(data,bands,threshold); mask=np.isfinite(values)&(values>threshold)
    return {"available":True,"reason":None,"statistics":stats,"threshold":threshold,"coverage_percent":stats["percentage_above_threshold"],"mask":mask}

def _rgb_composite(data, mapping):
    """Build an actual R=B04, G=B03, B=B02 display array for RGB inference."""
    channels = [np.ma.asarray(data[mapping[band]], dtype=np.float32).filled(np.nan) for band in ("B04", "B03", "B02")]
    rgb = []
    for channel in channels:
        finite = channel[np.isfinite(channel)]
        if not finite.size:
            raise ValueError("RGB composite contains no valid pixels")
        lo, hi = np.percentile(finite, (2, 98))
        scaled = np.zeros_like(channel, dtype=np.uint8) if hi <= lo else np.clip((channel - lo) * 255 / (hi - lo), 0, 255).astype(np.uint8)
        rgb.append(scaled)
    return np.stack(rgb, axis=-1)

def analyze(path, weather_fn=current_weather):
    path=Path(path); geo=data=None; names=[]; mapping={}; diagnostics=[]; errors=[]
    if path.suffix.lower() in {".tif",".tiff"}:
        geo=read_geotiff(path); data=geo["data"].astype(np.float32); count=geo["band_count"]; width,height=geo["width"],geo["height"]
        names,mapping,details=identify_bands(path,geo["descriptions"],count,geo.get("metadata"))
        if count==3 and {"ColorInterp.red","ColorInterp.green","ColorInterp.blue"}<=set(geo.get("colorinterp",[])): mapping={"B02":2,"B03":1,"B04":0}
    else:
        details=[]
        with Image.open(path) as im: width,height=im.size; count=len(im.getbands()); names=list(im.getbands())
    routed=route(path,count,mapping)
    rgb_data = _rgb_composite(data, mapping) if routed["model_type"] == "rgb" and data is not None else data
    prediction,model=_prediction(routed["model_type"],path,rgb_data)
    location=_location(path,geo,diagnostics)
    empty={"available":False,"reason":"Requires Sentinel-2 spectral bands; RGB images do not contain the required bands.","statistics":None,"threshold":None,"coverage_percent":None,"mask":None}; indexes={"ndvi":empty.copy(),"ndwi":empty.copy(),"ndbi":empty.copy()}
    if data is not None: indexes={"ndvi":_index("NDVI",data,mapping,ndvi,VEGETATION_THRESHOLD),"ndwi":_index("NDWI",data,mapping,ndwi,WATER_THRESHOLD),"ndbi":_index("NDBI",data,mapping,ndbi,BUILT_UP_THRESHOLD)}
    water={"available":indexes["ndwi"]["available"],"detected":None,"coverage_percent":indexes["ndwi"]["coverage_percent"],"pixel_count":None,"area_m2":None,"reason":indexes["ndwi"]["reason"],"threshold":WATER_THRESHOLD}
    area={"pixel_area_m2":None,"water_area_m2":None,"water_area_ha":None,"water_area_km2":None}
    if indexes["ndwi"]["mask"] is not None:
        count_pixels=int(np.count_nonzero(indexes["ndwi"]["mask"])); a=masked_area(indexes["ndwi"]["mask"],geo["transform"],geo["crs"]); water.update(detected=bool(count_pixels),pixel_count=count_pixels,area_m2=a["square_meters"])
        pixel_size=geo.get("pixel_size")
        if pixel_size and geo.get("georeferenced"):
            area.update(pixel_area_m2=abs(pixel_size[0]*pixel_size[1]),water_area_m2=a["square_meters"],water_area_ha=(a["square_meters"] / 10000 if a["square_meters"] is not None else None),water_area_km2=a["square_kilometers"])
    vegetation={"available":indexes["ndvi"]["available"],"mean_ndvi":(indexes["ndvi"]["statistics"] or {}).get("mean"),"coverage_percent":indexes["ndvi"]["coverage_percent"],"reason":indexes["ndvi"]["reason"],"threshold":VEGETATION_THRESHOLD}
    built={"available":indexes["ndbi"]["available"],"mean_ndbi":(indexes["ndbi"]["statistics"] or {}).get("mean"),"coverage_percent":indexes["ndbi"]["coverage_percent"],"reason":indexes["ndbi"]["reason"],"threshold":BUILT_UP_THRESHOLD}
    weather=_weather_unavailable()
    if location["latitude"] is not None and weather_fn:
        try:
            print(f"[WEATHER] Request: lat={location['latitude']} lon={location['longitude']}")
            w=weather_fn(location["latitude"],location["longitude"],timeout=10); weather.update(w)
            if not w.get("available"): diagnostics.append({"service":"weather", "status":"failed", "message":w.get("error", "Unknown error")})
        except Exception as e: weather=_weather_unavailable(str(e)); diagnostics.append({"service":"weather", "status":"failed", "message":str(e)})
    terrain_reason=rgb_requirement(mapping) if path.suffix.lower() in {".tif",".tiff"} else model.get("message")
    if not prediction and routed["model_type"] is not None: errors.append({"service":"terrain_model", "message":model.get("message", "Model inference unavailable")})
    terrain_reason = terrain_reason or "Terrain classification requires RGB imagery or a supported multiband RGB composite."
    raster={"crs":geo.get("crs") if geo else None,"pixel_size_x":geo.get("pixel_size", (None,None))[0] if geo and geo.get("pixel_size") else None,"pixel_size_y":geo.get("pixel_size", (None,None))[1] if geo and geo.get("pixel_size") else None,"transform":list(geo["transform"]) if geo else None,"bounds":geo.get("bounds") if geo else None,"center":{"latitude":location.get("latitude"),"longitude":location.get("longitude")}}
    print(f"[ANALYZE] type={routed['input_type']} bands={names} model={model.get('path')} indices={[k for k,v in indexes.items() if v['available']]}")
    return {"success":not errors,"status":"success" if not errors else "partial","input":{"filename":path.name,"type":routed["input_type"],"width":width,"height":height,"bands":names,"band_count":count},"terrain":{"available":bool(prediction),"label":prediction["label"] if prediction else None,"confidence":prediction["confidence"] if prediction else None,"top_predictions":prediction["top_predictions"] if prediction else [],"reason":None if prediction else terrain_reason},"location":location,"weather":weather,"raster":raster,"spectral":{"bands":names,"ndvi":{k:v for k,v in indexes['ndvi'].items() if k != 'mask'},"ndwi":{k:v for k,v in indexes['ndwi'].items() if k != 'mask'},"ndbi":{k:v for k,v in indexes['ndbi'].items() if k != 'mask'}},"analysis":{"water":water,"vegetation":vegetation,"built_up":built,"area":area,"depth":{"available":False,"reason":"Water depth requires elevation/depth data."}},"model":{"name":model.get("name"),"path":model.get("path"),"backend":model.get("backend"),"used":bool(prediction)},"errors":errors,"diagnostics":diagnostics}
