import streamlit as st
import datetime
import time
import pytz
from geopy.geocoders import Nominatim
from astral.sun import sun
from astral import LocationInfo
from timezonefinder import TimezoneFinder
import os # Import für Dateiprüfung

# --- SEITENKONFIGURATION & LAYOUT (Responsiv) ---
st.set_page_config(page_title="romanWatch - temporale Uhr", page_icon="🏛️", layout="centered")

# --- HEADER-GRAFIK EINBINDEN ---
# WICHTIG: Das Bild muss im gleichen Verzeichnis als 'graphic.png' liegen!
bild_pfad = "graphic.png" 

if os.path.exists(bild_pfad):
    # 'use_container_width=True' sorgt für automatische Größenanpassung auf Handy & Desktop
    st.image(bild_pfad, use_container_width=True)
else:
    # Fallback, falls das Bild fehlt
    st.title("🏛️ romanWatch")
    st.warning(f"Hinweis: Die Header-Grafik '{bild_pfad}' wurde nicht im Verzeichnis gefunden.")


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

# --- SEITENLEISTE (MENÜ) ---
st.sidebar.header("Einstellungen")
# ÄNDERUNG: Standard-Standort auf "Rom" gesetzt
ort_name = st.sidebar.text_input("📍 Standort:", "Rom")
live_update = st.sidebar.checkbox("Live-Uhr (Sekundentakt)", value=True, help="Ausschalten, um in Ruhe einen Ort einzutippen")

# --- NEU: CHARMANTER HINWEIS AUF DIE BUCHSEITE IN DER SIDEBAR ---
st.sidebar.markdown("---") # Trennlinie
st.sidebar.info("""
**Von der Sonnenuhr zur Cäsium-Sekunde ⏱️**

Hat Ihnen diese kleine spielerische Reise in die relative Zeitmessung gefallen? Wenn Sie sich (wie ich) nicht nur für historische Gedankenspiele, sondern für die handfesten, modernen Grundlagen der Naturwissenschaften begeistern:

Besuchen Sie gerne meine interaktive Lern-Baustelle unter **[physik.hier-im-netz.de](https://physik.hier-im-netz.de)**. Dort finden Sie spannende Flashcards, Rätsel und alle Infos zur kommenden 2. Auflage meines Buches *"Brückenkurs Physik"* (Springer Nature).
""")


# --- HAUPTPROGRAMM ---
# Titel nach dem Bild (falls Bild vorhanden)
if os.path.exists(bild_pfad):
     st.subheader("Ihre temporale Uhr")

lat, lon = hole_koordinaten(ort_name)
uhr_platzhalter = st.empty()

if lat is None or lon is None:
    st.error("Ort nicht gefunden. Bitte überprüfe die Schreibweise.")
