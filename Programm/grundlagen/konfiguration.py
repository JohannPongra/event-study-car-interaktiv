"""grundlagen · konfiguration – klar abgegrenzter Projektbaustein."""
from Programm.grundlagen.pfade import pfad
from Programm.grundlagen.pfade import ORDNER
from pathlib import Path
from Programm.grundlagen.standardwerte import STANDARD
import argparse
from datetime import date
import json
import re

def einstellungen(werte=None):
    cfg = json.loads(json.dumps(STANDARD))
    if werte is not None and (not isinstance(werte, dict)):
        raise ValueError('Einstellungen müssen ein JSON-Objekt sein.')
    cfg.update(werte or {})
    unbekannt = set(cfg) - set(STANDARD)
    if unbekannt:
        raise ValueError('Unbekannte Einstellungen: ' + ', '.join(sorted(unbekannt)))
    if isinstance(cfg['tickers'], str):
        cfg['tickers'] = re.split('[,;\\s]+', cfg['tickers'].strip().upper())
    if not isinstance(cfg['tickers'], list):
        raise ValueError('Unternehmen als Liste oder kommagetrennten Text angeben.')
    cfg['tickers'] = list(dict.fromkeys((str(t).upper() for t in cfg['tickers'] if t)))
    cfg['benchmark'] = str(cfg['benchmark']).strip().upper()
    if not cfg['tickers']:
        raise ValueError('Mindestens ein Unternehmen auswählen.')
    for ticker in [*cfg['tickers'], cfg['benchmark']]:
        if not re.fullmatch('[A-Z][A-Z0-9.-]{0,14}', ticker):
            raise ValueError('Ungültiger Ticker: ' + str(ticker))
    if cfg['benchmark'] in cfg['tickers']:
        raise ValueError('Der Benchmark darf keine untersuchte Aktie sein.')
    if date.fromisoformat(cfg['start']) > date.fromisoformat(cfg['end']):
        raise ValueError('Startdatum liegt nach dem Enddatum.')
    for name in ['window', 'estimation']:
        pair = cfg[name]
        if not isinstance(pair, list) or len(pair) != 2 or any((type(v) is not int for v in pair)) or (pair[0] > pair[1]):
            raise ValueError('Ungültiges Zeitfenster: ' + name)
    if not -20 <= cfg['window'][0] <= cfg['window'][1] <= 20:
        raise ValueError('Ereignisfenster muss innerhalb [-20,+20] liegen.')
    if cfg['estimation'][1] >= min(-10, cfg['window'][0]) or cfg['estimation'][1] - cfg['estimation'][0] < 29:
        raise ValueError('Schätzfenster muss mindestens 30 Tage umfassen und vor dem Ereignis enden.')
    if cfg['return_type'] not in {'log', 'simple'} or cfg['covariance'] not in {'cluster', 'HC3'}:
        raise ValueError('Ungültige Rendite- oder Standardfehlerwahl.')
    if not isinstance(cfg['predictors'], list) or not cfg['predictors'] or any((not isinstance(v, str) for v in cfg['predictors'])) or (len(set(cfg['predictors'])) != len(cfg['predictors'])) or (not set(cfg['predictors']) <= set(STANDARD['predictors'])):
        raise ValueError('Einflussgrößen müssen eindeutig und bekannt sein.')
    for key in ['fixed_effects', 'winsorize', 'only_amc', 'robustness', 'abs_car_robustness', 'download_trends', 'download_transcripts', 'abs_sue_for_abs_car']:
        if type(cfg[key]) is not bool:
            raise ValueError(key + ' muss true oder false sein.')
    if cfg['bestand'] and (not re.fullmatch('bestand_[0-9]{8}_[0-9]{6}_[a-f0-9]{6}', cfg['bestand'])):
        raise ValueError('Ungültige Datenbestandskennung.')
    if type(cfg['request_limit']) is not int or not 1 <= cfg['request_limit'] <= 5000:
        raise ValueError('Anfragelimit muss zwischen 1 und 5000 liegen.')
    if not isinstance(cfg['pause_seconds'], (int, float)) or not 0 <= cfg['pause_seconds'] <= 120:
        raise ValueError('Ungültige Pause.')
    if not re.fullmatch('[A-Z]{2}', cfg['geo']):
        raise ValueError('Region muss ein zweistelliges Länderkürzel sein.')
    if not re.fullmatch('[0-9a-f]{40}', cfg['finbert_revision']):
        raise ValueError('FinBERT braucht eine feste Modellrevision.')
    if type(cfg['finbert_batch_size']) is not int or not 1 <= cfg['finbert_batch_size'] <= 128:
        raise ValueError('FinBERT-Stapelgröße muss zwischen 1 und 128 liegen.')
    if cfg['sentiment_method'] not in {'sentence', 'lc_sentence', 'lc_context'}:
        raise ValueError('Unbekanntes Sentimentverfahren.')
    if not isinstance(cfg['fiscal_year_end'], dict) or not isinstance(cfg['queries'], dict):
        raise ValueError('Suchbegriffe und Geschäftsjahresenden müssen JSON-Objekte sein.')
    for ticker, month in cfg['fiscal_year_end'].items():
        if type(month) is not int or not 1 <= month <= 12:
            raise ValueError('Geschäftsjahresende muss ein Monat von 1 bis 12 sein.')
    for query in cfg['queries'].values():
        if not isinstance(query, str) or not query.strip() or len(query) > 100:
            raise ValueError('Ungültiger Suchbegriff.')
    date.fromisoformat(cfg['meta_query_switch'])
    return cfg

def laden(datei=None):
    datei = Path(datei) if datei else pfad(ORDNER, 'einstellungen.json')
    return einstellungen(json.loads(datei.read_text(encoding='utf-8-sig')) if datei.exists() else {})

def suchbegriff(cfg, ticker, berichtstag):
    if ticker == 'META' and berichtstag < cfg['meta_query_switch']:
        return 'Facebook stock'
    return cfg['queries'].get(ticker, ticker + ' stock')

def argumente(beschreibung):
    parser = argparse.ArgumentParser(description=beschreibung)
    parser.add_argument('--config', type=Path, help='Alternative Einstellungsdatei')
    return parser

def modell_predictors(cfg, outcome, predictors=None):
    """CAR nutzt SUE; das ergänzende Betragsmodell verwendet |SUE|."""
    selected = cfg['predictors'] if predictors is None else predictors
    return ['abs_sue' if col == 'sue' and outcome in {'abs_car', 'log_abs_car'} and cfg.get('abs_sue_for_abs_car', False) else col for col in selected]
