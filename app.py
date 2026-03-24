import streamlit as st
import datetime
import time
import pytz
from geopy.geocoders import Nominatim
from astral.sun import sun
from astral import LocationInfo
from timezonefinder import TimezoneFinder
import os

# --- SEITENKONFIGURATION & LAYOUT (Responsiv) ---
st.set_page_config(page_title="Zeitreise-App", page_icon="🌋", layout="centered")

# --- CUSTOM CSS FÜR DIE UHRZEIT OBEN ---
st.markdown("""
<style>
    .time-top {
        font-size: 3.5rem !important;
        font-weight: 700;
        color: #d4af37; /* Gold */
        text-align: center;
        margin-top: -0.5rem;
        margin-bottom: 0rem;
        line-height: 1.1;
    }
    .time-top-label {
        font-size: 1.1rem;
        color: #a0a0a0;
        text-align: center;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# --- HILFSFUNKTIONEN ---
def int_zu_roemisch(zahl):
    if zahl == 0:
        return "N" # N für "nulla"
    werte = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
    symbole = ["M", "CM", "D", "CD", "C", "XC", "L", "XL", "X", "IX", "V", "IV", "I"]
    roemisch = ""
    i = 0
    while zahl > 0:
        for _ in range(zahl // werte[i]):
            roemisch += symbole[i]
            zahl -= werte[i]
        i += 1
    return roemisch

def get_vigilia_info(stunde_der_nacht):
    vigiliae = [
        {"name": "I. VIGILIA (Prima Vigilia)", "span": "1. - 3. Nachstunde", "icon": "🌙"},
        {"name": "II. VIGILIA (Secunda Vigilia)", "span": "4. - 6. Nachstunde", "icon": "🌌"},
        {"name": "III. VIGILIA (Tertia Vigilia)", "span": "7. - 9. Nachstunde", "icon": "🌑"},
        {"name": "IV. VIGILIA (Quarta Vigilia)", "span": "10. - 12. Nachstunde", "icon": "🌅"},
    ]
    idx = int((stunde_der_nacht - 1) // 3)
    if idx < 0: idx = 0
    if idx > 3: idx = 3
    return vigiliae[idx]

# --- CACHING FÜR API-ABFRAGEN ---
@st.cache_data
def hole_koordinaten(stadt):
    geolocator = Nominatim(user_agent="meine_roemische_uhr_app")
    try:
        location = geolocator.geocode(stadt)
        if location:
            return location.latitude, location.longitude
    except Exception as e:
        st.error(f"Fehler bei der Geolokalisierung: {e}")
    return None, None

@st.cache_data
def hole_zeitzone(lat, lon):
    tf = TimezoneFinder()
    return tf.timezone_at(lng=lon, lat=lat)

# --- HEADER-GRAFIK EINBINDEN ---
bild_pfad = "graphic.png" 
if os.path.exists(bild_pfad):
    st.image(bild_pfad, use_container_width=True)
else:
    st.title("🏛️ Zeitreise-App")
    st.warning(f"Hinweis: Die Header-Grafik '{bild_pfad}' wurde nicht im Verzeichnis gefunden.")

if os.path.exists(bild_pfad):
     st.subheader("🌋 Zeitreise nach Pompeji")

# --- STEUERUNG ALS EXPANDER ---
with st.expander("⚙️ Umrechnungs-Standort anpassen", expanded=True):
    ort_name = st.text_input("📍 Standort (z.B. Neapel, Pompeji):", "Neapel")
    live_update = st.checkbox("Live-Uhr (Sekundentakt)", value=True, help="Ausschalten, um in Ruhe einen anderen Ort einzutippen")

# --- HAUPTPROGRAMM (UHR-BERECHNUNG) ---
lat, lon = hole_koordinaten(ort_name)
uhr_platzhalter = st.empty()

if lat is None or lon is None:
    st.error("Ort nicht gefunden. Bitte überprüfe die Schreibweise.")
else:
    tz_name = hole_zeitzone(lat, lon)
    lokale_zeitzone = pytz.timezone(tz_name) if tz_name else pytz.UTC
    
    jetzt_utc = datetime.datetime.now(datetime.timezone.utc)
    jetzt_lokal = jetzt_utc.astimezone(lokale_zeitzone)
    
    ort_info = LocationInfo(ort_name, tz_name if tz_name else "UTC", tz_name if tz_name else "UTC", lat, lon)
    
    # Sonnenstandsdaten für heute berechnen
    sonnen_daten = sun(ort_info.observer, date=jetzt_utc.date())
    t_auf = sonnen_daten["sunrise"]
    t_unter = sonnen_daten["sunset"]
    
    #
