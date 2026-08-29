# 🌪️ WeatherGPT — AI-Driven Hyper-Local Early Warning System

A real-time weather intelligence and disaster early-warning system built for **Smart India Hackathon (SIH26068)**.  
Powered by **Groq LLM**, **Open-Meteo**, and **OpenStreetMap**.

---

## Features

- 📍 Hyper-local weather for any city, village, or district in India
- ⚠️ Automatic red-alert for flood/wind disaster thresholds
- 🤖 AI-generated safety briefings via Groq LLM
- 🌐 Multi-lingual support (13 Indian languages)
- 📊 Live telemetry: temperature, humidity, wind, 24h rainfall prediction

---

## Run Locally

```bash
# 1. Clone the repo
git clone https://github.com/priyanshugupta-26/weather-gpt-groq.git
cd weather-gpt-groq

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add your API key
echo "GROQ_API_KEY=your_key_here" > .env

# 4. Run
streamlit run app.py
```

---

## Deploy on Streamlit Community Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io) and connect your GitHub account
2. Select this repo, branch `main`, and `app.py` as the entry point
3. Under **Advanced settings → Secrets**, add:
   ```
   GROQ_API_KEY = "your_groq_api_key_here"
   ```
4. Click **Deploy** — done!

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| LLM | Groq (LLaMA / GPT-OSS) |
| Weather API | Open-Meteo (free, no key needed) |
| Geocoding | OpenStreetMap Nominatim |
| Language | Python 3.10+ |
