"""sentiment · kontext · aggregierung – klar abgegrenzter Projektbaustein."""
from Programm.grundlagen.pfade import pfad
from Programm.sentiment.kontext.abschnitte import MODELL
from Programm.sentiment.kontext.abschnitte import REGEL
from Programm.sentiment.kontext.abschnitte import REVISION
from Programm.sentiment.satztrennung import SATZTRENNUNG_VERSION
from Programm.sentiment.kontext.abschnitte import VARIANTEN
import json
from Programm.grundlagen.tabellen import lesen
import numpy as np
import pandas as pd
from Programm.grundlagen.pruefsummen import pruefsumme

def aggregieren(scored, variant):
    data = scored.copy()
    data['positive_weight'] = data.n_sentences.where(data.label.eq('positive'), 0)
    data['negative_weight'] = data.n_sentences.where(data.label.eq('negative'), 0)
    data['neutral_weight'] = data.n_sentences.where(data.label.eq('neutral'), 0)
    data['prob_weight'] = data.n_sentences * (data.p_positive - data.p_negative)
    result = data.groupby('event_id').agg(n_units=('unit_id', 'size'), n_sentences=('n_sentences', 'sum'), n_positive_weight=('positive_weight', 'sum'), n_negative_weight=('negative_weight', 'sum'), n_neutral_weight=('neutral_weight', 'sum'), probability_sum=('prob_weight', 'sum')).reset_index()
    result['tone'] = (result.n_positive_weight - result.n_negative_weight) / result.n_sentences
    result['tone_probability'] = result.pop('probability_sum') / result.n_sentences
    result['tone_source'] = VARIANTEN[variant]
    result['model'], result['revision'] = (MODELL, REVISION)
    return result

def tonalitaet(folder, variant):
    out = pfad(pfad(folder, 'aufbereitet'), 'kontext')
    meta_file = pfad(out, 'manifest.json')
    if not meta_file.exists():
        return pd.DataFrame(columns=['event_id', 'tone', 'tone_source'])
    meta = json.loads(meta_file.read_text(encoding='utf-8'))
    if (meta['model'], meta['revision'], meta['rule'], meta['sentence_split']) != (MODELL, REVISION, REGEL, SATZTRENNUNG_VERSION):
        raise ValueError('Verfahren der Kontextanalyse wurde geändert; Kontextanalyse neu ausführen.')
    if meta['transcripts_sha256'] != pruefsumme(pfad(pfad(folder, 'aufbereitet'), 'transcripts.csv')):
        raise ValueError('Kontextanalyse gehört zu älteren Transkripten; neu ausführen.')
    file = pfad(out, 'tone_' + variant + '.csv')
    for name, digest in meta['files'].items():
        if pruefsumme(pfad(out, name)) != digest:
            raise ValueError('Datei der Kontextanalyse wurde verändert: ' + name)
    data = lesen(file)
    weights = data[['n_positive_weight', 'n_negative_weight', 'n_neutral_weight']].to_numpy(float)
    total = weights.sum(axis=1)
    if data.event_id.duplicated().any() or not np.isfinite(weights).all() or (weights < 0).any() or (weights % 1 != 0).any() or (total <= 0).any():
        raise ValueError('Ungültige Gewichte in der Kontextanalyse.')
    expected = (weights[:, 0] - weights[:, 1]) / total
    if not np.allclose(total, data.n_sentences) or not np.allclose(expected, data.tone, rtol=0, atol=1e-12):
        raise ValueError('Tonalität passt nicht zu den Abschnittsgewichten.')
    return data[['event_id', 'tone', 'tone_source']]
