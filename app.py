import streamlit as st
import datetime
from astral import LocationInfo
from astral.sun import sun
import pytz
from geopy.geocoders import Nominatim
import re

# ==========================================
# 1. KONFIGURATION & STYLING
# ==========================================
st.set_page_name("RomanWatch - Römische Uhr")
st.set_page_icon("⏱️")

# Custom CSS für Layout-Anpassungen (Römische Zeit nach oben)
st.markdown("""
<style>
    /* Versteckt das Streamlit-Menü für einen cleaner Look */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Styling für die arabische Uhrzeit oben */
    .time-top {
        font-size: 3rem !important;
        font-weight: 700;
        color: #d4af37; /* Gold */
        text-align: center;
        margin-top: -1rem; /* Zieht es näher ans Bild */
        margin-bottom: 0rem;
    }
    .time-top-label {
        font-size: 1rem;
        color: #a0a0a0;
        text-align: center;
        margin-bottom: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. HILFSFUNKTIONEN
# ==========================================

# Römische Ziffern Konverter (für die Legende)
def to_roman(n):
    if not (0 < n < 4000):
        return str(n)
    val = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
    syb = ["M", "CM", "D", "CD", "C", "XC", "L", "XL", "X", "IX", "V", "IV", "I"]
    roman_num = ''
    i = 0
    while n > 0:
        for _ in range(n // val[i]):
            roman_num += syb[i]
            n -= val[i]
        i += 1
    return roman_num

# Geocoding: Ort -> Koordinaten
def get_coords(location_name):
    geolocator = Nominatim(user_agent="roman_watch_app")
    try:
        location = geolocator.geocode(location_name)
        if location:
            return location.latitude, location.longitude, location.raw.get('display_name')
        else:
            return None, None, None
    except Exception as e:
        return None, None, f"Fehler: {e}"

# Römische Wachen (Vigiliae) Logik
def get_vigilia_info(stunde_der_nacht):
    """Gibt den Namen und die Stundenspanne einer Vigilia zurück."""
    vigiliae = [
        {"name": "I. VIGILIA (Prima Vigilia)", "span": "1.-3. Nachstunde", "icon": "🌙"},
        {"name": "II. VIGILIA (Secunda Vigilia)", "span": "4.-6. Nachstunde", "icon": "🌌"},
        {"name": "III. VIGILIA (Tertia Vigilia)", "span": "7.-9. Nachstunde", "icon": "🌑"},
        {"name": "IV. VIGILIA (Quarta Vigilia)", "span": "10.-12. Nachstunde", "icon": "🌅"},
    ]
    
    # Stunde_der_nacht ist 1-12, Vigiliae sind 0-3
    idx = int((stunde_der_nacht - 1) // 3)
    
    # Sicherheitscheck für Rundungsfehler am Morgen
    if idx < 0: idx = 0
    if idx > 3: idx = 3
        
    return vigiliae[idx]

# ==========================================
# 3. HAUPTPROGRAMM / UI
# ==========================================

st.title("RomanWatch: Römische Temporale Uhr")
st.markdown("*Wie spät wäre es jetzt in Pompeji?*")

# 3.1. SITEDAR / EINSTELLUNGEN
with st.sidebar:
    st.header("Einstellungen")
    
    location_input = st.text_input("Ort suchen (z.B. Rome, Pompeii, Berlin)", "Pompeii, Italy")
    lat, lon, full_address = get_coords(location_input)
    
    if lat and lon:
        st.success(f"Ort gefunden: {lat:.4f}°N, {lon:.4f}°E")
        st.info(f"Genaue Adresse: {full_address}")
    else:
        st.error("Ort nicht gefunden oder Geocoding-Fehler.")
        st.stop() # App stoppen, wenn kein Ort da ist

    date_input = st.date_input("Datum", datetime.date.today())
    
    # Zeitzone basierend auf Koordinaten finden (sehr rudimentär)
    timezone_str = 'Europe/Rome' if lon < 15 else 'Europe/Berlin' # Vereinfacht
    local_tz = pytz.timezone(timezone_str)
    
    # Berechnung des Sonnenstands für das gewählte Datum (00:00 Uhr lokal)
    naive_date = datetime.datetime.combine(date_input, datetime.time(0, 0))
    aware_date = local_tz.localize(naive_date)

    try:
        loc = LocationInfo("Custom", "World", timezone_str, lat, lon)
        s = sun(loc.observer, date=aware_date.date(), tzinfo=aware_date.tzinfo)
        sunrise = s['sunrise']
        sunset = s['sunset']
    except Exception as e:
        st.error(f"Fehler bei Sonnenstandsberechnung: {e}")
        st.stop()

# 3.2. BERECHNUNG DER ZEIT
now_utc = datetime.datetime.now(pytz.utc)
now_local = now_utc.astimezone(local_tz)

is_day = sunrise < now_local < sunset

if is_day:
    day_duration = sunset - sunrise
    hour_duration = day_duration / 12
    elapsed_time = now_local - sunrise
    roman_decimal_hour = elapsed_time / hour_duration
    base_text = "Tagstunde (hora diurna)"
else:
    # Nacht berechnen:
    if now_local >= sunset: # Nach Sonnenuntergang, vor Mitternacht
        night_duration = (sunrise + datetime.timedelta(days=1)) - sunset
        elapsed_time = now_local - sunset
    else: # Nach Mitternacht, vor Sonnenaufgang
        night_duration = sunrise - (sunset - datetime.timedelta(days=1))
        prev_sunset = sunset - datetime.timedelta(days=1)
        elapsed_time = now_local - prev_sunset
        
    hour_duration = night_duration / 12
    roman_decimal_hour = elapsed_time / hour_duration
    base_text = "Nachtstunde (hora nocturna)"

# Formatieren der arabischen Uhrzeit
whole_hours = int(roman_decimal_hour)
decimal_minutes = (roman_decimal_hour - whole_hours) * 60
whole_minutes = int(decimal_minutes)
decimal_seconds = (decimal_minutes - whole_minutes) * 60
whole_seconds = int(decimal_seconds)

roman_time_str = f"{whole_hours:02d}:{whole_minutes:02d}:{whole_seconds:02d}"

# 3.3. UI ANZEIGE (MIT BILD NACH OBEN)
# Bildschöne antike Sonnenuhr/Wasseruhr
st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/1/14/Roman_pocket_sundials_IJK.jpg/1280px-Roman_pocket_sundials_IJK.jpg", caption="Antike Römische Taschensonnenuhren (I-III Jhd.)")

# DIE NEUE ANZEIGE: Römische Zeit oben (arabisch)
st.markdown(f'<p class="time-top">{roman_time_str}</p>', unsafe_allow_html=True)
st.markdown(f'<p class="time-top-label">Römische Temporale Zeit ({date_input.strftime("%d.%m.%Y")} • {now_local.strftime("%H:%M:%S")})</p>', unsafe_allow_html=True)

st.divider()

# DETAILS UND NACHTWACHEN (UNTEN)
if is_day:
    # Anzeige am Tag: Die Sonnenuhr ist aktiv
    st.subheader(f"Es ist Tag in {location_input}")
    st.metric(label=f"Aktuelle {base_text}", value=f"{whole_hours + 1}. Stunde", help="Die Römer zählten die Stunden ab Sonnenaufgang (0-11, also 1.-12. Stunde).")
    
    st.progress(roman_decimal_hour / 11.0 if roman_decimal_hour <= 11 else 1.0)
    st.caption(f"Fortschritt des lichten Tages (Länge: {day_duration})")

else:
    # Anzeige in der Nacht: Die Nachtwachen sind aktiv
    st.subheader(f"Es ist Nacht in {location_input}")
    
    stunde_der_nacht = whole_hours + 1
    vigilia_info = get_vigilia_info(stunde_der_nacht)
    
    st.metric(label="Aktuelle Wache (Vigilia)", value=f"{vigilia_info['name']}", help=f"Die Römer teilten die Nacht in 4 Wachen zu je 3 Nachstunden.")
    st.metric(label="Nachstunde (hora nocturna)", value=f"{stunde_der_nacht}. Stunde", help=f"Entspricht der {vigilia_info['span']}.")
    
    st.progress(roman_decimal_hour / 11.0 if roman_decimal_hour <= 11 else 1.0)
    st.caption(f"Fortschritt der Nacht (Länge: {night_duration})")
    
    st.warning(f"{vigilia_info['icon']} {vigilia_info['name']}: Wache für die Legionen am Limes.")

# 3.4. LEGENDE & PHYSIK
st.divider()
with st.expander("Wie funktioniert diese Uhr? (Die Physik dahinter)"):
    st.markdown("""
    ### Temporale Stunden vs. Äquinoktialstunden

    Unsere modernen Stunden sind "Äquinoktialstunden" – sie sind immer exakt 60 Minuten (3600 Sekunden) lang, egal wo man sich auf der Erde befindet oder welche Jahreszeit wir haben. Sie basieren auf der Annahme einer gleichförmigen Erdrotation.

    Die Römer hingegen nutzten "temporale Stunden" (*horae*). Sie definierten:
    1.  Die Zeitspanne zwischen Sonnenaufgang und Sonnenuntergang ist **immer 12 Tagstunden** lang.
    2.  Die Zeitspanne zwischen Sonnenuntergang und Sonnenaufgang ist **immer 12 Nachstunden** lang.

    **Der physikalische Effekt:**
    Da die Länge des lichten Tages im Jahreslauf stark schwankt (im Sommer lang, im Winter kurz), variiert auch die Länge einer römischen Stunde. Eine *hora diurna* im Hochsommer war in Rom fast 75 moderne Minuten lang, während sie im tiefsten Winter auf nur 45 Minuten schrumpfte.

    ### Die Nachtwachen (Vigiliae)
    Da eine Sonnenuhr nachts nutzlos war, orientierten sich die Römer (besonders das Militär) an den vier *Vigiliae* (Nachtwachen), die jeweils drei Nachstunden umfassten. Dies geschah meist mit Hilfe von Wasseruhren (*Clepsydra*), die für jeden Monat angepasst werden mussten, um die unterschiedlichen Stundenlängen korrekt darzustellen.

    Diese App berechnet anhand der astronomischen Sonnenstandsdaten für Ihren gewählten Ort und Zeitpunkt die exakte Länge der temporalen Stunden und zeigt die Wachen an.
    """)
