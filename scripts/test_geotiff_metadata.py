import json, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from gis.geotiff_reader import read_geotiff
from gis.geolocation import extract_geolocation
from weather.geocoding_service import reverse_geocode
from weather.weather_service import current_weather
if len(sys.argv)!=2: raise SystemExit('Usage: python scripts/test_geotiff_metadata.py path/to/B03.tif')
geo=read_geotiff(sys.argv[1],read_data=False); loc=extract_geolocation(sys.argv[1],geo)
print(json.dumps({'filename':Path(sys.argv[1]).name,'width':geo['width'],'height':geo['height'],'band_count':geo['band_count'],'crs':geo['crs'],'bounds':geo['bounds'],'transform':str(geo['transform']),'pixel_size':geo['pixel_size'],'location':loc},indent=2,default=str))
if loc.get('latitude') is not None:
    print('Reverse geocoding:',json.dumps(reverse_geocode(loc['latitude'],loc['longitude']),indent=2)); print('Weather:',json.dumps(current_weather(loc['latitude'],loc['longitude']),indent=2))
