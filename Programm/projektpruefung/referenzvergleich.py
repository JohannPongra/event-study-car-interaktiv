"""projektpruefung · referenzvergleich – klar abgegrenzter Projektbaustein."""
from Programm.grundlagen.pfade import pfad
from Programm.grundlagen.pfade import REFERENCE, EINFACHE_REFERENCE
from pathlib import Path
import json

def referenz_fuer(renditeart):
    if renditeart == 'simple':
        return EINFACHE_REFERENCE
    if renditeart == 'log':
        return REFERENCE
    raise ValueError('Unbekannte Renditeart: ' + str(renditeart))


def vergleichen(out, reference=None):
    if reference is None:
        manifest = pfad(out, 'manifest.json')
        art = json.loads(manifest.read_text(encoding='utf-8'))['config']['return_type'] if manifest.exists() else 'log'
        reference = referenz_fuer(art)
    reference = Path(reference)
    import numpy as np
    import pandas as pd
    reports = []
    names = ['analysedaten', 'alle_ereignisse', 'ausschluesse', 'koeffizienten', 'diagnostik', 'robustheit', 'vif', 'event_study', 'beschreibung', 'korrelationen', 'residuen', 'unternehmensauswahl']
    for name in names:
        old = pd.read_csv(pfad(reference, name + '.csv'), encoding='utf-8-sig')
        new = pd.read_csv(pfad(out, name + '.csv'), encoding='utf-8-sig')
        if old.shape != new.shape or list(old.columns) != list(new.columns):
            raise ValueError('Form des Referenzergebnisses abweichend: ' + name)
        largest = 0.0
        for col in old:
            if pd.api.types.is_numeric_dtype(old[col]) and pd.api.types.is_numeric_dtype(new[col]):
                a = old[col].to_numpy(dtype=float)
                b = new[col].to_numpy(dtype=float)
                if not np.allclose(a, b, rtol=1e-09, atol=1e-11, equal_nan=True):
                    raise ValueError('Numerische Referenzabweichung: ' + name + '/' + col)
                finite = np.isfinite(a) & np.isfinite(b)
                if finite.any():
                    largest = max(largest, float(np.max(np.abs(a[finite] - b[finite]))))
            elif not old[col].fillna('<NA>').astype(str).equals(new[col].fillna('<NA>').astype(str)):
                raise ValueError('Text-/Zuordnungsabweichung: ' + name + '/' + col)
        reports.append({'table': name, 'rows': len(new), 'columns': len(new.columns), 'max_absolute_difference': largest, 'passed': True})
    data = pd.read_csv(pfad(out, 'analysedaten.csv'), encoding='utf-8-sig')
    if len(data) != 170 or data.event_trading_day.nunique() != 113:
        raise ValueError('Stichprobe weicht von 170 Ereignissen / 113 Datumsclustern ab.')
    return {'reference': str(reference), 'passed': True, 'event_count': 170, 'event_date_clusters': 113, 'relative_tolerance': 1e-09, 'absolute_tolerance': 1e-11, 'tables': reports}
