import streamlit as st
import weather_service
import rag_engine
import os

st.set_page_config(
    page_title="WeatherGPT: Early Warning System",
    page_icon="🌪️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Dark Mode and styling
st.markdown("""
<style>
    /* ── Nuclear dark mode: force every surface dark ── */
    html, body,
    .stApp,
    .stApp > div,
    .stApp > div > div,
    [data-testid="stAppViewContainer"],
    [data-testid="stAppViewContainer"] > div,
    [data-testid="stAppViewBlockContainer"],
    .block-container,
    .main,
    .main > div,
    section.main,
    section.main > div,
    [data-testid="stMainBlockContainer"],
    [data-testid="stVerticalBlock"],
    [data-testid="stVerticalBlockBorderWrapper"],
    .stChatFloatingInputContainer,
    [data-testid="stChatInputContainer"],
    [data-testid="stBottom"],
    [data-testid="stBottom"] > div {
        background-color: #0b0f19 !important;
        color: #f3f4f6 !important;
    }

    /* ── Force ALL text white ── */
    * {
        color: #f3f4f6;
    }
    /* Only override specific things that should NOT be white */
    .stButton > button { color: white !important; }
    [data-testid="stAlert"] * { color: inherit; }

    /* ── Headers ── */
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"],
    [data-testid="stSidebar"] > div,
    [data-testid="stSidebarContent"] {
        background-color: #111827 !important;
        border-right: 1px solid #374151 !important;
    }

    /* ── Text inputs ── */
    .stTextInput input,
    textarea,
    input[type="text"] {
        background-color: #1f2937 !important;
        color: #ffffff !important;
        border: 1px solid #374151 !important;
        border-radius: 8px !important;
    }
    input::placeholder, textarea::placeholder {
        color: #9ca3af !important;
    }

    /* ── Selectbox ── */
    .stSelectbox [data-baseweb="select"] > div {
        background-color: #1f2937 !important;
        border-color: #374151 !important;
    }
    .stSelectbox [data-baseweb="select"] span,
    .stSelectbox [data-baseweb="select"] div {
        color: #ffffff !important;
        background-color: #1f2937 !important;
    }
    [data-baseweb="popover"],
    [data-baseweb="menu"],
    [data-baseweb="menu"] ul,
    [data-baseweb="menu"] li {
        background-color: #1f2937 !important;
        color: #ffffff !important;
    }
    [data-baseweb="menu"] li:hover {
        background-color: #374151 !important;
    }

    /* ── Buttons ── */
    .stButton > button {
        background-color: #3b82f6 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    .stButton > button:hover {
        background-color: #2563eb !important;
        box-shadow: 0 4px 15px rgba(59,130,246,0.4) !important;
    }

    /* ── Metric cards ── */
    [data-testid="stMetricValue"] { color: #60a5fa !important; }
    [data-testid="stMetricLabel"] { color: #d1d5db !important; }

    /* ── Chat messages ── */
    [data-testid="stChatMessage"],
    .stChatMessage {
        background-color: #1a2332 !important;
        border: 1px solid #374151 !important;
        border-radius: 12px !important;
    }

    /* ── Chat input bar ── */
    [data-testid="stChatInput"],
    .stChatInputContainer,
    [data-testid="stChatInputContainer"] {
        background-color: #111827 !important;
        border-top: 1px solid #374151 !important;
    }
    [data-testid="stChatInput"] textarea {
        background-color: #1f2937 !important;
        color: #ffffff !important;
        border: 1px solid #374151 !important;
        border-radius: 8px !important;
    }

    /* ── Divider ── */
    hr { border-color: #374151 !important; }

    /* ── Emergency alert ── */
    .emergency-alert {
        background-color: rgba(220, 38, 38, 0.15) !important;
        border: 2px solid #dc2626 !important;
        border-radius: 8px !important;
        padding: 1rem !important;
        margin-bottom: 1rem !important;
    }
    .emergency-alert, .emergency-alert * {
        color: #fca5a5 !important;
    }
</style>
""", unsafe_allow_html=True)

# Define Languages
LANGUAGES = [
    "English", "Hindi (हिन्दी)", "Telugu (తెలుగు)", "Bengali (বাংলা)", 
    "Marathi (मराठी)", "Tamil (தமிழ்)", "Gujarati (ગુજરાતી)", 
    "Kannada (ಕನ್ನಡ)", "Malayalam (മലയാളം)", "Punjabi (ਪੰਜਾਬੀ)", 
    "Odia (ଓଡ଼ିଆ)", "Assamese (অসমীয়া)", "Nepali (नेपाली)"
]

# Session State Initialization
if "messages" not in st.session_state:
    st.session_state.messages = []
if "weather_data" not in st.session_state:
    st.session_state.weather_data = None
if "location_info" not in st.session_state:
    st.session_state.location_info = None
if "is_alert" not in st.session_state:
    st.session_state.is_alert = False
if "alert_reasons" not in st.session_state:
    st.session_state.alert_reasons = []

def process_location(location, language):
    with st.spinner("Geocoding location..."):
        loc_info, loc_err = weather_service.get_coordinates(location)
    
    if loc_err:
        st.error(loc_err)
        return
        
    st.session_state.location_info = loc_info
    
    with st.spinner("Fetching weather telemetry..."):
        w_data, w_err = weather_service.get_weather_data(loc_info['lat'], loc_info['lon'])
        
    if w_err:
        st.error(w_err)
        return
        
    st.session_state.weather_data = w_data
    
    # Evaluate Risk
    is_alert, alert_reasons = False, []
    try:
        rain_val = float(w_data.get("predicted_rain_24h", 0))
        if rain_val > 50.0:
            is_alert = True
            alert_reasons.append(f"High cumulative 24h rainfall predicted: {rain_val} mm (Threshold: >50mm). Risk of flash floods or waterlogging.")
    except Exception:
        pass
    try:
        wind_val = float(w_data.get("wind_speed", 0))
        if wind_val > 45.0:
            is_alert = True
            alert_reasons.append(f"High wind speeds detected: {wind_val} km/h (Threshold: >45 km/h). Potential structural hazards.")
    except Exception:
        pass
    st.session_state.is_alert = is_alert
    st.session_state.alert_reasons = alert_reasons
    
    # Generate initial summary
    with st.spinner("Analyzing data with AI..."):
        ai_response = rag_engine.generate_weather_response(
            location_name=loc_info['name'],
            weather_data=w_data,
            language=language,
            is_alert=is_alert,
            alert_reasons=alert_reasons
        )
        
    st.session_state.messages.append({"role": "assistant", "content": ai_response})


# Sidebar
with st.sidebar:
    st.title("🌪️ WeatherGPT")
    st.caption("AI-Driven Hyper-Local Early Warning System (SIH26068)")
    
    st.header("📍 Location Control")
    location_input = st.text_input("Enter City, Village, or District")
    
    st.header("🌐 Regional Language")
    selected_language = st.selectbox("Select Language", LANGUAGES)
    
    fetch_btn = st.button("Fetch Telemetry & Analyze", use_container_width=True)
    
    if fetch_btn and location_input:
        st.session_state.messages = [] # Reset chat on new location
        process_location(location_input, selected_language)

    if st.session_state.weather_data:
        st.divider()
        st.header("📊 System Telemetry")
        wd = st.session_state.weather_data
        
        col1, col2 = st.columns(2)
        col1.metric("Temp", f"{wd['temperature']}°C")
        col2.metric("Feels Like", f"{wd['feels_like']}°C")
        
        col3, col4 = st.columns(2)
        col3.metric("Wind", f"{wd['wind_speed']} km/h")
        col4.metric("Humidity", f"{wd['humidity']}%")
        
        st.metric("24h Rain Prediction", f"{wd['predicted_rain_24h']} mm")

# Main Content Area
st.title("Weather Analysis & Chat")

if st.session_state.location_info:
    st.markdown(f"**Current Location:** `{st.session_state.location_info['name']}`")
    
if st.session_state.is_alert:
    st.markdown(f"""
    <div class="emergency-alert">
        <h2>⚠️ URGENT RED ALERT TRIGGERED</h2>
        <p><strong>Reasons:</strong> {', '.join(st.session_state.alert_reasons)}</p>
    </div>
    """, unsafe_allow_html=True)

# Display Chat Messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat Input
if user_query := st.chat_input("Ask a question about the weather or safety..."):
    if not st.session_state.weather_data:
        st.warning("Please search for a location first.")
    else:
        st.session_state.messages.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)
            
        with st.spinner("Thinking..."):
            ai_response = rag_engine.generate_weather_response(
                location_name=st.session_state.location_info['name'],
                weather_data=st.session_state.weather_data,
                language=selected_language,
                is_alert=st.session_state.is_alert,
                alert_reasons=st.session_state.alert_reasons,
                user_message=user_query
            )
            
        st.session_state.messages.append({"role": "assistant", "content": ai_response})
        with st.chat_message("assistant"):
            st.markdown(ai_response)