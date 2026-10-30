"""datenerhebung · abruf – klar abgegrenzter Projektbaustein."""
from Programm.grundlagen.pfade import pfad
import json
from Programm.grundlagen.pruefsummen import pruefsumme
import requests
from Programm.grundlagen.json_dateien import speichern
import time
from Programm.grundlagen.laufkennungen import zeit

def ohne_schluessel(value, keys):
    if isinstance(value, dict):
        return {k: ohne_schluessel(v, keys) for k, v in value.items() if k.lower() not in {'apikey', 'api_key', 'authorization'}}
    if isinstance(value, list):
        return [ohne_schluessel(v, keys) for v in value]
    if isinstance(value, str):
        for key in keys:
            if key:
                value = value.replace(key, '[ENTFERNT]')
    return value

class Abruf:
    """Vorhandene Antworten wiederverwenden; neue Abrufe begrenzen."""

    def __init__(self, folder, cfg, keys, fortschritt):
        self.folder, self.cfg, self.keys = (folder, cfg, keys)
        self.fortschritt = fortschritt
        self.anzahl, self.letzter = (0, 0)

    def holen(self, provider, name, params):
        file = pfad(pfad(pfad(self.folder, 'roh'), provider), name + '.json')
        if file.exists():
            return json.loads(file.read_text(encoding='utf-8'))
        key = self.keys.get(provider, '').strip()
        if not key:
            raise ValueError('API-Schlüssel fehlt: ' + provider)
        if self.anzahl >= self.cfg['request_limit']:
            raise ValueError('Anfragelimit erreicht. Diesen Datenbestand später fortsetzen.')
        pause = self.cfg['pause_seconds'] - (time.monotonic() - self.letzter)
        if pause > 0:
            time.sleep(pause)
        self.anzahl += 1
        self.letzter = time.monotonic()
        self.fortschritt(f'Abruf {self.anzahl}: {name}')
        from Programm.datenerhebung import alpha_vantage, serpapi
        anbieter = {'alpha_vantage': alpha_vantage, 'serpapi': serpapi}[provider]
        url = anbieter.URL
        request = dict(params, **{'apikey': key} if provider == 'alpha_vantage' else {'api_key': key})
        try:
            response = requests.get(url, params=request, timeout=60)
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError):
            raise ValueError(provider + ': Abruf fehlgeschlagen. Verbindung und Tarif prüfen.') from None
        if not isinstance(payload, dict):
            raise ValueError('Unerwartete Anbieterantwort.')
        issue = next((payload[k] for k in ['Error Message', 'Information', 'Note', 'error'] if payload.get(k)), None)
        if issue:
            raise ValueError(provider + ': ' + str(ohne_schluessel(str(issue), self.keys.values()))[:500])
        speichern(file, ohne_schluessel(payload, self.keys.values()))
        speichern(file.with_suffix('.quelle.json'), {'provider': provider, 'request': params, 'retrieved_at': zeit(), 'sha256': pruefsumme(file)})
        return payload
