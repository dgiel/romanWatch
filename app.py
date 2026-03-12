import streamlit as st
import datetime
import time
import pytz
from geopy.geocoders import Nominatim
from astral.sun import sun
from astral import LocationInfo
from timezonefinder import TimezoneFinder

st.set_page_config(page_title="Temporale Uhr", page_icon="🏛️")
st.title("🏛️ Meine temporale Uhr")

# --- HILFSFUNKTION ---
# Umwandlung von arabischen in römische Ziffern
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

# --- CACHING FÜR API-ABFRAGEN ---
@st.cache_data
def hole_koordinaten(stadt):
    geolocator = Nominatim(user_agent="meine_roemische_uhr_app")
    location = geolocator.geocode(stadt)
    if location:
        return location.latitude, location.longitude
    return None, None

@st.cache_data
def hole_zeitzone(lat, lon):
    tf = TimezoneFinder()
    return tf.timezone_at(lng=lon, lat=lat)

# --- SEITENLEISTE (MENÜ) ---
st.sidebar.header("Einstellungen")
ort_name = st.sidebar.text_input("📍 Standort:", "Offenburg")

# Hier ist der neue Umschalter für die 3 Modi!
modus = st.sidebar.radio(
    "Anzeigemodus wählen:",
    ("Moderne Zeit", "Römische Zeit - Arabische Ziffern", "Römische Zeit - Römische Ziffern")
)

live_update = st.sidebar.checkbox("Live-Uhr (Sekundentakt)", value=True, help="Ausschalten, um in Ruhe einen Ort einzutippen")

# --- HAUPTPROGRAMM ---
lat, lon = hole_koordinaten(ort_name)
uhr_platzhalter = st.empty()

if lat is None or lon is None:
    st.error("Ort nicht gefunden. Bitte überprüfe die Schreibweise.")
else:
    # Zeitzonen und Zeiten berechnen
    tz_name = hole_zeitzone(lat, lon)
    lokale_zeitzone = pytz.timezone(tz_name) if tz_name else pytz.UTC
    
    jetzt_utc = datetime.datetime.now(datetime.timezone.utc)
    jetzt_lokal = jetzt_utc.astimezone(lokale_zeitzone)
    
    # Sonnenstandsdaten holen
    ort_info = LocationInfo(ort_name, "Region", tz_name if tz_name else "UTC", lat, lon)
    sonnen_daten = sun(ort_info.observer, date=jetzt_utc.date())
    
    t_auf = sonnen_daten["sunrise"]
    t_unter = sonnen_daten["sunset"]
    
    tageslaenge_sek = (t_unter - t_auf).total_seconds()
    wahrer_mittag = t_auf + datetime.timedelta(seconds=tageslaenge_sek / 2)
    
    # --- ANZEIGE ---
    with uhr_platzhalter.container():
        st.subheader(f"📍 {ort_name.capitalize()}")
        st.write("---")
        
        # MODUS 1: Moderne Zeit
        if modus == "Moderne Zeit":
            st.metric(label="Moderne Ortszeit", value=jetzt_lokal.strftime('%H:%M:%S'))
            st.info(f"Zeitzone: {tz_name}")
            
        # MODUS 2 & 3: Römische Zeit
        else:
            if t_auf <= jetzt_utc <= t_unter:
                abstand_zum_mittag_sek = (jetzt_utc - wahrer_mittag).total_seconds()
                skalierungsfaktor = 43200 / tageslaenge_sek # 12 Stunden = 43200 Sekunden
                roemische_sekunden = abstand_zum_mittag_sek * skalierungsfaktor
                
                roemischer_mittag = datetime.datetime(2000, 1, 1, 12, 0, 0)
                roemische_zeit = roemischer_mittag + datetime.timedelta(seconds=roemische_sekunden)
                
                if modus == "Römische Zeit - Römische Ziffern":
                    h = int_zu_roemisch(roemische_zeit.hour)
                    m = int_zu_roemisch(roemische_zeit.minute)
                    s = int_zu_roemisch(roemische_zeit.second)
                    anzeige_zeit = f"{h} : {m} : {s}"
                    st.metric(label="Römische Zeit", value=anzeige_zeit)
                
                elif modus == "Römische Zeit - Arabische Ziffern":
                    anzeige_zeit = roemische_zeit.strftime("%H:%M:%S")
                    st.metric(label="Römische Zeit", value=anzeige_zeit)
                    
                st.success("Die Sonne ist am Himmel! Die temporalen Tagesstunden laufen.")
                
            else:
                st.metric(label="Römische Zeit", value="Nox (Nacht)")
                st.warning("🌙 **Es ist aktuell Nacht!** Die temporalen Stunden ruhen, es gelten die Vigiliae (Nachtwachen).")
    
    # Live-Aktualisierung
    if live_update:
        time.sleep(1)
        st.rerun()
