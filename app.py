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
if os.path.exists(bild_pfad):
    st.image(bild_pfad, use_container_width=True)
    st.subheader("🌋 Zeitreise nach Pompeji")
else:
    st.title("🏛️ Zeitreise nach Pompeji")
    st.warning(f"Hinweis: Die Header-Grafik '{bild_pfad}' wurde nicht im Verzeichnis gefunden.")

# --- 2. LAYOUT-CONTAINER DEFINIEREN ---
# So zwingen wir die Uhrzeit nach GANZ OBEN, noch bevor die Einstellungen kommen!
uhrzeit_container = st.container()

with st.expander("⚙️ Umrechnungs-Standort anpassen", expanded=True):
    ort_name = st.text_input("📍 Standort (z.B. Neapel, Pompeji):", "Neapel")
    live_update = st.checkbox("Live-Uhr (Sekundentakt)", value=True, help="Ausschalten, um in Ruhe einen anderen Ort einzutippen")

# --- 3. HAUPTPROGRAMM (UHR-BERECHNUNG) ---
lat, lon = hole_koordinaten(ort_name)
tz_name = hole_zeitzone(lat, lon)
lokale_zeitzone = pytz.timezone(tz_name) if tz_name else pytz.UTC

jetzt_utc = datetime.datetime.now(datetime.timezone.utc)
jetzt_lokal = jetzt_utc.astimezone(lokale_zeitzone)

ort_info = LocationInfo(ort_name, tz_name if tz_name else "UTC", tz_name if tz_name else "UTC", lat, lon)

# Sonnenstandsdaten berechnen
sonnen_daten = sun(ort_info.observer, date=jetzt_utc.date())
t_auf = sonnen_daten["sunrise"]
t_unter = sonnen_daten["sunset"]

# Tag oder Nacht ermitteln
if t_auf <= jetzt_utc <= t_unter:
    is_day = True
    dauer = (t_unter - t_auf).total_seconds()
    vergangen = (jetzt_utc - t_auf).total_seconds()
    label_text = "Römische Tageszeit (hora diurna)"
else:
    is_day = False
    label_text = "Römische Nachtzeit (hora nocturna)"
    if jetzt_utc > t_unter:
        morgen_daten = sun(ort_info.observer, date=(jetzt_utc + datetime.timedelta(days=1)).date())
        t_auf_naechster = morgen_daten["sunrise"]
        dauer = (t_auf_naechster - t_unter).total_seconds()
        vergangen = (jetzt_utc - t_unter).total_seconds()
    else:
        gestern_daten = sun(ort_info.observer, date=(jetzt_utc - datetime.timedelta(days=1)).date())
        t_unter_vorher = gestern_daten["sunset"]
        dauer = (t_auf - t_unter_vorher).total_seconds()
        vergangen = (jetzt_utc - t_unter_vorher).total_seconds()

# Umrechnung in römische Stunden
stunden_dauer = dauer / 12
roemisch_dezimal = vergangen / stunden_dauer

ganze_stunden = int(roemisch_dezimal)

# FIX: Für die Anzeige schieben wir die Stunde um 1 nach oben (1. bis 12. Stunde)
anzeige_stunde = min(12, ganze_stunden + 1)

rest_minuten = (roemisch_dezimal - ganze_stunden) * 60
ganze_minuten = int(rest_minuten)
rest_sekunden = (rest_minuten - ganze_minuten) * 60
ganze_sekunden = int(rest_sekunden)

# In der arabischen Digital-Anzeige nutzen wir jetzt "anzeige_stunde"
anzeige_arabisch = f"{anzeige_stunde:02d}:{ganze_minuten:02d}:{ganze_sekunden:02d}"

try:
    # Für die römischen Ziffern nutzen wir ebenfalls "anzeige_stunde"
    h = int_zu_roemisch(anzeige_stunde)
    m = int_zu_roemisch(ganze_minuten)
    s = int_zu_roemisch(ganze_sekunden)
    anzeige_roemisch = f"{h} : {m} : {s}"
except Exception:
    anzeige_roemisch = "Berechnungsfehler"

# --- 4. UI ANZEIGE (Befüllung der Container) ---

# A) Römische Zeit im Container GANZ OBEN injizieren
with uhrzeit_container:
    # Sauberes Inline-CSS, das garantiert nicht von Streamlit verschluckt wird
    st.markdown(f"<h1 style='text-align: center; color: #d4af37; font-size: 4.5rem; margin-bottom: 0px;'>{anzeige_arabisch}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: gray; font-size: 1.2rem; margin-top: -10px;'>{label_text}</p>", unsafe_allow_html=True)
    st.write("---")

# B) Restliche Metriken und Infos unterm Expander
st.caption(f"📍 **{ort_name.capitalize()}** | 🌍 Zeitzone: {tz_name}")
col1, col2 = st.columns(2)
with col1:
    st.metric(label="Moderne Ortszeit", value=jetzt_lokal.strftime('%H:%M:%S'))
with col2:
    st.metric(label="Römische Ziffern", value=anzeige_roemisch)

st.write("---")

# Status & Nachtwachen-Logik
if is_day:
    aktuelle_stunde = min(12, ganze_stunden + 1)
    st.success("☀️ Die Sonne ist am Himmel! Die temporalen Tagesstunden laufen.")
    st.info(f"Wir befinden uns in der **{aktuelle_stunde}. hora diurna** (Tagstunde).")
else:
    aktuelle_stunde_der_nacht = min(12, ganze_stunden + 1)
    vigilia = get_vigilia_info(aktuelle_stunde_der_nacht)
    
    st.warning("🌙 **Es ist aktuell Nacht!** Die temporalen Stunden ruhen, es gelten die Vigiliae (Nachtwachen).")
    st.metric(label="Aktuelle Wache", value=vigilia["name"])
    st.info(f"{vigilia['icon']} Wir befinden uns in der **{aktuelle_stunde_der_nacht}. hora nocturna** (Entspricht der {vigilia['
