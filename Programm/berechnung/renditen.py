"""berechnung · renditen – klar abgegrenzter Projektbaustein."""
import numpy as np

def renditen(prices, art='simple'):
    """Formel 1: P_t / P_(t-1) - 1; logarithmische Renditen bleiben explizit wählbar."""
    if art not in {'simple', 'log'}:
        raise ValueError('Unbekannte Renditeart: ' + str(art))
    valid = prices.where(prices > 0)
    return np.log(valid).diff() if art == 'log' else valid.pct_change(fill_method=None)
