"""berechnung · tonalitaet – klar abgegrenzter Projektbaustein."""
from Programm.grundlagen.pfade import pfad
from Programm.sentiment.satztrennung import SATZTRENNUNG_VERSION
import json
from Programm.grundlagen.tabellen import lesen
import pandas as pd
from Programm.grundlagen.pruefsummen import pruefsumme
from Programm.sentiment.tonalitaet import tonwert

def tonalitaet(folder, cfg):
    if cfg.get('sentiment_method', 'sentence') != 'sentence':
        from Programm.sentiment.kontext.aggregierung import tonalitaet as lc_tonalitaet
        return lc_tonalitaet(folder, cfg['sentiment_method'])
    out = pfad(folder, 'aufbereitet')
    file = pfad(out, 'tone.csv')
    if file.exists():
        meta = json.loads(pfad(out, 'finbert.json').read_text(encoding='utf-8'))
        if meta.get('sentence_split') != SATZTRENNUNG_VERSION:
            raise ValueError('Die Satztrennung wurde geändert. Zuerst FinBERT erneut ausführen, danach Berechnung und Regression.')
        if meta['revision'] != cfg['finbert_revision'] or meta['transcripts_sha256'] != pruefsumme(pfad(out, 'transcripts.csv')) or meta['tone_sha256'] != pruefsumme(file):
            raise ValueError('FinBERT-Ergebnisse sind veraltet oder verändert. FinBERT erneut ausführen.')
    else:
        file = pfad(out, 'tone_importiert.csv')
    if not file.exists():
        return pd.DataFrame(columns=['event_id', 'tone', 'tone_source'])
    frame = lesen(file)
    if {'n_positive', 'n_negative', 'n_neutral'} <= set(frame):
        counts = frame[['n_positive', 'n_negative', 'n_neutral']].apply(pd.to_numeric, errors='coerce')
        if counts.isna().any().any() or (counts < 0).any().any() or (counts % 1 != 0).any().any():
            raise ValueError('FinBERT-Satzzahlen sind ungültig.')
        frame['tone'] = [tonwert(*row) for row in counts.to_numpy()]
    if 'tone' not in frame:
        raise ValueError('Importierte Tonalität braucht tone oder die drei Satzzahlen.')
    frame['tone'] = pd.to_numeric(frame.tone, errors='coerce')
    if frame.tone.dropna().abs().gt(1).any():
        raise ValueError('TONE liegt außerhalb [-1,+1].')
    frame['tone_source'] = 'FinBERT neu berechnet' if file.name == 'tone.csv' else 'aus bestehender FinBERT-Tabelle übernommen'
    return frame[['event_id', 'tone', 'tone_source']]

def tondefinition(cfg):
    method = cfg.get('sentiment_method', 'sentence')
    return {'sentence': 'FinBERT-Tonalität: (positive minus negative Sätze) / (positive + negative + neutrale Sätze)', 'lc_sentence': 'finbert-lc, einzelne Sätze: (positive minus negative Sätze) / alle Sätze einschließlich neutraler', 'lc_context': 'finbert-lc, natürliche Mehrsatzabschnitte bis 512 Tokens: Abschnittsklasse (+1/0/-1) gewichtet mit Satzanzahl, geteilt durch alle Sätze einschließlich neutraler'}[method]
