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
        st.write(f"🌍 **Ort:** {lat:.4f}, {lon:.4f} | ☀️ **Wahrer Mittag:** {wahrer_mittag.strftime('%H:%M:%S')} (UTC)")
        st.write("---")
        
        # Prüfen, ob die Sonne gerade am Himmel steht
        if t_auf <= jetzt_utc <= t_unter:
            # 1. Abstand zum wahren Mittag in echten Sekunden
            abstand_zum_mittag_sek = (jetzt_utc - wahrer_mittag).total_seconds()
            
            # 2. Skalierungsfaktor (Römischer Tag = exakt 12h = 43.200 Sekunden)
            skalierungsfaktor = 43200 / tageslaenge_sek
            
            # 3. Römische Sekunden Abweichung
            roemische_sekunden = abstand_zum_mittag_sek * skalierungsfaktor
            
            # 4. Umrechnung in das bekannte Format (Basis 12:00:00 Uhr)
            roemischer_mittag = datetime.datetime(2000, 1, 1, 12, 0, 0)
            roemische_zeit = roemischer_mittag + datetime.timedelta(seconds=roemische_sekunden)
            
            # Anzeige in groß
            st.metric(label="Aktuelle Römische Zeit", value=roemische_zeit.strftime("%H:%M:%S"))
            
            st.info("💡 Zur Info: Im römischen System geht die Sonne stets exakt um **06:00:00 Uhr** auf und um **18:00:00 Uhr** unter.")
            
        else:
            st.warning("🌙 **Es ist aktuell Nacht!**")
            st.write("Die temporalen Tagesstunden der Antike gelten nur zwischen Sonnenaufgang und Sonnenuntergang. Die Nacht wurde stattdessen in vier Nachtwachen (Vigiliae) unterteilt.")
    
    # 1 Sekunde warten und dann die App neu laden (für die Live-Uhrzeit)
    time.sleep(1)
    st.rerun()
