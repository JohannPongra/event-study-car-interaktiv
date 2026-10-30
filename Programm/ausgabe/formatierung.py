"""ausgabe · formatierung – klar abgegrenzter Projektbaustein."""
from Programm.grundlagen.standardwerte import LABELS
import pandas as pd
GRUEN, GOLD = ('#257a69', '#b48035')
ZIELE = {'car': 'Gerichtete Kursreaktion', 'abs_car': 'Größe der Kursreaktion'}

def renditeeinheit(cfg, singular=False):
    if singular:
        return 'logarithmischer Prozentpunkt' if cfg['return_type'] == 'log' else 'Prozentpunkt'
    return 'logarithmische Prozentpunkte' if cfg['return_type'] == 'log' else 'Prozentpunkte'


def label(name):
    return f'{LABELS.get(name, name)} ({name.upper()})' if name in LABELS else name

def zahl(value, stellen=4):
    return '–' if pd.isna(value) else f'{value:.{stellen}f}'.replace('.', ',')

def pwert(value):
    return '< 0,0001' if pd.notna(value) and value < 0.0001 else zahl(value)
