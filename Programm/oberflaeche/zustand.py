"""oberflaeche · zustand – klar abgegrenzter Projektbaustein."""
from Programm.grundlagen.pfade import ORDNER, pfad, dateien
from Programm.grundlagen.pfade import ALTBESTAND
from Programm.grundlagen.pfade import BESTAENDE
from Programm.grundlagen.pfade import ERGEBNISSE
from Programm.oberflaeche.auftraege import JOB
from Programm.oberflaeche.auftraege import LOCK
from Programm.oberflaeche.auftraege import TOKEN
import json
from Programm.grundlagen.konfiguration import laden

def zustand():
    cfg = laden()
    stocks = []
    for folder in sorted([ALTBESTAND, *dateien(BESTAENDE, 'bestand_*')], key=lambda p: p.name, reverse=True):
        file = pfad(folder, 'bestand.json')
        if not file.exists():
            continue
        meta = json.loads(file.read_text(encoding='utf-8'))
        prepared = pfad(pfad(folder, 'aufbereitet'), 'verarbeitung.json')
        download_status = pfad(folder, 'download_status.json')
        count = json.loads(prepared.read_text(encoding='utf-8'))['ereignisse'] if prepared.exists() else None
        stocks.append({'id': folder.name, 'art': meta['art'], 'created_at': meta['created_at'], 'ereignisse': count, 'aufbereitet': prepared.exists(), 'download_status': json.loads(download_status.read_text(encoding='utf-8')).get('status') if download_status.exists() else None, 'berechnet': pfad(pfad(folder, 'berechnet'), 'berechnung.json').exists()})
    analyses = []
    for folder in sorted(dateien(ERGEBNISSE, 'analyse_*'), reverse=True):
        file = pfad(folder, 'manifest.json')
        if file.exists():
            meta = json.loads(file.read_text(encoding='utf-8'))
            analyses.append({'id': folder.name, 'created_at': meta['created_at'], 'n': meta['berechnung']['sample_n'], 'bestand': meta['config']['bestand'], 'sentiment_method': meta['config'].get('sentiment_method', 'sentence'), 'jamovi': pfad(folder, 'Jamovi_Daten.csv').exists() and pfad(folder, 'Uebersichtliche_Daten.csv').exists()})
    comparisons = []
    for folder in sorted((ORDNER / 'Ergebnisse/Kontextvergleiche').glob('vergleich_*'), reverse=True):
        file = pfad(folder, 'manifest.json')
        if file.exists():
            meta = json.loads(file.read_text(encoding='utf-8'))
            comparisons.append({'id': folder.name, 'bestand': meta['config']['bestand'], 'analysen': meta['analysen']})
    with LOCK:
        return {'config': cfg, 'bestaende': stocks, 'analysen': analyses, 'vergleiche': comparisons, 'job': dict(JOB), 'token': TOKEN, 'import_default': str(ALTBESTAND)}
