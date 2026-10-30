from Programm.grundlagen.standardwerte import MODELL
import hashlib
import pandas as pd
from Programm.sentiment.satztrennung import saetze

def satzdaten(texts, cfg):
    rows = []
    for _, turn in texts.sort_values(['event_id', 'turn_index']).iterrows():
        if pd.isna(turn.content):
            continue
        for index, sentence in enumerate(saetze(turn.content)):
            identity = f"{MODELL}|{cfg['finbert_revision']}|{turn.event_id}|{turn.turn_index}|{index}|{sentence}"
            rows.append({'sentence_id': hashlib.sha256(identity.encode('utf-8')).hexdigest(), 'event_id': turn.event_id, 'turn_index': turn.turn_index, 'sentence_index': index, 'text': sentence})
    if not rows:
        raise ValueError('Keine Transkriptsätze vorhanden. Texte importieren oder herunterladen.')
    sentences = pd.DataFrame(rows)
    return sentences
