"""datenaufbereitung · suchinteresse – klar abgegrenzter Projektbaustein."""
from Programm.grundlagen.pfade import pfad, dateien
import csv
from datetime import date, timedelta
from Programm.datenaufbereitung.validierung import eindeutig
import io
import json
import pandas as pd
from Programm.grundlagen.pruefsummen import pruefsumme

def trends_csv(file):
    lines = file.read_text(encoding='utf-8-sig').splitlines()
    start = next((i for i, line in enumerate(lines) if line.startswith(('Woche,', 'Week,', 'Woche;', 'Week;'))), None)
    if start is None:
        raise ValueError('Trends-CSV braucht den originalen Wochenkopf: ' + file.name)
    delimiter = ';' if ';' in lines[start] else ','
    rows = list(csv.reader(io.StringIO('\n'.join(lines[start:])), delimiter=delimiter))
    if len(rows[0]) != 2:
        raise ValueError('Je Trends-Export genau einen Suchbegriff verwenden: ' + file.name)
    query = rows[0][1].split(': (')[0].strip()
    ticker = file.name.split('_')[0].upper()
    values = [{'week': row[0], 'svi': row[1]} for row in rows[1:] if len(row) == 2 and row[0]]
    return (ticker, query, pd.DataFrame(values, columns=['week', 'svi']))

def trends(raw):
    parts, audit = ([], [])
    sources = [(p, 'csv') for p in sorted(dateien(pfad(raw, 'trends'), '*.csv'))]
    sources += [(p, 'json') for p in sorted(dateien(pfad(raw, 'serpapi'), 'trends_*.json')) if not p.name.endswith('.quelle.json')]
    for file, kind in sources:
        if kind == 'csv':
            ticker, query, frame = trends_csv(file)
        else:
            meta = json.loads(file.with_suffix('.quelle.json').read_text(encoding='utf-8'))
            ticker, query = (file.stem.split('_')[1], meta['request']['q'])
            payload = json.loads(file.read_text(encoding='utf-8'))
            values = []
            for row in payload.get('interest_over_time', {}).get('timeline_data', []):
                if row.get('isPartial') or row.get('is_partial'):
                    continue
                metrics = row.get('values', [])
                if len(metrics) != 1:
                    raise ValueError('Trends-Antwort braucht einen Suchbegriff: ' + file.name)
                week = pd.to_datetime(int(row['timestamp']), unit='s', utc=True).strftime('%Y-%m-%d')
                if date.fromisoformat(week) + timedelta(days=7) > date.today():
                    continue
                values.append({'week': week, 'svi': metrics[0].get('extracted_value', metrics[0].get('value'))})
            frame = pd.DataFrame(values, columns=['week', 'svi'])
        if frame.empty:
            raise ValueError('Leerer Trends-Export: ' + file.name)
        frame['week'] = pd.to_datetime(frame.week, errors='raise')
        eindeutig(frame, ['week'], 'Trends ' + file.name)
        frame.sort_values('week', inplace=True)
        dates = frame.week.dt.date.tolist()
        if len(dates) < 9 or any((b - a != timedelta(days=7) for a, b in zip(dates, dates[1:]))) or any((d.weekday() != 6 for d in dates)):
            raise ValueError('Trends benötigt mindestens neun aufeinanderfolgende Sonntagswochen: ' + file.name)
        original = frame.svi.astype(str)
        frame['svi'] = pd.to_numeric(frame.svi, errors='coerce')
        if ((frame.svi < 0) | (frame.svi > 100)).any():
            raise ValueError('Trends-Werte außerhalb 0 bis 100: ' + file.name)
        frame['censored'] = original.str.startswith('<')
        frame['week'] = frame.week.dt.strftime('%Y-%m-%d')
        frame['ticker'], frame['query'], frame['export_id'] = (ticker, query, file.name)
        frame['supplemental'] = '2017_2018' in file.name
        frame['source_sha256'] = pruefsumme(file)
        parts.append(frame)
        audit.append({'export_id': file.name, 'ticker': ticker, 'query': query, 'weeks': len(frame), 'start': frame.week.iloc[0], 'end': frame.week.iloc[-1], 'missing': int(frame.svi.isna().sum()), 'zeros': int(frame.svi.eq(0).sum()), 'sha256': pruefsumme(file)})
    result = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=['week', 'svi', 'ticker', 'query', 'export_id', 'supplemental', 'source_sha256'])
    return (result, pd.DataFrame(audit, columns=['export_id', 'ticker', 'query', 'weeks', 'start', 'end', 'missing', 'zeros', 'sha256']))
