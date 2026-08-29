import requests
import json
from datetime import datetime, timedelta

def get_coordinates(location_name):
    """Fetch latitude and longitude for a given location using OpenStreetMap Nominatim."""
    if not location_name:
        return None, "Location name cannot be empty."

    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": location_name,
        "format": "json",
        "limit": 1
    }
    headers = {
        "User-Agent": "WeatherGPT-App/1.0"
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if not data:
            return None, f"Location '{location_name}' not found. Please try a different location."
        
        lat = float(data[0]["lat"])
        lon = float(data[0]["lon"])
        display_name = data[0]["display_name"]
        return {"lat": lat, "lon": lon, "name": display_name}, None
    except Exception as e:
        return None, f"Error fetching location data: {str(e)}"

def get_weather_data(lat, lon):
    """Fetch current weather and 24h forecast from Open-Meteo."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": ["temperature_2m", "relative_humidity_2m", "apparent_temperature", "precipitation", "wind_speed_10m"],
        "hourly": ["precipitation"],
        "timezone": "auto",
        "forecast_days": 2
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        current = data.get("current", {})
        hourly = data.get("hourly", {})
        
        # Calculate next 24h cumulative precipitation
        current_time_str = current.get("time")
        precipitation_list = hourly.get("precipitation", [])
        time_list = hourly.get("time", [])
        
        predicted_rain_24h = 0.0
        
        if current_time_str and precipitation_list and time_list:
            try:
                # Find the index of the current time in the hourly array
                # The format is typically "YYYY-MM-DDTHH:00"
                start_index = 0
                for i, t in enumerate(time_list):
                    if t >= current_time_str:
                        start_index = i
                        break
                
                # Sum the next 24 hours (or up to available data)
                end_index = min(start_index + 24, len(precipitation_list))
                predicted_rain_24h = sum(precipitation_list[start_index:end_index])
            except Exception:
                pass

        weather_info = {
            "temperature": current.get("temperature_2m", 0),
            "feels_like": current.get("apparent_temperature", 0),
            "humidity": current.get("relative_humidity_2m", 0),
            "wind_speed": current.get("wind_speed_10m", 0),
            "current_precipitation": current.get("precipitation", 0),
            "predicted_rain_24h": round(predicted_rain_24h, 2)
        }
        return weather_info, None
    except Exception as e:
        return None, f"Error fetching weather data: {str(e)}"

def get_live_weather(city_name):
    """Fetch live weather for a city name. Returns a formatted dict or an error string."""
    coords, error = get_coordinates(city_name)
    if error:
        return error

    weather, err = get_weather_data(coords["lat"], coords["lon"])
    if err:
        return err

    return {
        "Temperature": f"{weather['temperature']} °C",
        "Feels Like": f"{weather['feels_like']} °C",
        "Humidity": f"{weather['humidity']} %",
        "Wind Speed": f"{weather['wind_speed']} km/h",
        "Current Precipitation": f"{weather['current_precipitation']} mm",
        "Predicted 24h Total Rain": f"{weather['predicted_rain_24h']} mm",
    }
