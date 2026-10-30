"""berechnung · berechnung – klar abgegrenzter Projektbaustein."""
from Programm.grundlagen.pfade import schreibziel_pruefen
from Programm.grundlagen.pfade import pfad, dateien
from Programm.berechnung.stichprobe import aufbereitung_pruefen
from Programm.grundlagen.pfade import bestand_ordner
from Programm.ausgabe.export.sqlite import datenbank
from Programm.grundlagen.konfiguration import einstellungen
from Programm.berechnung.gewinnueberraschung import gewinnueberraschungen
from Programm.berechnung.handelsvolumen import handelsvolumen
from Programm.grundlagen.tabellen import lesen
from Programm.berechnung.marktmodell import marktmodell
import numpy as np
import pandas as pd
from Programm.grundlagen.pruefsummen import pruefsumme
from Programm.berechnung.renditen import renditen
from Programm.grundlagen.tabellen import schreiben
from Programm.grundlagen.json_dateien import speichern
from Programm.berechnung.suchinteresse import suchinteresse
from Programm.berechnung.tonalitaet import tonalitaet
from Programm.grundlagen.laufkennungen import zeit

def berechnen(werte=None, fortschritt=print, export=True):
    cfg = einstellungen(werte)
    folder = bestand_ordner(cfg)
    if export:
        schreibziel_pruefen(folder)
    aufbereitung_pruefen(folder, cfg)
    prepared = pfad(folder, 'aufbereitet')
    prices, volume = (lesen(pfad(prepared, 'prices.csv')), lesen(pfad(prepared, 'volume.csv')))
    events = lesen(pfad(prepared, 'events.csv'))
    history = gewinnueberraschungen(lesen(pfad(prepared, 'earnings_history.csv')))
    weeks = lesen(pfad(prepared, 'trends_wochen.csv'))
    tone = tonalitaet(folder, cfg)
    dates = prices.loc[prices[cfg['benchmark']].gt(0), 'date'].to_numpy()
    prices = prices.set_index('date').reindex(dates)
    volume = volume.set_index('date').reindex(dates)
    returns = renditen(prices, cfg['return_type'])
    earnings = history.set_index('event_id')
    tones = tone.set_index('event_id')
    fallback = lesen(pfad(prepared, 'search_importiert.csv')).set_index('event_id') if pfad(prepared, 'search_importiert.csv').exists() else pd.DataFrame()
    records, days, exclusions = ([], [], [])
    for row in events.itertuples(index=False):
        record = row._asdict()
        problems = []
        for name in ['ue', 'sue_history_std', 'sue_history_n', 'sue']:
            record[name] = earnings.loc[row.event_id, name]
        record['sue_source'] = 'aus EPS-Historie berechnet'
        if pd.isna(record['sue']) and (not list(dateien(pfad(pfad(folder, 'roh'), 'alpha_vantage'), 'earnings_*.json'))) and (not pfad(pfad(folder, 'roh'), 'earnings_history.csv').exists()) and pd.notna(getattr(row, 'sue', np.nan)):
            record['sue'], record['sue_source'] = (float(row.sue), 'aus Import übernommen; Historie unvollständig')
        record['tone'] = tones.loc[row.event_id, 'tone'] if row.event_id in tones.index else np.nan
        record['tone_source'] = tones.loc[row.event_id, 'tone_source'] if row.event_id in tones.index else 'nicht verfügbar'
        record.update(suchinteresse(row, weeks, cfg))
        if weeks.empty and row.event_id in fallback.index:
            column = 'search' if 'search' in fallback else 'google_trends_attention'
            if column in fallback:
                record['search'] = pd.to_numeric(fallback.loc[row.event_id, column], errors='coerce')
                record['search_source'] = 'aus Import übernommen; kein Rohdatenexport vorhanden'
        record['car'], record['abs_car'] = (np.nan, np.nan)
        record['vol'], record['prevol'] = (np.nan, np.nan)
        if cfg['only_amc'] and row.release_timing != 'AMC':
            problems.append('Veröffentlichung nicht als AMC bekannt')
        if pd.isna(row.event_trading_day) or row.event_trading_day not in dates:
            problems.append('Ereignishandelstag fehlt')
        elif row.ticker not in returns:
            problems.append('Aktienkurse fehlen')
        else:
            index = int(np.flatnonzero(dates == row.event_trading_day)[0])
            first, last = cfg['estimation']
            a, b = cfg['window']
            if index + first < 1 or index + last >= len(dates) or index + a < 1 or (index + b >= len(dates)):
                problems.append('Kurszeitraum deckt Schätz-/Ereignisfenster nicht ab')
            else:
                try:
                    metrics, expected, abnormal = marktmodell(returns[row.ticker], returns[cfg['benchmark']], np.arange(index + first, index + last + 1), np.arange(index + a, index + b + 1))
                    record.update(metrics)
                    for day, exp, ar in zip(range(a, b + 1), expected, abnormal):
                        days.append({'event_id': row.event_id, 'ticker': row.ticker, 'event_trading_day': row.event_trading_day, 'relative_day': day, 'date': dates[index + day], 'actual_return': returns[row.ticker].iloc[index + day], 'market_return': returns[cfg['benchmark']].iloc[index + day], 'expected_return': exp, 'ar': ar})
                except ValueError as exc:
                    problems.append(str(exc))
            if row.ticker in volume:
                record.update(handelsvolumen(volume[row.ticker], index))
        record['event_study_ready'] = not problems and np.isfinite(record['car'])
        for name in cfg['predictors']:
            if not np.isfinite(record.get(name, np.nan)):
                problems.append(name.upper() + ' fehlt/ungültig')
        if not np.isfinite(record['car']):
            problems.append('CAR fehlt/ungültig')
        record['usable'] = not problems
        record['exclusion_reason'] = '; '.join(dict.fromkeys(problems))
        records.append(record)
        if problems:
            exclusions.append({'event_id': row.event_id, 'ticker': row.ticker, 'reason': record['exclusion_reason']})
    all_events = pd.DataFrame(records)
    for col in ['sue', 'search', 'vol', 'prevol']:
        all_events[col + '_raw'] = all_events[col]
    selected = all_events.loc[all_events.usable].copy()
    limits = {}
    if cfg['winsorize']:
        for col in ['sue', 'vol', 'prevol']:
            if col not in cfg['predictors']:
                continue
            low, high = selected[col].quantile([0.01, 0.99])
            selected[col] = selected[col].clip(low, high)
            limits[col] = {'lower': low, 'upper': high, 'sample_n': len(selected)}
    selected['abs_sue'] = selected.sue.abs()
    daily = pd.DataFrame(days, columns=['event_id', 'ticker', 'event_trading_day', 'relative_day', 'date', 'actual_return', 'market_return', 'expected_return', 'ar'])
    excluded = pd.DataFrame(exclusions, columns=['event_id', 'ticker', 'reason'])
    result = {'data': selected, 'events': all_events, 'daily': daily, 'exclusions': excluded, 'history': history, 'prices': prices.reset_index(), 'volume': volume.reset_index(), 'trends': weeks}
    if export:
        out = pfad(folder, 'berechnet')
        for name in ['data', 'events', 'daily', 'exclusions', 'history']:
            schreiben(result[name], pfad(out, name + '.csv'))
        datenbank(result, out, cfg)
        speichern(pfad(out, 'berechnung.json'), {'created_at': zeit(), 'config': cfg, 'winsorization': limits, 'sample_n': len(selected), 'all_n': len(all_events), 'inputs': {str(path.relative_to(folder)): pruefsumme(path) for path in sorted([*dateien(prepared, '*'), *(dateien(pfad(prepared, 'kontext'), '*') if cfg['sentiment_method'] != 'sentence' else [])]) if path.is_file()}, 'data_sha256': pruefsumme(pfad(out, 'data.csv')), 'daily_sha256': pruefsumme(pfad(out, 'daily.csv')), 'events_sha256': pruefsumme(pfad(out, 'events.csv'))})
        fortschritt(f'{len(selected)} verwendbare Ereignisse; {len(excluded)} Ausschlüsse. Datenbank und PSPP-Dateien gespeichert.')
    return result
