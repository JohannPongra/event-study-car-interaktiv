"""berechnung · stichprobe – klar abgegrenzter Projektbaustein."""
from Programm.grundlagen.pfade import pfad
import json
from Programm.grundlagen.pruefsummen import pruefsumme

def aufbereitung_pruefen(folder, cfg):
    file = pfad(pfad(folder, 'aufbereitet'), 'verarbeitung.json')
    if not file.exists():
        raise ValueError('Zuerst python -m Programm aufbereiten ausführen.')
    meta = json.loads(file.read_text(encoding='utf-8'))
    for key in ['bestand', 'tickers', 'start', 'end', 'benchmark', 'fiscal_year_end']:
        if cfg[key] != meta['config'][key]:
            raise ValueError('Auswahl seit der Aufbereitung verändert. Datenverarbeitung erneut ausführen.')
    for name, expected in meta['tabellen'].items():
        path = pfad(pfad(folder, 'aufbereitet'), name + '.csv')
        if not path.exists() or pruefsumme(path) != expected:
            raise ValueError('Aufbereitete Tabelle verändert: ' + name + '. Datenverarbeitung erneut ausführen.')
    for name, expected in meta['rohdateien'].items():
        path = pfad(folder, name)
        if not path.exists() or pruefsumme(path) != expected:
            raise ValueError('Rohdatei verändert: ' + name + '. Datenverarbeitung erneut ausführen.')
