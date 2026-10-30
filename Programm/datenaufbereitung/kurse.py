"""datenaufbereitung · kurse – klar abgegrenzter Projektbaustein."""
from Programm.grundlagen.pfade import pfad, dateien
from Programm.datenaufbereitung.validierung import eindeutig
import json
from Programm.grundlagen.tabellen import lesen
import pandas as pd

def kurse(raw):
    if pfad(raw, 'prices.csv').exists():
        prices, volume = (lesen(pfad(raw, 'prices.csv')), lesen(pfad(raw, 'volume.csv')) if pfad(raw, 'volume.csv').exists() else pd.DataFrame(columns=['date']))
    else:
        price_parts, volume_parts = ([], [])
        for file in sorted(dateien(pfad(raw, 'alpha_vantage'), 'prices_*.json')):
            if file.name.endswith('.quelle.json'):
                continue
            ticker = file.stem.removeprefix('prices_')
            payload = json.loads(file.read_text(encoding='utf-8-sig'))
            rows = payload.get('Time Series (Daily)', {})
            if not rows:
                raise ValueError(ticker + ': keine täglichen adjustierten Kurse.')
            frame = pd.DataFrame.from_dict(rows, orient='index').sort_index()
            frame.index.name = 'date'
            price_parts.append(pd.to_numeric(frame['5. adjusted close'], errors='coerce').rename(ticker))
            splits = pd.to_numeric(frame['8. split coefficient'], errors='coerce')
            if splits.isna().any() or (splits <= 0).any():
                raise ValueError(ticker + ': ungültige Splitfaktoren.')
            future = splits.iloc[::-1].cumprod().iloc[::-1] / splits
            volume_parts.append((pd.to_numeric(frame['6. volume'], errors='coerce') * future).rename(ticker))
        if not price_parts:
            raise ValueError('Kursdaten fehlen.')
        prices = pd.concat(price_parts, axis=1).rename_axis('date').reset_index()
        volume = pd.concat(volume_parts, axis=1).rename_axis('date').reset_index()
    for name, frame in [('prices', prices), ('volume', volume)]:
        if 'date' not in frame:
            raise ValueError(name + ': Spalte date fehlt.')
        frame['date'] = pd.to_datetime(frame['date'], errors='raise').dt.strftime('%Y-%m-%d')
        eindeutig(frame, ['date'], name)
        for col in frame.columns.difference(['date']):
            frame[col] = pd.to_numeric(frame[col], errors='coerce')
        frame.sort_values('date', inplace=True)
    return (prices, volume)
