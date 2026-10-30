"""grundlagen · tabellen – klar abgegrenzter Projektbaustein."""
from Programm.grundlagen.pfade import schreibziel_pruefen
import pandas as pd

def lesen(path):
    return pd.read_csv(path, encoding='utf-8-sig', keep_default_na=True)

def schreiben(frame, path):
    schreibziel_pruefen(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, encoding='utf-8-sig', na_rep='')
