"""statistik · robustheit · modellvarianten – klar abgegrenzter Projektbaustein."""
from Programm.berechnung.berechnung import berechnen
from Programm.statistik.regression import fit
from Programm.statistik.koeffizienten import koeffizienten
import numpy as np
import pandas as pd

def varianten(data, cfg, primary, fortschritt):
    """Vereinbarte Sensitivitätsprüfungen; nur Zielgrößen bei Fensterwechsel ändern."""
    rows, errors = ([], [])

    def variante(label, subset, outcome, settings=None):
        settings = {**cfg, **(settings or {})}
        try:
            _, robust, x = fit(subset, outcome, cfg['predictors'], settings)
            rows.extend(koeffizienten(robust, x, label, outcome, subset, settings))
        except (ValueError, np.linalg.LinAlgError) as exc:
            errors.append({'variant': label, 'outcome': outcome, 'message': str(exc)})
    if cfg['robustness']:
        raw = data.copy()
        for col in ['sue', 'vol', 'prevol', 'search']:
            raw[col] = raw[col + '_raw'] if col + '_raw' in raw else raw[col]
        raw['abs_sue'] = raw.sue.abs()
        winsor = raw.copy()
        for col in ['sue', 'vol', 'prevol']:
            lo, hi = raw[col].quantile([0.01, 0.99])
            winsor[col] = raw[col].clip(lo, hi)
        winsor['abs_sue'] = winsor.sue.abs()
        for outcome in ['car', 'abs_car']:
            variante('ohne feste Effekte', data, outcome, {'fixed_effects': False})
            variante('Winsorisierung SUE VOL PREVOL 1/99', winsor, outcome)
            if cfg['winsorize']:
                variante('ohne Winsorisierung', raw, outcome)
            variante('Unternehmen: alle', data, outcome)
            for ticker in sorted(data.ticker.unique()):
                variante('Unternehmen: ohne ' + ticker, data.loc[data.ticker.ne(ticker)], outcome)
        for window in [[-1, 1], [0, 2]]:
            fortschritt('Alternatives CAR-Fenster ' + str(window) + '; Erklärungsgrößen unverändert')
            calculated = berechnen({**cfg, 'window': window}, lambda _: None, export=False)['data']
            by_id = calculated.set_index('event_id')
            if not data.event_id.isin(by_id.index).all():
                raise ValueError('Alternatives Fenster hat nicht dieselbe Ereignisstichprobe.')
            alternative = data.copy()
            alternative['car'] = alternative.event_id.map(by_id.car)
            alternative['abs_car'] = alternative.car.abs()
            for outcome in ['car', 'abs_car']:
                variante('Ereignisfenster ' + str(window), alternative, outcome)
    return (pd.DataFrame(rows), pd.DataFrame(errors, columns=['variant', 'outcome', 'message']))
