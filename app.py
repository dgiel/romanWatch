import streamlit as st
import datetime
import time
import pytz
from geopy.geocoders import Nominatim
from astral.sun import sun
from astral import LocationInfo
from timezonefinder import TimezoneFinder
import os

# --- SEITENKONFIGURATION & LAYOUT ---
st.set_page_config(page_title="Zeitreise-App", page_icon="🌋", layout="centered")

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
    idx = max(0, min(idx, 3)) # Sicherstellen, dass der Index immer gültig ist
    return vigiliae[idx]

# --- CACHING FÜR API-ABFRAGEN (Mit Fallback!) ---
@st.cache_data
def hole_koordinaten(stadt):
    geolocator = Nominatim(user_agent="pompeji_zeitreise_app_v2")
    try:
        location = geolocator.geocode(stadt)
        if location:
            return location.latitude, location.longitude
    except Exception:
        pass
    # Fallback zu Neapel, falls die API streikt, damit die App nicht weiß bleibt!
    return 40.8518, 14.2681

@st.cache_data
def hole_zeitzone(lat, lon):
    try:
        tf = TimezoneFinder()
        return tf.timezone_at(lng=lon, lat=lat)
    except Exception:
        return "Europe/Rome"

# --- 1. HEADER-GRAFIK EINBINDEN ---
bild_pfad = "graphic.png" 
if os.path
