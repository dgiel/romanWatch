import streamlit as st
import datetime
import time

st.set_page_config(page_title="Römische Uhr", page_icon="⏰")

st.title("Meine Römische Uhr")

# Platzhalter für die Uhrzeit, damit sie nicht immer neu unten angefügt wird
uhr_platzhalter = st.empty()

def berechne_roemische_zeit(zeit):
    # Hier kannst du später deine Logik einbauen!
    # Aktuell gibt sie einfach die normale Zeit zurück.
    return zeit.strftime("%H:%M:%S")

# Endlosschleife für die Live-Aktualisierung
while True:
    jetzt = datetime.datetime.now()
    uhrzeit_anzeige = berechne_roemische_zeit(jetzt)
    
    # Anzeige im Platzhalter aktualisieren
    uhr_platzhalter.header(f"Die aktuelle Zeit ist: {uhrzeit_anzeige}")
    
    # Warte 1 Sekunde bis zum nächsten Update
    time.sleep(1)
