"""datenaufbereitung · aufbereitung – klar abgegrenzter Projektbaustein."""
from Programm.grundlagen.pfade import schreibziel_pruefen
from Programm.grundlagen.pfade import pfad
from Programm.grundlagen.pfade import bestand_ordner
from Programm.datenaufbereitung.validierung import eindeutig
from Programm.grundlagen.konfiguration import einstellungen
from Programm.datenaufbereitung.ereignisse import ereignisse
from Programm.datenaufbereitung.kurse import kurse
from Programm.grundlagen.tabellen import lesen
from Programm.grundlagen.pruefsummen import pruefsumme
from Programm.grundlagen.tabellen import schreiben
from Programm.grundlagen.json_dateien import speichern
from Programm.datenaufbereitung.transkripttexte import texte
from Programm.datenaufbereitung.suchinteresse import trends
from Programm.grundlagen.laufkennungen import zeit

def verarbeiten(werte=None, fortschritt=print):
    cfg = einstellungen(werte)
    folder = bestand_ordner(cfg)
    schreibziel_pruefen(folder)
    raw, out = (pfad(folder, 'roh'), pfad(folder, 'aufbereitet'))
    fortschritt('Kurse, EPS-Historie und Ereignistage vereinheitlichen …')
    prices, volume = kurse(raw)
    history, events = ereignisse(raw, prices, cfg)
    transcripts = texte(raw, events, cfg)
    trend_weeks, trend_audit = trends(raw)
    tables = {'prices': prices, 'volume': volume, 'earnings_history': history, 'events': events, 'transcripts': transcripts, 'trends_wochen': trend_weeks, 'trends_exports': trend_audit}
    for name in ['tone_importiert', 'search_importiert']:
        if pfad(raw, name + '.csv').exists():
            frame = lesen(pfad(raw, name + '.csv'))
            eindeutig(frame, ['event_id'], name)
            tables[name] = frame.loc[frame.event_id.isin(events.event_id)].copy()
    for name, frame in tables.items():
        schreiben(frame, pfad(out, name + '.csv'))
    speichern(pfad(out, 'verarbeitung.json'), {'created_at': zeit(), 'config': cfg, 'ereignisse': len(events), 'rohdateien': {str(p.relative_to(folder)): pruefsumme(p) for p in sorted(raw.rglob('*')) if p.is_file()}, 'tabellen': {name: pruefsumme(pfad(out, name + '.csv')) for name in tables}, 'hinweise': ['Importierte Kurse müssen split- und dividendenadjustiert sein; Volumen splitadjustiert.', 'Veröffentlichungszeiten sind nur mit belegter Quelle als geprüft markiert.', 'SEARCH wird später je Ereignis aus genau einem Export berechnet.']})
    fortschritt(f'{len(events)} Ereignisse aufbereitet. FinBERT oder Berechnung als Nächstes.')
    return {'bestand': cfg['bestand'], 'ereignisse': len(events), 'transkriptbeitraege': len(transcripts)}
