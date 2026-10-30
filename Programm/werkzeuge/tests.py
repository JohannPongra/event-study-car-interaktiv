"""Alle aktiven Tests unabhängig vom aktuellen Arbeitsordner starten."""
from Programm.grundlagen.pfade import pfad
import argparse, unittest, tempfile
from Programm.grundlagen.pfade import ORDNER

def main(argv=None):
    temp = ORDNER / 'Pruefungen/Protokolle/Temporaer'
    temp.mkdir(parents=True, exist_ok=True)
    tempfile.tempdir = str(temp)
    p = argparse.ArgumentParser()
    p.add_argument('--muster', default='test_*.py')
    a = p.parse_args(argv)
    suite = unittest.defaultTestLoader.discover(str(pfad(ORDNER, 'Pruefungen/Tests')), pattern=a.muster, top_level_dir=str(ORDNER))
    return 0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1
