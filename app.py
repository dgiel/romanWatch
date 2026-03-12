import streamlit as st
import datetime
import time
from geopy.geocoders import Nominatim
from astral.sun import sun
from astral import LocationInfo

st.set_page_config(page_title="Römische Uhr", page_icon="🏛️")
st.title("🏛️ Meine Römische Uhr")

# WICHTIG: Zwischenspeichern (Caching), damit wir nicht jede Sekunde 
# den Geodaten-Server anfragen und gesperrt werden!
@st.cache_data
def hole_koordinaten(stadt):
    geolocator = Nominatim(user_agent="meine_roemische_uhr_app")
    location = geolocator.geocode(stadt)
    if location:
        return location.latitude, location.longitude
    return None, None

# Eingabefeld (Standardwert auf Offenburg gesetzt)
ort_name = st.text_input("Standort für die Sonnenberechnung:", "Offenburg")
lat, lon = hole_koordinaten(ort_name)

# Platzhalter, damit die Ansicht nicht flackert
uhr_platzhalter = st.empty()

if lat is None or lon is None:
    st.error("Ort nicht gefunden. Bitte überprüfe die Schreibweise.")
else:
    # Alles in der Weltzeit (UTC) berechnen, das umgeht alle Zeitzonen-Probleme!
    jetzt_utc = datetime.datetime.now(datetime.timezone.utc)
    
    # Astronomische Daten für heute holen
    ort_info = LocationInfo(ort_name, "Region", "UTC", lat, lon)
    sonnen_daten = sun(ort_info.observer, date=jetzt_utc.date())
    
    t_auf = sonnen_daten["sunrise"]
    t_unter = sonnen_daten["sunset"]
    
    # Tageslänge und Wahrer Mittag in echten Sekunden
    tageslaenge_sek = (t_unter - t_auf).total_seconds()
    wahrer_mittag = t_auf + datetime.timedelta(seconds=tageslaenge_sek / 2)
    
    with uhr_platzhalter.container():
        st.write(f"🌍
