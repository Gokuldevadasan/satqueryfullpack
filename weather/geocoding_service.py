"""Nominatim reverse geocoding with a required identifying User-Agent."""
import requests
from gis.geolocation import valid_coordinates

def reverse_geocode(latitude, longitude, timeout=10):
    if not valid_coordinates(latitude,longitude): return {"available":False,"place":"Unknown","error":"Invalid coordinates"}
    try:
        response=requests.get('https://nominatim.openstreetmap.org/reverse',params={'format':'jsonv2','lat':latitude,'lon':longitude,'zoom':18,'addressdetails':1},headers={'User-Agent':'SatQuery-Medium/1.0 (local satellite analysis)'},timeout=timeout)
        response.raise_for_status(); body=response.json(); address=body.get('address',{})
        city=address.get('city') or address.get('town') or address.get('village') or address.get('municipality')
        state=address.get('state'); country=address.get('country'); place=', '.join(x for x in (city,state,country) if x) or body.get('display_name','Unknown')
        return {'available':True,'place':place,'city':city,'state':state,'country':country,'country_code':address.get('country_code'),'display_name':body.get('display_name')}
    except requests.exceptions.RequestException as exc: return {'available':False,'place':'Unknown','error':str(exc)}