else:
    tz_name = hole_zeitzone(lat, lon)
    lokale_zeitzone = pytz.timezone(tz_name) if tz_name else pytz.UTC
    
    jetzt_utc = datetime.datetime.now(datetime.timezone.utc)
    jetzt_lokal = jetzt_utc.astimezone(lokale_zeitzone)
    
    # Astral LocationInfo benötigt 'Region', wir nutzen tz_name als Behelf
    ort_info = LocationInfo(ort_name, tz_name if tz_name else "UTC", tz_name if tz_name else "UTC", lat, lon)
    sonnen_daten = sun(ort_info.observer, date=jetzt_utc.date())
    
    t_auf = sonnen_daten["sunrise"]
    t_unter = sonnen_daten["sunset"]
    
    tageslaenge_sek = (t_unter - t_auf).total_seconds()
    wahrer_mittag = t_auf + datetime.timedelta(seconds=tageslaenge_sek / 2)
    
    with uhr_platzhalter.container():
        st.subheader(f"📍 {ort_name.capitalize()}")
        st.caption(f"🌍 Zeitzone: {tz_name}")
        st.write("---")
        
        # metric ist von Haus aus gut lesbar auf allen Geräten
        st.metric(label="1️⃣ Moderne Ortszeit", value=jetzt_lokal.strftime('%H:%M:%S'))
        st.write("---")
        
        if t_auf <= jetzt_utc <= t_unter:
            abstand_zum_mittag_sek = (jetzt_utc - wahrer_mittag).total_seconds()
            skalierungsfaktor = 43200 / tageslaenge_sek # 12 Stunden = 43200 Sekunden
            roemische_sekunden = abstand_zum_mittag_sek * skalierungsfaktor
            
            roemischer_mittag = datetime.datetime(2000, 1, 1, 12, 0, 0)
            roemische_zeit = roemischer_mittag + datetime.timedelta(seconds=roemische_sekunden)
            
            anzeige_arabisch = roemische_zeit.strftime("%H:%M:%S")
            
            # Fehler abfangen, falls Stunden/Minuten/Sekunden negativ werden (sollte durch if-Bedingung verhindert sein, aber sicher ist sicher)
            try:
                h = int_zu_roemisch(roemische_zeit.hour)
                m = int_zu_roemisch(roemische_zeit.minute)
                s = int_zu_roemisch(roemische_zeit.second)
                anzeige_roemisch = f"{h} : {m} : {s}"
            except Exception:
                 anzeige_roemisch = "Berechnungsfehler"

            
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
        Die Römer nutzten sogenannte **[temporale Stunden](https://de.wikipedia.org/wiki/Temporale_Stunden)**. Der Tag zwischen Sonnenaufgang und Sonnenuntergang wurde stets in exakt **12 gleich lange Stunden** unterteilt.
        
        Das führt zu einer faszinierenden Mechanik:
        * ☀️ Im **Sommer**, wenn die Tage lang sind, dauert eine römische Stunde (und damit auch jede Minute und Sekunde) länger als unsere heutige.
        * ❄️ Im **Winter**, bei kurzen Tagen, vergeht die römische Zeit spürbar schneller.
        * 🕛 Nur am **wahren Mittag** (wenn die Sonne exakt am höchsten steht), sind beide Systeme perfekt synchron auf 12:00:00 Uhr.
        
        Die Nacht wurde nicht in Stunden, sondern in vier Nachtwachen (*Vigiliae*) eingeteilt. Unsere Null (0) kannten die Römer noch nicht, weshalb hier ein **N** für *nulla/nihil* (nichts) angezeigt wird.
        
        📖 *[Mehr dazu auf Wikipedia lesen](https://de.wikipedia.org/wiki/Temporale_Stunden)*
        """)

    # --- RECHTLICHES & DATENSCHUTZ ---
    with st.expander("⚖️ Impressum & Datenschutz"):
        st.markdown("""
        **Impressum (Anbieterkennzeichnung)** *Max Mustermann* *Musterstraße 1* *12345 Musterstadt* *E-Mail: max@mustermail.de* **Datenschutz** Diese App speichert aktiv keine persönlichen Daten der Nutzer (keine Cookies, keine Datenbank). Bitte beachten Sie jedoch:  
        * **Hosting:** Diese App wird über die Streamlit Community Cloud bereitgestellt. Beim Aufruf werden serverseitig Verbindungsdaten (wie Ihre IP-Adresse) durch Streamlit verarbeitet.  
        * **Geodaten:** Die von Ihnen eingegebenen Ortsnamen werden zur Berechnung der Koordinaten an die Server von OpenStreetMap (Nominatim) gesendet.  

        **Haftungsausschluss** Dies ist ein rein privates Hobbyprojekt. Es wird keine Gewähr für die Richtigkeit, Aktualität oder ständige Verfügbarkeit der berechneten Zeiten und Geodaten übernommen.
        """)

    # Live-Aktualisierung
    if live_update:
        time.sleep(1)
        st.rerun()
