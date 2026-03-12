import streamlit as st
import datetime
import time
import pytz
from geopy.geocoders import Nominatim
from astral.sun import sun
from astral import LocationInfo
from timezonefinder import TimezoneFinder

st.set_page_config(page_title="Temporale Uhr", page_icon="🏛️")
st.title("🏛️ Römische Uhrzeit 🏛️")

# --- HILFSFUNKTION ---
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
ort_name = st.sidebar.text_input("📍 Standort:", "Augusta Treverorum")
live_update = st.sidebar.checkbox("Live-Uhr (Sekundentakt)", value=True, help="Ausschalten, um in Ruhe einen Ort einzutippen")

# --- HAUPTPROGRAMM ---
lat, lon = hole_koordinaten(ort_name)
uhr_platzhalter = st.empty()

if lat is None or lon is None:
    st.error("Ort nicht gefunden. Bitte überprüfe die Schreibweise.")
else:
    tz_name = hole_zeitzone(lat, lon)
    lokale_zeitzone = pytz.timezone(tz_name) if tz_name else pytz.UTC
    
    jetzt_utc = datetime.datetime.now(datetime.timezone.utc)
    jetzt_lokal = jetzt_utc.astimezone(lokale_zeitzone)
    
    ort_info = LocationInfo(ort_name, "Region", tz_name if tz_name else "UTC", lat, lon)
    sonnen_daten = sun(ort_info.observer, date=jetzt_utc.date())
    
    t_auf = sonnen_daten["sunrise"]
    t_unter = sonnen_daten["sunset"]
    
    tageslaenge_sek = (t_unter - t_auf).total_seconds()
    wahrer_mittag = t_auf + datetime.timedelta(seconds=tageslaenge_sek / 2)
    
    with uhr_platzhalter.container():
        st.subheader(f"📍 {ort_name.capitalize()}")
        st.caption(f"🌍 Zeitzone: {tz_name}")
        st.write("---")
        
        st.metric(label="1️⃣ Moderne Ortszeit", value=jetzt_lokal.strftime('%H:%M:%S'))
        st.write("---")
        
        if t_auf <= jetzt_utc <= t_unter:
            abstand_zum_mittag_sek = (jetzt_utc - wahrer_mittag).total_seconds()
            skalierungsfaktor = 43200 / tageslaenge_sek # 12 Stunden = 43200 Sekunden
            roemische_sekunden = abstand_zum_mittag_sek * skalierungsfaktor
            
            roemischer_mittag = datetime.datetime(2000, 1, 1, 12, 0, 0)
            roemische_zeit = roemischer_mittag + datetime.timedelta(seconds=roemische_sekunden)
            
            anzeige_arabisch = roemische_zeit.strftime("%H:%M:%S")
            
            h = int_zu_roemisch(roemische_zeit.hour)
            m = int_zu_roemisch(roemische_zeit.minute)
            s = int_zu_roemisch(roemische_zeit.second)
            anzeige_roemisch = f"{h} : {m} : {s}"
            
            st.metric(label="2️⃣ Römische Zeit (Arabische Ziffern)", value=anzeige_arabisch)
            st.metric(label="3️⃣ Römische Zeit (Römische Ziffern)", value=anzeige_roemisch)
            
            st.success("☀️ Die Sonne ist am Himmel! Die temporalen Tagesstunden laufen.")
            
        else:
            st.metric(label="2️⃣ Römische Zeit", value="Nox (Nacht)")
            st.metric(label="3️⃣ Römische Zeit", value="Nox (Nacht)")
            st.warning("🌙 **Es ist aktuell Nacht!** Die temporalen Stunden ruhen, es gelten die Vigiliae (Nachtwachen).")
    
    # --- ERKLÄRTEXT IM AUFKLAPPMENÜ ---
    st.write("---")
    with st.expander("ℹ️ Wie funktioniert die römische Zeit?"):
        st.write("""
        Die Römer nutzten sogenannte **temporale Stunden**. Der Tag zwischen Sonnenaufgang und Sonnenuntergang wurde stets in exakt **12 gleich lange Stunden** unterteilt.
        
        Das führt zu einer faszinierenden Mechanik:
        * ☀️ Im **Sommer**, wenn die Tage lang sind, dauert eine römische Stunde (und damit auch jede Minute und Sekunde) länger als unsere heutige.
        * ❄️ Im **Winter**, bei kurzen Tagen, vergeht die römische Zeit spürbar schneller.
        * 🕛 Nur am **wahren Mittag** (wenn die Sonne exakt am höchsten steht), sind beide Systeme perfekt synchron auf 12:00:00 Uhr.
        
        Die Nacht wurde nicht in Stunden, sondern in vier Nachtwachen (*Vigiliae*) eingeteilt. Unsere Null (0) kannten die Römer noch nicht, weshalb hier ein **N** für *nulla/nihil* (nichts) angezeigt wird.
        """)

    # Live-Aktualisierung
    if live_update:
        time.sleep(1)
        st.rerun()
