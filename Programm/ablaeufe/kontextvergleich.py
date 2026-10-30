"""ablaeufe · kontextvergleich – klar abgegrenzter Projektbaustein."""
from Programm.statistik.sentimentvergleich import vergleichskennzahlen
from Programm.sentiment.kontext.klassenverteilung import klassenverteilung
from Programm.ausgabe.grafiken.sentimentvergleich import vergleichsgrafiken
from Programm.ausgabe.bericht.sentimentvergleich import vergleichsbericht
from Programm.sentiment.kontext.pruefstichprobe import pruefstichprobe
from Programm.sentiment.kontext.methoden import METHODEN
from Programm.grundlagen.pfade import pfad
from Programm.grundlagen.pfade import ERGEBNISSE
from Programm.grundlagen.pfade import ORDNER
from Programm.berechnung.berechnung import berechnen
from Programm.grundlagen.pfade import bestand_ordner
from Programm.grundlagen.konfiguration import einstellungen
from Programm.grundlagen.laufkennungen import kennung
from Programm.grundlagen.konfiguration import laden
from Programm.grundlagen.tabellen import lesen
import matplotlib
matplotlib.use('Agg')
from Programm.grundlagen.pruefsummen import pruefsumme
from Programm.statistik.auswertung import regressieren
from Programm.grundlagen.tabellen import schreiben
from Programm.grundlagen.json_dateien import speichern
from Programm.berechnung.tonalitaet import tonalitaet
from Programm.datenaufbereitung.aufbereitung import verarbeiten
from Programm.grundlagen.laufkennungen import zeit

def vergleichen(werte=None, fortschritt=print):
    cfg = einstellungen(werte if werte is not None else laden())
    if 'tone' not in cfg['predictors']:
        raise ValueError('Für den Sentimentvergleich zuerst die Einflussgröße Tonalität auswählen.')
    folder = bestand_ordner(cfg)
    verarbeiten(cfg, fortschritt)
    tones = {}
    for method in METHODEN:
        current = dict(cfg, sentiment_method=method)
        tone = tonalitaet(folder, current)
        if tone.empty:
            if method == 'sentence':
                from Programm.sentiment.auswertung import auswerten
            else:
                from Programm.sentiment.kontext.auswertung import auswerten
            auswerten(current, fortschritt)
            tone = tonalitaet(folder, current)
        tones[method] = tone
    samples = {method: berechnen(dict(cfg, sentiment_method=method), fortschritt, export=False) for method in METHODEN}
    ids = set(samples['sentence']['data'].event_id)
    if not ids or any((set(result['data'].event_id) != ids for result in samples.values())):
        raise ValueError('Die Sentimentverfahren liefern unterschiedliche vollständige Stichproben; Vergleich nicht ausgeführt.')
    data = samples['sentence']['data'][['event_id', 'ticker', 'reported_date', 'event_trading_day', 'car', 'abs_car']].copy()
    results, coefficients = ({}, [])
    for method in METHODEN:
        current = dict(cfg, sentiment_method=method)
        fortschritt(METHODEN[method] + ': vollständige Event Study und Regressionen …')
        berechnen(current, fortschritt)
        result = regressieren(current, fortschritt)
        results[method] = result
        coef = lesen(pfad(pfad(ERGEBNISSE, result['ordner']), 'koeffizienten.csv'))
        coef = coef.loc[coef.variable.eq('tone')].copy()
        coef.insert(0, 'sentiment_method', method)
        coefficients.append(coef)
        data = data.merge(tones[method][['event_id', 'tone']].rename(columns={'tone': method}), on='event_id', how='left', validate='one_to_one')
    corr, coefs = vergleichskennzahlen(data, coefficients)
    out = pfad(ERGEBNISSE, kennung('vergleich'))
    out.mkdir(parents=True)
    schreiben(data, pfad(out, 'Call_Tonwerte.csv'))
    schreiben(corr, pfad(out, 'Korrelationen.csv'))
    schreiben(coefs, pfad(out, 'TONE_Koeffizienten.csv'))
    distribution = klassenverteilung(folder)
    schreiben(distribution, pfad(out, 'Klassenverteilung.csv'))
    vergleichsgrafiken(out, data, coefs)
    vergleichsbericht(out, data, corr, coefs, distribution, results)
    pruefstichprobe(folder, out)
    pfad(out, 'Methodik.md').write_text(pfad(ORDNER, 'KONTEXT_SENTIMENT.md').read_text(encoding='utf-8'), encoding='utf-8')
    speichern(pfad(out, 'manifest.json'), {'created_at': zeit(), 'config': cfg, 'n': len(data), 'analysen': {m: r['ordner'] for m, r in results.items()}, 'methoden': METHODEN, 'transcripts_sha256': pruefsumme(pfad(pfad(folder, 'aufbereitet'), 'transcripts.csv')), 'lc_manifest_sha256': pruefsumme(pfad(pfad(pfad(folder, 'aufbereitet'), 'kontext'), 'manifest.json')), 'gemeinsame_stichprobe': True, 'nsp_used': False, 'dateien': {p.name: pruefsumme(p) for p in out.iterdir() if p.is_file()}})
    speichern(pfad(folder, 'letzter_sentimentvergleich.json'), {'ordner': out.name, 'n': len(data), 'analysen': {m: r['ordner'] for m, r in results.items()}})
    from Programm.ausgabe.verzeichnis import aktualisieren
    aktualisieren()
    fortschritt('Sentimentvergleich gespeichert: ' + str(out))
    return {'ordner': results[cfg['sentiment_method']]['ordner'], 'vergleich': out.name, 'n': len(data), 'bericht': str(pfad(out, 'bericht.html'))}
