"""werkzeuge · satzcache uebernahme – klar abgegrenzter Projektbaustein."""
from Programm.grundlagen.pfade import schreibziel_pruefen
from Programm.grundlagen.pfade import pfad
from Programm.grundlagen.standardwerte import MODELL
from Programm.sentiment.satztrennung import SATZTRENNUNG_VERSION
from Programm.grundlagen.pfade import bestand_ordner
import hashlib
import json
from Programm.grundlagen.konfiguration import laden
from Programm.grundlagen.tabellen import lesen
import numpy as np
import pandas as pd
from Programm.grundlagen.pruefsummen import pruefsumme
from Programm.sentiment.satztrennung import saetze
from Programm.grundlagen.tabellen import schreiben
from Programm.grundlagen.json_dateien import speichern
from Programm.berechnung.tonalitaet import tonalitaet

def vorbereiten():
    cfg = laden()
    target = bestand_ordner(cfg)
    schreibziel_pruefen(target)
    origin = json.loads(pfad(target, 'bestand.json').read_text(encoding='utf-8'))['basisbestand']
    base = pfad(target.parent, origin)
    meta = json.loads(pfad(pfad(base, 'aufbereitet'), 'finbert.json').read_text(encoding='utf-8'))
    if meta['model'] != MODELL or meta['revision'] != cfg['finbert_revision'] or meta['sentence_split'] != SATZTRENNUNG_VERSION:
        raise ValueError('Modell oder Satzregel des Quellbestands weicht ab.')
    tonalitaet(base, dict(cfg, sentiment_method='sentence'))
    old = lesen(pfad(pfad(base, 'aufbereitet'), 'finbert_saetze.csv'))
    if old.sentence_id.duplicated().any():
        raise ValueError('Doppelte Quellsatzkennung.')
    identity = [hashlib.sha256(f"{MODELL}|{cfg['finbert_revision']}|{r.event_id}|{r.turn_index}|{r.sentence_index}|{r.text}".encode('utf-8')).hexdigest() for r in old.itertuples()]
    if identity != old.sentence_id.tolist():
        raise ValueError('Quellsatzkennung passt nicht zu Text und Modell.')
    probabilities = old[['p_neutral', 'p_positive', 'p_negative']].to_numpy(float)
    labels = np.array(['neutral', 'positive', 'negative'])[probabilities.argmax(axis=1)]
    if not np.isfinite(probabilities).all() or (probabilities < 0).any() or (not np.allclose(probabilities.sum(axis=1), 1, atol=1e-05)) or (not np.array_equal(labels, old.label)):
        raise ValueError('Ungültige Quellvorhersagen.')
    actual = old.groupby(['event_id', 'label']).size().unstack(fill_value=0).reindex(columns=['positive', 'negative', 'neutral'], fill_value=0)
    expected = lesen(pfad(pfad(base, 'aufbereitet'), 'tone.csv')).set_index('event_id')
    if set(actual.index) != set(expected.index) or not np.array_equal(actual.to_numpy(), expected.loc[actual.index, ['n_positive', 'n_negative', 'n_neutral']].to_numpy()):
        raise ValueError('Quellvorhersagen passen nicht zur geprüften TONE-Tabelle.')
    conflicts = old.groupby('text').label.nunique()
    usable = old.loc[~old.text.isin(conflicts.index[conflicts.gt(1)])].drop_duplicates('text').set_index('text')
    cache_file = pfad(target, 'finbert_cache.csv')
    cached = lesen(cache_file) if cache_file.exists() else pd.DataFrame(columns=['sentence_id', 'label', 'p_neutral', 'p_positive', 'p_negative'])
    existing = set(cached.sentence_id)
    additions = []
    total = 0
    for turn in lesen(pfad(pfad(target, 'aufbereitet'), 'transcripts.csv')).itertuples():
        for index, sentence in enumerate(saetze(turn.content)):
            total += 1
            identity = hashlib.sha256(f"{MODELL}|{cfg['finbert_revision']}|{turn.event_id}|{turn.turn_index}|{index}|{sentence}".encode('utf-8')).hexdigest()
            if identity in existing or sentence not in usable.index:
                continue
            row = usable.loc[sentence]
            additions.append({'sentence_id': identity, **{col: row[col] for col in ['label', 'p_neutral', 'p_positive', 'p_negative']}})
            existing.add(identity)
    if additions:
        schreiben(pd.concat([cached, pd.DataFrame(additions)], ignore_index=True), cache_file)
    report = {'source_stock': origin, 'model': MODELL, 'revision': cfg['finbert_revision'], 'source_scored_sha256': pruefsumme(pfad(pfad(base, 'aufbereitet'), 'finbert_saetze.csv')), 'rule': 'Exakt gleicher Satztext, identisches Modell und Revision; keine Textnormalisierung', 'sentences_total': total, 'predictions_reused': len(additions), 'previous_current_cache': len(cached), 'remaining': total - len(existing)}
    speichern(pfad(target, 'Satzcache_Uebernahme.json'), report)
    print(json.dumps(report, ensure_ascii=False), flush=True)
