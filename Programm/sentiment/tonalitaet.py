"""sentiment · tonalitaet – klar abgegrenzter Projektbaustein."""
import numpy as np

def tonwert(positive, negative, neutral):
    """Formel 13: jeder Satz zählt einmal, neutrale Sätze gehören zum Nenner."""
    total = positive + negative + neutral
    return (positive - negative) / total if total else np.nan
