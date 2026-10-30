import json, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from gis.geolocation import valid_coordinates
from weather.geocoding_service import reverse_geocode
from weather.weather_service import current_weather
if len(sys.argv)!=3: raise SystemExit('Usage: python scripts/test_location_weather.py <latitude> <longitude>')
lat,lon=map(float,sys.argv[1:]); print('SATQUERY LOCATION TEST\n\nLatitude:',lat,'\nLongitude:',lon)
if not valid_coordinates(lat,lon): raise SystemExit('RESULT: FAIL - invalid coordinates')
place=reverse_geocode(lat,lon); weather=current_weather(lat,lon)
print('\nREVERSE GEOCODING\n-----------------\n'+json.dumps(place,indent=2)); print('\nWEATHER\n-------\n'+json.dumps(weather,indent=2)); print('\nRESULT:', 'PASS' if weather.get('available') else 'PARTIAL (weather unavailable)')
