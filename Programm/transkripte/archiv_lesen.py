"""transkripte · archiv lesen – klar abgegrenzter Projektbaustein."""
from Programm.grundlagen.pfade import pfad
from pathlib import Path
import csv, hashlib, json
from Programm.grundlagen.pfade import ROOT
EXPORT = pfad(ROOT, 'EXPORT_LAPTOP_20261015')
BASE = pfad(ROOT, 'Transkripte')
FROZEN = pfad(ROOT, 'Daten/bestaende/bestand_20261016_100035_d963e3')

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def rows(path, delimiter=','):
    with Path(path).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f, delimiter=delimiter))

def daten():
    return (load(pfad(EXPORT, 'Ergebnis.json')), load(pfad(EXPORT, 'Nachweise/Entscheidungen.json')), rows(pfad(EXPORT, 'Nachweise/Hoerpruefung_original.csv'), ';'))
