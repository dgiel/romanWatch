from astral.sun import sun
from astral import LocationInfo
import datetime

def berechne_roemische_zeit(ort_name, lat, lon, zeitzone):
    # 1. Sonnenaufgang und -untergang für den Ort heute holen
    ort = LocationInfo(ort_name, "Region", zeitzone, lat, lon)
    sonne = sun(ort.observer, date=datetime.date.today(), tzinfo=ort.timezone)
    
    t_auf = sonne["sunrise"]
    t_unter = sonne["sunset"]
    jetzt = datetime.datetime.now(ort.timezone)
    
    # Prüfen, ob es Tag ist
    if jetzt < t_auf or jetzt > t_unter:
        return "Es ist Nacht! (Römer hatten hierfür Nachtwachen/Vigiliae)"
    
    # 2. Reale Tageslänge und wahren Mittag berechnen (in Sekunden)
    tageslaenge_sekunden = (t_unter - t_auf).total_seconds()
    wahrer_mittag = t_auf + datetime.timedelta(seconds=tageslaenge_sekunden / 2)
    
    # 3. Abstand zum Mittag ermitteln und skalieren
    abstand_zum_mittag_sek = (jetzt - wahrer_mittag).total_seconds()
    skalierungsfaktor = (12 * 3600) / tageslaenge_sekunden
    
    roemische_sekunden_abstand = abstand_zum_mittag_sek * skalierungsfaktor
    
    # 4. In die übliche Zeit umrechnen (Basis 12:00:00 Uhr)
    roemischer_mittag = datetime.datetime(jetzt.year, jetzt.month, jetzt.day, 12, 0, 0)
    roemische_zeit = roemischer_mittag + datetime.timedelta(seconds=roemische_sekunden_abstand)
    
    return roemische_zeit.strftime("%H:%M:%S")
