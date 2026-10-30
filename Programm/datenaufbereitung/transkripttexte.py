"""datenaufbereitung · transkripttexte – klar abgegrenzter Projektbaustein."""
from Programm.grundlagen.pfade import pfad
from Programm.datenaufbereitung.validierung import eindeutig
from Programm.datenerhebung.quartale import geschaeftsquartal
import json
from Programm.grundlagen.tabellen import lesen
import pandas as pd

def texte(raw, events, cfg):
    parts = []
    if pfad(raw, 'transcripts.csv').exists():
        parts.append(lesen(pfad(raw, 'transcripts.csv')))
    else:
        for _, row in events.iterrows():
            month = cfg['fiscal_year_end'].get(row.ticker)
            if not month:
                continue
            quarter = geschaeftsquartal(row.fiscal_date_ending, month)
            file = pfad(pfad(raw, 'alpha_vantage'), f'transcript_{row.ticker}_{quarter}.json')
            if not file.exists():
                continue
            payload = json.loads(file.read_text(encoding='utf-8-sig'))
            if payload.get('symbol', row.ticker) != row.ticker or payload.get('quarter', quarter) != quarter:
                raise ValueError('Transkript gehört zu einem anderen Unternehmen/Quartal: ' + file.name)
            turns = payload.get('transcript', [])
            if not isinstance(turns, list):
                raise ValueError('Unerwartetes Transkriptformat: ' + file.name)
            parts.append(pd.DataFrame([{'event_id': row.event_id, 'ticker': row.ticker, 'turn_index': i, 'speaker': turn.get('speaker', ''), 'speaker_title': turn.get('title', ''), 'content': turn.get('content', '')} for i, turn in enumerate(turns)]))
    frame = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=['event_id', 'ticker', 'turn_index', 'speaker', 'speaker_title', 'content'])
    if not {'event_id', 'content'} <= set(frame):
        raise ValueError('Transkripte brauchen event_id und content.')
    frame = frame.loc[frame.event_id.isin(events.event_id)].copy()
    if 'turn_index' not in frame:
        frame['turn_index'] = frame.groupby('event_id').cumcount()
    eindeutig(frame, ['event_id', 'turn_index'], 'Transkripte')
    return frame
