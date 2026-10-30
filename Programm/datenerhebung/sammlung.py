"""datenerhebung · sammlung – klar abgegrenzter Projektbaustein."""
from Programm.grundlagen.pfade import schreibziel_pruefen
from Programm.grundlagen.pfade import struktur_vorbereiten
from Programm.grundlagen.pfade import pfad
from Programm.datenerhebung.abruf import Abruf
from Programm.grundlagen.pfade import BESTAENDE
from Programm.grundlagen.pfade import ORDNER
from datetime import date, timedelta
from Programm.grundlagen.konfiguration import einstellungen
from Programm.datenerhebung.quartale import geschaeftsquartal
import hashlib
import json
from Programm.grundlagen.laufkennungen import kennung
from Programm.datenerhebung.abruf import ohne_schluessel
import os
from Programm.grundlagen.json_dateien import speichern
from Programm.grundlagen.konfiguration import suchbegriff
from Programm.grundlagen.laufkennungen import zeit

def sammeln(werte=None, keys=None, fortschritt=print):
    cfg = einstellungen(werte)
    keys = keys or {'alpha_vantage': os.getenv('ALPHA_VANTAGE_API_KEY', ''), 'serpapi': os.getenv('SERPAPI_API_KEY', '')}
    if not cfg['bestand']:
        cfg['bestand'] = kennung('bestand')
    folder = pfad(BESTAENDE, cfg['bestand'])
    schreibziel_pruefen(folder)
    folder.mkdir(parents=True, exist_ok=True)
    struktur_vorbereiten(folder)
    metadata = pfad(folder, 'bestand.json')
    created_at = zeit()
    if metadata.exists():
        old = json.loads(metadata.read_text(encoding='utf-8'))
        created_at = old['created_at']
        if old.get('art') != 'download':
            raise ValueError('Importbestände nicht mit Downloads vermischen. Neuen Bestand starten.')
        invariant = ['tickers', 'start', 'end', 'benchmark', 'queries', 'geo', 'meta_query_switch', 'fiscal_year_end']
        if any((old['config'][k] != cfg[k] for k in invariant)):
            raise ValueError('Für andere Unternehmen, Begriffe oder Zeiträume einen neuen Bestand anlegen.')
    speichern(metadata, {'art': 'download', 'created_at': created_at, 'config': cfg})
    speichern(pfad(ORDNER, 'einstellungen.json'), cfg)
    client = Abruf(folder, cfg, keys, fortschritt)
    speichern(pfad(folder, 'download_status.json'), {'status': 'running', 'started_at': zeit()})
    try:
        events = []
        for ticker in cfg['tickers']:
            payload = client.holen('alpha_vantage', 'earnings_' + ticker, {'function': 'EARNINGS', 'symbol': ticker})
            history = payload.get('quarterlyEarnings', [])
            if not history:
                raise ValueError(ticker + ': keine Quartalsberichte geliefert.')
            events.extend(((ticker, row) for row in history if cfg['start'] <= row.get('reportedDate', '') <= cfg['end']))
        if not events:
            raise ValueError('Keine Ereignisse im gewählten Berichtszeitraum.')
        for ticker in dict.fromkeys([cfg['benchmark'], *cfg['tickers']]):
            client.holen('alpha_vantage', 'prices_' + ticker, {'function': 'TIME_SERIES_DAILY_ADJUSTED', 'symbol': ticker, 'outputsize': 'full'})
        if cfg['download_transcripts']:
            for ticker, event in events:
                month = cfg['fiscal_year_end'].get(ticker)
                if month is None:
                    raise ValueError(ticker + ': Geschäftsjahresende in den Einstellungen ergänzen.')
                quarter = geschaeftsquartal(event['fiscalDateEnding'], month)
                client.holen('alpha_vantage', 'transcript_' + ticker + '_' + quarter, {'function': 'EARNINGS_CALL_TRANSCRIPT', 'symbol': ticker, 'quarter': quarter})
        if cfg['download_trends']:
            sections = sorted({(ticker, int(row['reportedDate'][:4]), suchbegriff(cfg, ticker, row['reportedDate'])) for ticker, row in events})
            for ticker, year, query in sections:
                start = date(year, 1, 1) - timedelta(days=120)
                end = min(date(year, 12, 31) + timedelta(days=14), date.today())
                # Auch Anfang eines Jahres einen hinreichend langen Zeitraum
                # abfragen, damit Trends Wochenwerte statt Tageswerte liefert.
                start = min(start, end - timedelta(days=370))
                term_id = hashlib.sha256(query.encode()).hexdigest()[:10]
                client.holen('serpapi', f'trends_{ticker}_{year}_{term_id}', {'engine': 'google_trends', 'q': query, 'date': f'{start} {end}', 'geo': cfg['geo'], 'data_type': 'TIMESERIES', 'tz': 0})
        status = {'status': 'complete', 'requests': client.anzahl, 'finished_at': zeit()}
    except Exception as exc:
        status = {'status': 'incomplete', 'requests': client.anzahl, 'message': ohne_schluessel(str(exc), keys.values()), 'finished_at': zeit()}
        speichern(pfad(folder, 'download_status.json'), status)
        raise
    speichern(pfad(folder, 'download_status.json'), status)
    fortschritt('Rohdaten gespeichert. Als Nächstes python -m Programm aufbereiten ausführen.')
    return {'bestand': cfg['bestand'], **status}
