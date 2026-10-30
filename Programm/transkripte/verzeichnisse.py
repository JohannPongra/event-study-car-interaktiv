"""transkripte · verzeichnisse – klar abgegrenzter Projektbaustein."""
from Programm.grundlagen.pfade import pfad
from pathlib import Path
import csv

def writecsv(path, data, columns):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    data = [pfade_aktualisieren(row) for row in data]
    with Path(path).open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=columns, delimiter=';', extrasaction='ignore')
        w.writeheader()
        w.writerows(data)

def pfade_aktualisieren(row):
    from Programm.grundlagen.pfade import ROOT
    result = dict(row)
    for key, value in row.items():
        if isinstance(value, str) and value.startswith(('Transkripte/', 'EXPORT_LAPTOP_20261015/', 'Daten/bestaende/')):
            file, sep, fragment = value.partition('#')
            result[key] = pfad(ROOT, file).relative_to(ROOT).as_posix() + (sep + fragment if sep else '')
    return result
