"""Call-Kennungen eindeutig auf die Ablage nach Dateityp abbilden."""
from Programm.grundlagen.pfade import BASE

def call_datei(art, event, endung):
    ticker, day = event.split('_', 1)
    return BASE / art / ticker / day[:4] / (event + endung)
