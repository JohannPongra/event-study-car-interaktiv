from Programm.grundlagen.tabellen import lesen
import numpy as np
import pandas as pd

def cache_laden(cache_file):
    cached = lesen(cache_file) if cache_file.exists() else pd.DataFrame(columns=['sentence_id', 'label', 'p_neutral', 'p_positive', 'p_negative'])
    if cached.sentence_id.duplicated().any():
        raise ValueError('Doppelter Satz im FinBERT-Zwischenspeicher.')
    if not cached.empty:
        probs = cached[['p_neutral', 'p_positive', 'p_negative']].to_numpy(dtype=float)
        labels = np.array(['neutral', 'positive', 'negative'])[probs.argmax(axis=1)]
        if not np.isfinite(probs).all() or (probs < 0).any() or (not np.allclose(probs.sum(axis=1), 1, atol=1e-05)) or (not np.array_equal(labels, cached.label.to_numpy())):
            raise ValueError('Ungültige gespeicherte FinBERT-Vorhersagen.')
    return cached
