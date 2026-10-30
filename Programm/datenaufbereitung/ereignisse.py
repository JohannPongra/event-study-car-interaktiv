"""datenaufbereitung · ereignisse – klar abgegrenzter Projektbaustein."""
from Programm.grundlagen.pfade import pfad, dateien
from Programm.datenaufbereitung.validierung import eindeutig
import json
from Programm.grundlagen.tabellen import lesen
import numpy as np
import pandas as pd

def ereignisse(raw, prices, cfg):
    all_history = []
    for file in sorted(dateien(pfad(raw, 'alpha_vantage'), 'earnings_*.json')):
        if file.name.endswith('.quelle.json'):
            continue
        ticker = file.stem.removeprefix('earnings_')
        payload = json.loads(file.read_text(encoding='utf-8-sig'))
        if payload.get('symbol', ticker) != ticker:
            raise ValueError('Ticker stimmt nicht mit Earnings-Datei überein: ' + file.name)
        for row in payload.get('quarterlyEarnings', []):
            all_history.append({'ticker': ticker, 'fiscal_date_ending': row.get('fiscalDateEnding'), 'reported_date': row.get('reportedDate'), 'reported_eps': row.get('reportedEPS'), 'estimated_eps': row.get('estimatedEPS'), 'release_timing': row.get('reportTime', 'unknown'), 'timing_source': 'Alpha Vantage reportTime', 'eps_source': file.name})
    history = pd.DataFrame(all_history)
    if history.empty and pfad(raw, 'earnings_history.csv').exists():
        history = lesen(pfad(raw, 'earnings_history.csv'))
    imported = lesen(pfad(raw, 'events.csv')) if pfad(raw, 'events.csv').exists() else pd.DataFrame()
    if history.empty:
        history = imported.copy()
    needed = ['ticker', 'reported_date', 'fiscal_date_ending', 'reported_eps', 'estimated_eps']
    if not set(needed) <= set(history):
        raise ValueError('EPS-/Ereignisdaten benötigen: ' + ', '.join(needed))
    if history[['ticker', 'reported_date', 'fiscal_date_ending']].isna().any().any():
        raise ValueError('Ticker, Berichtsdatum und Quartalsende dürfen nicht fehlen.')
    for col in ['reported_date', 'fiscal_date_ending']:
        history[col] = pd.to_datetime(history[col], errors='raise').dt.strftime('%Y-%m-%d')
    history['ticker'] = history['ticker'].str.upper()
    for col in ['reported_eps', 'estimated_eps']:
        history[col] = pd.to_numeric(history[col], errors='coerce')
    history['event_id'] = history['ticker'] + '_' + history['reported_date']
    eindeutig(history, ['event_id'], 'EPS-Historie')
    history.sort_values(['ticker', 'reported_date'], inplace=True)
    events = history.loc[history.ticker.isin(cfg['tickers']) & history.reported_date.between(cfg['start'], cfg['end'])].copy()
    if events.empty:
        raise ValueError('Keine Ereignisse für diese Auswahl.')
    if not imported.empty:
        imported['ticker'] = imported.ticker.str.upper()
        imported['reported_date'] = pd.to_datetime(imported.reported_date, errors='raise').dt.strftime('%Y-%m-%d')
        canonical = imported.ticker + '_' + imported.reported_date
        if 'event_id' not in imported:
            imported['event_id'] = canonical
        elif not imported.event_id.eq(canonical).all():
            raise ValueError('event_id muss TICKER_YYYY-MM-DD des Berichts entsprechen.')
        eindeutig(imported, ['event_id'], 'Importierte Ereignisse')
        for col in ['company_name', 'release_timing', 'report_time_source', 'report_time_verified', 'sue']:
            if col in imported:
                mapped = events.event_id.map(imported.set_index('event_id')[col])
                events[col] = mapped.combine_first(events[col]) if col in events else mapped
        if 'report_time_source' in events:
            events['timing_source'] = events['report_time_source']
    if 'release_timing' not in events:
        events['release_timing'] = 'unknown'
    if 'report_time_verified' not in events:
        events['report_time_verified'] = False
    times = pfad(raw, 'veroeffentlichungszeiten.csv')
    if times.exists():
        overrides = lesen(times).set_index('event_id')
        if overrides.index.duplicated().any() or not {'release_timing', 'source'} <= set(overrides):
            raise ValueError('Veröffentlichungszeiten benötigen eindeutige event_id, release_timing und source.')
        for key, value in overrides.iterrows():
            selected = events.event_id.eq(key)
            events.loc[selected, 'release_timing'] = value.release_timing
            events.loc[selected, 'timing_source'] = value.source
            events.loc[selected, 'report_time_verified'] = bool(pd.notna(value.source) and str(value.source).strip())
    timing = {'post-market': 'AMC', 'after market close': 'AMC', 'amc': 'AMC', 'pre-market': 'BMO', 'before market open': 'BMO', 'bmo': 'BMO'}
    events['release_timing'] = events.release_timing.fillna('unknown').map(lambda s: timing.get(str(s).strip().lower(), 'unknown'))
    if cfg['benchmark'] not in prices:
        raise ValueError('Kurse des Benchmarks fehlen: ' + cfg['benchmark'])
    calendar = pd.to_datetime(prices.loc[prices[cfg['benchmark']].gt(0), 'date']).sort_values().to_numpy()

    def handelstag(row):
        side = 'right' if row.release_timing == 'AMC' else 'left'
        if row.release_timing == 'unknown':
            return None
        index = np.searchsorted(calendar, np.datetime64(row.reported_date), side=side)
        return str(calendar[index])[:10] if index < len(calendar) else None
    events['event_trading_day'] = events.apply(handelstag, axis=1)
    events['year'] = events.reported_date.str[:4].astype(int)
    events['quarter'] = pd.to_datetime(events.reported_date).dt.quarter
    return (history, events)
