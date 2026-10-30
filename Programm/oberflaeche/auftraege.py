"""oberflaeche · auftraege – klar abgegrenzter Projektbaustein."""
from Programm.grundlagen.pfade import ALTBESTAND
from Programm.grundlagen.json_dateien import json_sicher
import secrets
import threading
from Programm.grundlagen.laufkennungen import zeit
TOKEN = secrets.token_urlsafe(32)
LOCK = threading.RLock()
JOB = {'status': 'idle', 'action': '', 'messages': [], 'result': None}

def fortschritt(message):
    with LOCK:
        JOB['messages'].append(str(message))
        JOB['messages'] = JOB['messages'][-120:]

def ausfuehren(action, cfg, payload):
    keys = payload.get('keys', {})
    try:
        from Programm.datenerhebung.sammlung import sammeln
        from Programm.datenaufbereitung.importieren import importieren
        from Programm.datenaufbereitung.aufbereitung import verarbeiten
        from Programm.sentiment.auswertung import auswerten
        from Programm.berechnung.berechnung import berechnen
        from Programm.statistik.auswertung import regressieren
        from Programm.ablaeufe.vollanalyse import alles
        if action == 'import':
            result = importieren(payload.get('source') or ALTBESTAND, cfg, fortschritt)
        elif action in {'download', 'resume'}:
            if action == 'download':
                cfg['bestand'] = ''
            result = sammeln(cfg, keys or None, fortschritt)
        elif action == 'process':
            result = verarbeiten(cfg, fortschritt)
        elif action == 'finbert':
            if cfg['sentiment_method'] == 'sentence':
                result = auswerten(cfg, fortschritt)
            else:
                from Programm.sentiment.kontext.auswertung import auswerten as lc_auswerten
                result = lc_auswerten(cfg, fortschritt)
        elif action == 'sentiment_compare':
            from Programm.ablaeufe.kontextvergleich import vergleichen
            result = vergleichen(cfg, fortschritt)
        elif action == 'calculate':
            result = berechnen(cfg, fortschritt)
            result = {'ereignisse': len(result['events']), 'verwendbar': len(result['data'])}
        elif action == 'regression':
            result = regressieren(cfg, fortschritt)
        elif action == 'all':
            result = alles(cfg, fortschritt)
        else:
            raise ValueError('Unbekannter Arbeitsschritt.')
        with LOCK:
            JOB.update(status='done', result=json_sicher(result), finished_at=zeit())
    except Exception as exc:
        message = str(exc)[:1200]
        for key in keys.values():
            if key:
                message = message.replace(key, '[ENTFERNT]')
        fortschritt(message)
        with LOCK:
            JOB.update(status='failed', result={'message': message}, finished_at=zeit())
    finally:
        keys.clear()
