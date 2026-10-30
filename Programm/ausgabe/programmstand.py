"""Vollständigen aktiven Programmstand zusammen mit einem Ergebnis sichern."""
from Programm.grundlagen.pfade import pfad
import shutil
from Programm.grundlagen.pfade import ORDNER, pfad

def sichern(out):
    target = pfad(out, 'skripte')
    target.mkdir(parents=True, exist_ok=True)
    for name in ['Programm', 'Technik/Abhaengigkeiten', 'Technik/Konfiguration', 'Technik/Startdateien', 'Dokumentation/Methodik']:
        shutil.copytree(ORDNER / name, target / name, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    for p in [*ORDNER.glob('*.bat'), pfad(ORDNER, 'README.md')]:
        shutil.copy2(p, target / p.name)
