import os
from dotenv import load_dotenv
from groq import Groq
from weather_service import get_coordinates, get_live_weather

# Load environment variables (local .env)
load_dotenv()

# Read API key — works both locally (.env) and on Streamlit Cloud (st.secrets)
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    try:
        import streamlit as st
        api_key = st.secrets.get("GROQ_API_KEY")
    except Exception:
        pass

client = Groq(api_key=api_key) if api_key else None

def evaluate_disaster_risk(weather_data):
    """
    Evaluates disaster alert thresholds from raw weather_data dict
    (keys: temperature, wind_speed, predicted_rain_24h, etc.)
    Returns (is_alert: bool, alert_reasons: list[str])
    """
    is_alert = False
    alert_reasons = []

    # Check predicted rain
    try:
        rain_val = float(weather_data.get("predicted_rain_24h", 0))
        if rain_val > 50.0:
            is_alert = True
            alert_reasons.append(
                f"High cumulative 24h rainfall predicted: {rain_val} mm (Threshold: >50mm). Risk of flash floods or waterlogging."
            )
    except Exception:
        pass

    # Check wind speed
    try:
        wind_val = float(weather_data.get("wind_speed", 0))
        if wind_val > 45.0:
            is_alert = True
            alert_reasons.append(
                f"High wind speeds detected: {wind_val} km/h (Threshold: >45 km/h). Potential structural hazards."
            )
    except Exception:
        pass

    return is_alert, alert_reasons


def initialize_weather_context(city_name):
    """
    Resolves coordinates, fetches live weather, calculates 24h rain trends,
    and evaluates disaster alert thresholds.
    """
    coords = get_coordinates(city_name)
    if not coords:
        return None, "Location not found", False, []
        
    weather_data = get_live_weather(city_name)
    if isinstance(weather_data, str):
        return coords, weather_data, False, []
        
    # Evaluate Disaster Thresholds
    is_alert = False
    alert_reasons = []
    
    # Check predicted rain
    rain_str = weather_data.get("Predicted 24h Total Rain", "0 mm")
    try:
        rain_val = float(rain_str.replace(" mm", ""))
        if rain_val > 50.0:
            is_alert = True
            alert_reasons.append(f"High cumulative 24h rainfall predicted: {rain_val} mm (Threshold: >50mm). Risk of flash floods or waterlogging.")
    except Exception:
        pass
        
    # Check wind speed
    wind_str = weather_data.get("Wind Speed", "0 km/h")
    try:
        wind_val = float(wind_str.replace(" km/h", ""))
        if wind_val > 45.0:
            is_alert = True
            alert_reasons.append(f"High wind speeds detected: {wind_val} km/h (Threshold: >45 km/h). Potential structural hazards.")
    except Exception:
        pass
        
    return coords, weather_data, is_alert, alert_reasons

def generate_weather_response(location_name, weather_data, language="English", is_alert=False, alert_reasons=None, user_message=""):
    if not client:
        return "Error: GROQ_API_KEY is missing from your .env file. Please add your API key."
        
    reasons_text = ", ".join(alert_reasons) if alert_reasons else "None"
    
    # Support both raw keys (from get_weather_data) and formatted keys (from get_live_weather)
    temperature      = weather_data.get('Temperature')      or f"{weather_data.get('temperature', 'N/A')} °C"
    feels_like       = weather_data.get('Feels Like')       or f"{weather_data.get('feels_like', 'N/A')} °C"
    humidity         = weather_data.get('Humidity')         or f"{weather_data.get('humidity', 'N/A')} %"
    wind_speed       = weather_data.get('Wind Speed')       or f"{weather_data.get('wind_speed', 'N/A')} km/h"
    current_precip   = weather_data.get('Current Precipitation') or f"{weather_data.get('current_precipitation', 'N/A')} mm"
    predicted_rain   = weather_data.get('Predicted 24h Total Rain') or f"{weather_data.get('predicted_rain_24h', 'N/A')} mm"

    system_prompt = f"""You are WeatherGPT, an advanced AI-driven Hyper-Local Early Warning System for natural disasters, floods, landslides, and agriculture (Smart India Hackathon Project). 

REAL-TIME & FORECAST TELEMETRY for {location_name}:
- Temperature: {temperature}
- Feels Like: {feels_like}
- Humidity: {humidity}
- Wind Speed: {wind_speed}
- Current Rain: {current_precip}
- Predicted 24-Hour Total Rain: {predicted_rain}
- Active Red Alert Status: {'ACTIVE' if is_alert else 'NORMAL'}
- Alert Factors: {reasons_text}

CRITICAL INSTRUCTIONS:
1. If 'Active Red Alert Status' is ACTIVE, prioritize issuing an urgent red-alert safety warning for potential floods, flash floods, or landslides.
2. EMERGENCY ACTION CHECKLIST: If high risk is detected, include markdown checkboxes ([ ]) detailing immediate safety protocols (securing livestock, moving to high ground, emergency rations).
3. MULTI-LINGUAL SUPPORT: Translate your entire response fluently into **{language}**. Keep meteorological values and numbers clear.
4. Answer the user's question accurately using only the provided live metrics. Never hallucinate.
"""

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message if user_message else "Provide a complete weather summary and safety check."}
            ],
            model="openai/gpt-oss-120b", 
            temperature=0.2 
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"AI Generation Error: {e}"