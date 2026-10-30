from Programm.grundlagen.pfade import pfad
from Programm.grundlagen.tabellen import lesen
import pandas as pd

def klassenverteilung(folder):
    distribution_rows = []
    unit_files = {'sentence': pfad(pfad(folder, 'aufbereitet'), 'finbert_saetze.csv'), 'lc_sentence': pfad(pfad(pfad(folder, 'aufbereitet'), 'kontext'), 'lc_saetze.csv'), 'lc_context': pfad(pfad(pfad(folder, 'aufbereitet'), 'kontext'), 'lc_abschnitte.csv')}
    for method, file in unit_files.items():
        units = lesen(file)
        weights = units.n_sentences if 'n_sentences' in units else pd.Series(1, index=units.index)
        distribution_rows.append({'sentiment_method': method, 'n_units': len(units), 'n_sentences': int(weights.sum()), **{f'n_{label}_units': int(units.label.eq(label).sum()) for label in ['positive', 'neutral', 'negative']}, **{f'n_{label}_sentence_weight': int(weights.loc[units.label.eq(label)].sum()) for label in ['positive', 'neutral', 'negative']}})
    distribution = pd.DataFrame(distribution_rows)
    return distribution
