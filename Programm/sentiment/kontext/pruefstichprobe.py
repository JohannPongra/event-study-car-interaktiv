from Programm.grundlagen.pfade import pfad
from Programm.grundlagen.tabellen import lesen
import pandas as pd
from Programm.grundlagen.tabellen import schreiben

def pruefstichprobe(folder, out):
    scored = lesen(pfad(pfad(pfad(folder, 'aufbereitet'), 'kontext'), 'lc_abschnitte.csv'))
    scored['ticker'] = scored.event_id.str.split('_').str[0]
    scored['year'] = scored.event_id.str.split('_').str[1].str[:4]
    review_parts = []
    for _, company in scored.groupby('ticker'):
        selected = pd.concat([part.sample(n=min(4, len(part)), random_state=241209) for _, part in company.groupby('year')])
        needed = min(40, len(company)) - len(selected)
        if needed > 0:
            selected = pd.concat([selected, company.drop(index=selected.index).sample(n=needed, random_state=241209)])
        review_parts.append(selected)
    review = pd.concat(review_parts, ignore_index=True)
    review = review[['event_id', 'turn_index', 'sentence_first', 'sentence_last', 'n_sentences', 'tokens', 'text']]
    review['menschliches_label'] = ''
    review['anmerkung'] = ''
    schreiben(review, pfad(out, 'Manuelle_Pruefstichprobe.csv'))
