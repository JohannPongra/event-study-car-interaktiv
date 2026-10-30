"""ablaeufe · vollanalyse – klar abgegrenzter Projektbaustein."""
from Programm.grundlagen.konfiguration import laden

def alles(werte, fortschritt=print):
    from Programm.ablaeufe.reproduktion import reproduzieren
    if werte != laden():
        raise ValueError('Die geführte Reproduktion verwendet die gespeicherten Projekteinstellungen.')
    return reproduzieren(fortschritt=fortschritt)
