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

def _weather_unavailable(note="Air temperature is unavailable; it is not land surface temperature."):
    return {"available":False,"temperature_c":None,"feels_like_c":None,"humidity_percent":None,"wind_kmh":None,"condition":None,"note":note}

def _location(path, geo):
    loc=extract_geolocation(path,geo); gis={"crs":geo.get("crs") if geo else None,"pixel_size":geo.get("pixel_size") if geo else None,"bounds":geo.get("bounds") if geo else None,"note":loc.get('location_reason')}
    if loc.get('latitude') is not None:
        print(f"[LOCATION] Input: {path.name}\nCRS: {gis['crs']}\nConverted WGS84: lat={loc['latitude']} lon={loc['longitude']}")
        place=reverse_geocode(loc['latitude'],loc['longitude'])
        print(f"[REVERSE GEOCODING] lat={loc['latitude']} lon={loc['longitude']} Place: {place.get('place')}")
        loc.update({key:value for key,value in place.items() if key != 'available'})
        if not place.get('available'): loc['location_status']='coordinates_available_reverse_geocode_failed'
    return loc,gis

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

def analyze(path, weather_fn=current_weather):
    path=Path(path); geo=data=None; names=[]; mapping={}; warnings=[]
    if path.suffix.lower() in {".tif",".tiff"}:
        geo=read_geotiff(path); data=geo["data"].astype(np.float32); count=geo["band_count"]; width,height=geo["width"],geo["height"]
        names,mapping,details=identify_bands(path,geo["descriptions"],count,geo.get("metadata"))
        if count==3 and {"ColorInterp.red","ColorInterp.green","ColorInterp.blue"}<=set(geo.get("colorinterp",[])): mapping={"B02":2,"B03":1,"B04":0}
    else:
        details=[]
        with Image.open(path) as im: width,height=im.size; count=len(im.getbands()); names=list(im.getbands())
    routed=route(path,count,mapping); prediction,model=_prediction(routed["model_type"],path,data)
    location,gis=_location(path,geo)
    empty={"available":False,"reason":None,"statistics":None,"threshold":None,"coverage_percent":None,"mask":None}; indexes={"ndvi":empty.copy(),"ndwi":empty.copy(),"ndbi":empty.copy()}
    if data is not None: indexes={"ndvi":_index("NDVI",data,mapping,ndvi,.2),"ndwi":_index("NDWI",data,mapping,ndwi,0),"ndbi":_index("NDBI",data,mapping,ndbi,0)}
    water={"detected":None,"coverage_percent":indexes["ndwi"]["coverage_percent"],"area_m2":None,"area_km2":None,"method":"NDWI threshold-based estimate","reason":indexes["ndwi"]["reason"],"depth":"Requires independent elevation/depth data","volume":"Requires independent elevation/depth data"}
    if indexes["ndwi"]["mask"] is not None:
        a=masked_area(indexes["ndwi"]["mask"],geo["transform"],geo["crs"]); water.update(detected=bool(np.any(indexes["ndwi"]["mask"])),area_m2=a["square_meters"],area_km2=a["square_kilometers"])
        if a["reason"]: water["area_reason"]=a["reason"]
    vegetation={"coverage_percent":indexes["ndvi"]["coverage_percent"],"ndvi":(indexes["ndvi"]["statistics"] or {}).get("mean"),"method":"NDVI threshold-based estimate","reason":indexes["ndvi"]["reason"]}
    built={"coverage_percent":indexes["ndbi"]["coverage_percent"],"ndbi":(indexes["ndbi"]["statistics"] or {}).get("mean"),"method":"NDBI threshold-based estimate","reason":indexes["ndbi"]["reason"]}
    weather=_weather_unavailable()
    if location["latitude"] is not None and weather_fn:
        try:
            print(f"[WEATHER] Request: lat={location['latitude']} lon={location['longitude']}")
            w=weather_fn(location["latitude"],location["longitude"],timeout=10); weather.update(available=bool(w.get("available")),temperature_c=w.get("temperature"),feels_like_c=w.get("feels_like"),humidity_percent=w.get("humidity"),wind_kmh=w.get("wind"),wind_speed_kmh=w.get("wind"),wind_direction_deg=w.get("wind_direction"),wind_gust_kmh=w.get("wind_gust"),pressure_hpa=w.get("pressure"),precipitation_mm=w.get("precipitation"),rain_mm=w.get("rain"),cloud_cover_percent=w.get("cloud_cover"),weather_code=w.get("weather_code"),weather_description=w.get("weather_description"),condition=w.get("weather_description") or w.get("condition"),source=w.get("source"),is_day=w.get("is_day"),note=w.get("note",weather["note"]));
            if w.get("error"): weather["error"]=w["error"]
        except Exception as e: weather.update(error=str(e),note="Weather service unavailable; image analysis completed.")
    terrain_reason=rgb_requirement(mapping) if path.suffix.lower() in {".tif",".tiff"} else model.get("message")
    if routed["model_type"] is None: warnings.append(terrain_reason or "Terrain classification was not run: input is not validated RGB or a compatible 13-band raster.")
    model["used"]=bool(prediction); model["reason"]=terrain_reason if not prediction else None
    return {"satquery_version":"Medium","status":"success" if prediction else "partial","message":model.get("message"),"warnings":warnings,"input":{"filename":path.name,"type":routed["input_type"],"bands":count,"width":width,"height":height,"band_names":names,"band_details":details,"georeferenced":bool(geo and geo["georeferenced"]),"nodata":geo.get("nodata") if geo else None},"terrain":{"class":prediction["label"] if prediction else None,"confidence":prediction["confidence"] if prediction else None,"top_predictions":prediction["top_predictions"] if prediction else [],"available":bool(prediction),"reason":terrain_reason if not prediction else None,"note":"Confidence is a model score, not guaranteed real-world accuracy."},"location":location,"gis":gis,"water":water,"vegetation":vegetation,"built_up":built,"spectral":{k:{x:y for x,y in v.items() if x!="mask"} for k,v in indexes.items()},"weather":weather,"model":model}
