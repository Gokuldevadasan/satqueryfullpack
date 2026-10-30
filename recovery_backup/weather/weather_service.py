import os
import requests

WMO={0:'Clear sky',1:'Mainly clear',2:'Partly cloudy',3:'Overcast',45:'Fog',48:'Rime fog',51:'Light drizzle',53:'Moderate drizzle',55:'Dense drizzle',61:'Slight rain',63:'Moderate rain',65:'Heavy rain',71:'Slight snow fall',73:'Moderate snow fall',75:'Heavy snow fall',80:'Slight rain showers',81:'Moderate rain showers',82:'Violent rain showers',95:'Thunderstorm',96:'Thunderstorm with slight hail',99:'Thunderstorm with heavy hail'}

def current_weather(latitude, longitude, base_url=None, api_key=None, timeout=8):
    """Open-Meteo default needs no key; custom APIs may be configured by environment."""
    url=base_url or os.getenv("WEATHER_API_URL", "https://api.open-meteo.com/v1/forecast")
    params={"latitude":latitude,"longitude":longitude,"current":"temperature_2m,apparent_temperature,relative_humidity_2m,wind_speed_10m,wind_direction_10m,wind_gusts_10m,precipitation,rain,cloud_cover,surface_pressure,weather_code,is_day","temperature_unit":"celsius","wind_speed_unit":"kmh"}
    if api_key or os.getenv("WEATHER_API_KEY"): params["apikey"]=api_key or os.getenv("WEATHER_API_KEY")
    try:
        response=requests.get(url,params=params,timeout=timeout); response.raise_for_status(); c=response.json().get("current",{}) ; code=c.get('weather_code')
        return {"available":True,"temperature":c.get("temperature_2m"),"feels_like":c.get("apparent_temperature"),"humidity":c.get("relative_humidity_2m"),"wind":c.get("wind_speed_10m"),"wind_direction":c.get('wind_direction_10m'),"wind_gust":c.get('wind_gusts_10m'),"pressure":c.get('surface_pressure'),"precipitation":c.get("precipitation"),"rain":c.get('rain'),"cloud_cover":c.get("cloud_cover"),"weather_code":code,"weather_description":WMO.get(code,'Unknown weather condition'),"condition":WMO.get(code,'Unknown weather condition'),"is_day":c.get('is_day'),"source":"Open-Meteo","note":"Temperature is air temperature, not land surface temperature."}
    except requests.exceptions.RequestException as exc: return {"available":False,"error":str(exc),"note":"Temperature is air temperature, not land surface temperature."}
