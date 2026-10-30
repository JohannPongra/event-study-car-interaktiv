"""werkzeuge · laptop import – klar abgegrenzter Projektbaustein."""
from Programm.grundlagen.pfade import pfad
from Programm.grundlagen.pfade import BESTAENDE
from Programm.grundlagen.pfade import ORDNER
from pathlib import Path
from Programm.grundlagen.pfade import bestand_ordner
import csv
import json
from Programm.grundlagen.laufkennungen import kennung
from Programm.grundlagen.tabellen import lesen
from Programm.grundlagen.pruefsummen import pruefsumme
import runpy
from Programm.grundlagen.tabellen import schreiben
import shutil
from Programm.grundlagen.json_dateien import speichern
from Programm.datenaufbereitung.aufbereitung import verarbeiten
from Programm.grundlagen.laufkennungen import zeit

def importieren(export, cfg, fortschritt=print):
    export = Path(export).resolve()
    verifier = runpy.run_path(str(pfad(pfad(ORDNER, 'EXPORT_LAPTOP_20261015'), 'export_pruefen.py')))
    verification = verifier['verify_package'](export)
    if verification['unresolved_count']:
        raise ValueError('Der Export enthält noch offene Prüfstellen.')
    manifest = json.loads(pfad(export, 'Ergebnis.json').read_text(encoding='utf-8'))
    source = bestand_ordner(cfg)
    events = lesen(pfad(pfad(source, 'aufbereitet'), 'events.csv'))
    expected = set(events.event_id)
    if set(manifest['calls']) != expected:
        raise ValueError('Die Call-Kennungen des Exports passen nicht exakt zum Ereignisbestand.')
    with pfad(export, 'Index.csv').open(encoding='utf-8-sig', newline='') as handle:
        index = list(csv.DictReader(handle, delimiter=';'))
    if len(index) != len(expected) or {r['Call'] for r in index} != expected:
        raise ValueError('Index ist unvollständig oder enthält doppelte Calls.')
    indexed = {r['Call']: r for r in index}
    rows = []
    for event in sorted(expected):
        item = manifest['calls'][event]
        path = pfad(export, item['text_path'])
        digest = pruefsumme(path)
        if digest != item['text_sha256'] or digest != indexed[event]['SHA256']:
            raise ValueError('Textprüfsumme passt nicht: ' + event)
        text = path.read_bytes().decode('utf-8')
        if not text.strip():
            raise ValueError('Leerer Call: ' + event)
        rows.append({'event_id': event, 'ticker': event.split('_')[0], 'turn_index': 0, 'speaker': '', 'speaker_title': '', 'content': text, 'source': 'Whisper, Laptop-Export 20261015; gezielte menschliche Hörprüfung', 'source_text_sha256': digest, 'source_text_file': 'roh/laptop_export/' + item['text_path'], 'speaker_assignment': 'nicht vorhanden; vollständiger Call in einer Zeile'})
    new_cfg = dict(cfg, bestand=kennung('bestand'))
    target = pfad(BESTAENDE, new_cfg['bestand'])
    target.mkdir(parents=True)
    shutil.copytree(pfad(source, 'roh'), pfad(target, 'roh'), ignore=shutil.ignore_patterns('transcripts.csv', 'tone_importiert.csv', 'laptop_export'))
    from Programm.grundlagen.pfade import rohbestand_gliedern
    rohbestand_gliedern(target)
    shutil.copytree(export, pfad(pfad(target, 'roh'), 'laptop_export'))
    verifier['verify_package'](pfad(pfad(target, 'roh'), 'laptop_export'))
    import pandas as pd
    schreiben(pd.DataFrame(rows), pfad(pfad(target, 'roh'), 'transcripts.csv'))
    speichern(pfad(target, 'bestand.json'), {'art': 'import', 'created_at': zeit(), 'quelle': str(export), 'basisbestand': source.name, 'config': new_cfg, 'export_pruefung': verification, 'transkriptimport': '170 vollständige Calls; keine Sprecherzuordnung erfunden', 'tone_status': 'Neuberechnung erforderlich; keine älteren Tonwerte übernommen', 'export_manifest_sha256': pruefsumme(pfad(export, 'Ergebnis.json')), 'transcripts_sha256': pruefsumme(pfad(pfad(target, 'roh'), 'transcripts.csv'))})
    verarbeiten(new_cfg, fortschritt)
    prepared = lesen(pfad(pfad(target, 'aufbereitet'), 'transcripts.csv')).set_index('event_id')
    for row in rows:
        if prepared.loc[row['event_id'], 'content'] != row['content']:
            raise ValueError('Text wurde bei der Aufbereitung verändert: ' + row['event_id'])
    speichern(pfad(ORDNER, 'einstellungen.json'), new_cfg)
    result = {'bestand': target.name, 'basisbestand': source.name, 'calls': len(rows), 'export_pruefung': verification, 'texte_unveraendert': True, 'aktiviert': True, 'sentiment_neu_berechnet': False}
    speichern(pfad(target, 'Laptop_Importpruefung.json'), result)
    fortschritt(json.dumps(result, ensure_ascii=False))
    return result
