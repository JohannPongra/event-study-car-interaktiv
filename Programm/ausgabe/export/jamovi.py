"""ausgabe · export · jamovi – klar abgegrenzter Projektbaustein."""
from Programm.grundlagen.pfade import pfad
from Programm.ausgabe.formatierung import renditeeinheit
import numpy as np
import pandas as pd
from Programm.grundlagen.pruefsummen import pruefsumme
from Programm.grundlagen.tabellen import schreiben
from Programm.grundlagen.json_dateien import speichern
from Programm.berechnung.tonalitaet import tondefinition
from Programm.grundlagen.laufkennungen import zeit
JAMOVI_SPALTEN = ['event_id', 'ticker', 'reported_date', 'event_trading_day', 'year', 'quarter', 'car', 'abs_car', 'sue', 'vol', 'prevol', 'tone', 'search']

def jamovi_export(data, out, cfg):
    """Eine eindeutige Ereigniszeile; jamovi bildet Faktor-Kontraste selbst."""
    missing = sorted(set(JAMOVI_SPALTEN) - set(data))
    if missing:
        raise ValueError('Jamovi-Export: Spalten fehlen: ' + ', '.join(missing))
    frame = data[JAMOVI_SPALTEN].copy()
    if cfg.get('abs_sue_for_abs_car', False):
        frame['abs_sue'] = frame.sue.abs()
    ids = frame.event_id.astype('string').str.strip()
    if ids.isna().any() or ids.eq('').any() or ids.duplicated().any():
        raise ValueError('Jamovi-Export: Jede event_id muss vorhanden und eindeutig sein; doppelte Ereignisse werden nicht zusammengefasst.')
    required = list(dict.fromkeys(['car', 'abs_car', *cfg['predictors']]))
    numeric = frame[required].apply(pd.to_numeric, errors='coerce')
    if not np.isfinite(numeric.to_numpy(dtype=float)).all():
        raise ValueError('Jamovi-Export: Ein Wert des gewählten Regressionsmodells fehlt oder ist ungültig.')
    if not np.allclose(numeric.abs_car, numeric.car.abs(), rtol=1e-12, atol=1e-14):
        raise ValueError('Jamovi-Export: ABS_CAR stimmt nicht mit dem Betrag der CAR überein.')
    out.mkdir(parents=True, exist_ok=True)
    schreiben(frame, pfad(out, 'Jamovi_Daten.csv'))
    frame.to_csv(pfad(out, 'Uebersichtliche_Daten.csv'), index=False, sep=';', decimal=',', encoding='utf-8-sig', na_rep='')
    window = '[' + ', '.join((f'{v:+d}' for v in cfg['window'])) + ']'
    winsorized = [name for name in ['sue', 'vol', 'prevol'] if cfg['winsorize'] and name in cfg['predictors']]
    definitions = [('event_id', 'Eindeutige Kennung des Ergebnisberichts; genau eine Zeile je Ereignis', 'ID', 'Text'), ('ticker', 'Unternehmen bzw. Börsenkürzel; Kategorie für Unternehmenseffekte', 'Nominal', 'Text'), ('reported_date', 'Veröffentlichungsdatum des Ergebnisberichts', 'ID', 'JJJJ-MM-TT'), ('event_trading_day', 'Zugeordneter Ereignishandelstag (Tag 0); Datum für Cluster', 'ID', 'JJJJ-MM-TT'), ('year', 'Kalenderjahr des Veröffentlichungsdatums; Kategorie für Jahreseffekte', 'Nominal', 'Jahr'), ('quarter', 'Kalenderquartal des Veröffentlichungsdatums; Kategorie für Quartalseffekte', 'Nominal', '1 bis 4'), ('car', f"Kumulative abnormale Rendite: Summe der AR im Ereignisfenster {window}; Marktmodell mit {cfg['benchmark']}", 'Stetig', f'Dezimalrendite; 0,01 = 1 {renditeeinheit(cfg, singular=True)}'), ('abs_car', 'Betrag der kumulativen abnormalen Rendite: abs(CAR)', 'Stetig', 'Dezimalrendite'), ('sue', 'Standardisierte Gewinnüberraschung: tatsächliches EPS minus erwartetes EPS, geteilt durch die Stichproben-SD der acht vorherigen UE; ggf. übernommener Importwert gemäß Herkunftsnachweis', 'Stetig', 'dimensionslos'), ('vol', 'Mittleres standardisiertes abnormales Handelsvolumen an den Handelstagen [0,+1]; logarithmiertes Volumen relativ zu Mittelwert und Stichproben-SD in [-60,-10]', 'Stetig', 'Standardabweichungen'), ('prevol', 'Mittleres standardisiertes abnormales Handelsvolumen an den Handelstagen [-3,-1]; gleiche Basis wie VOL', 'Stetig', 'Standardabweichungen'), ('tone', tondefinition(cfg), 'Stetig', '-1 bis +1'), ('search', 'Aufmerksamkeit: ln(SVI der Ereigniswoche / Median der acht Vorwochen desselben Trends-Exports); ggf. übernommener Importwert gemäß Herkunftsnachweis', 'Stetig', 'Log-Verhältnis')]
    if 'abs_sue' in frame:
        definitions.append(('abs_sue', 'Betrag der SUE; nur für das ABS_CAR-Modell anstelle von SUE', 'Stetig', 'dimensionslos'))
    codebook = pd.DataFrame([{'variable': name, 'beschreibung': description, 'messniveau': level, 'einheit': unit, 'bearbeitung': 'Auf dem 1%- und 99%-Quantil der Regressionsstichprobe winsorisiert' if name in winsorized else 'Berechneter bzw. zugeordneter Wert'} for name, description, level, unit in definitions])
    schreiben(codebook, pfad(out, 'Jamovi_Variablen.csv'))
    factors = 'ticker, year und quarter unter Faktoren; nur Haupteffekte, keine Wechselwirkungen' if cfg['fixed_effects'] else 'Faktoren leer lassen (dieser Lauf hat keine festen Effekte)'
    winsor_text = ', '.join((name.upper() for name in winsorized)) or 'keine Variablen'
    pfad(out, 'Jamovi_Anleitung.md').write_text(f"# Eine Zeile je Ereignis\n\n**Jamovi_Daten.csv** enthält {len(frame)} Ereignisse mit {len(frame.columns)} Spalten.\nJede event_id ist eindeutig. CAR, ABS_CAR, SUE, VOL, PREVOL, TONE und SEARCH stehen jeweils in derselben Ereigniszeile.\nDie Datentabelle enthält keine fe_-Hilfsspalten, Rohwert-Doppelungen oder Zwischenrechnungen.\nDie vollständige Herkunft und die Rohwerte bleiben in der Datenbank bzw. im ausführlichen Analysedatensatz dokumentiert.\n\n## In Excel oder einem anderen deutschen Tabellenprogramm öffnen\n\n**Uebersichtliche_Daten.csv** enthält dieselben Werte in {len(frame.columns)} getrennten Spalten.\nFormat: Semikolon als Trennzeichen, Komma als Dezimalzeichen, UTF-8 mit BOM.\nBei abweichenden Regionseinstellungen: Daten → Aus Text/CSV → Trennzeichen **Semikolon** wählen.\nFür jamovi den separaten Export **Jamovi_Daten.csv** verwenden (Komma als Trennzeichen, Dezimalpunkt).\n\n## In jamovi verwenden\n\n1. Datei → Öffnen → Jamovi_Daten.csv auswählen.\n2. Analysen → Regression → Lineare Regression wählen.\n3. Abhängige Variable: car; für das zweite Modell abs_car.\n4. Kovariaten im CAR-Modell: {', '.join(cfg['predictors'])}. Im ABS_CAR-Modell SUE durch abs_sue ersetzen, wenn abs_sue_for_abs_car aktiviert ist.\n5. {factors}.\n6. Bei neuen Importen Messniveaus anhand von Jamovi_Variablen.csv kontrollieren und das Dokument als .omv speichern.\n\nUnternehmen, Jahr und Quartal erlauben dieselben Kontrollen ohne zusätzliche Dummyspalten.\n„FE“ bedeutet feste Effekte. Diese Hilfsspalten sind keine weiteren erhobenen Einflussgrößen.\nPREVOL und VOL messen Handelsvolumen, nicht Kursvolatilität.\nCAR und ABS_CAR sind zwei alternative Zielgrößen; ABS_CAR wird nicht zusätzlich als Einflussgröße für CAR eingesetzt.\n\n## Festlegungen dieses Exports\n\n- CAR-Ereignisfenster: {window}; Schätzfenster: {cfg['estimation']}; Benchmark: {cfg['benchmark']}; Renditeart: {cfg['return_type']}.\n- VOL bleibt auf [0,+1], PREVOL auf [-3,-1] festgelegt, auch bei einem anderen CAR-Fenster.\n- Jahr und Quartal beziehen sich auf das Veröffentlichungsdatum, nicht auf das Geschäftsjahr.\n- Bereits winsorisiert: {winsor_text}. Nicht ein zweites Mal winsorisieren.\n- Nur für das gewählte Modell vollständige Ereignisse werden exportiert. Nicht gewählte Einflussgrößen können bei anderen Datenbeständen fehlen; leere Zellen bedeuten fehlende Werte, nicht null.\n- Einstellungen, CSV-Prüfsumme und Vollständigkeit je Variable stehen in Jamovi_Export.json.\n\nDie gewöhnliche jamovi-Regression verwendet klassische Standardfehler. Die Python-Auswertung nutzt gemäß diesem Lauf **{cfg['covariance']}**.\nGleiche Koeffizienten bedeuten deshalb nicht automatisch gleiche p-Werte. Datumscluster und die vollständigen Robustheitsprüfungen sind weiterhin im Python-Bericht dokumentiert.\n", encoding='utf-8')
    speichern(pfad(out, 'Jamovi_Export.json'), {'format_version': 2, 'created_at': zeit(), 'rows': len(frame), 'unique_event_ids': int(ids.nunique()), 'columns': list(frame), 'missing_per_column': {name: int(frame[name].isna().sum()) for name in frame}, 'csv_sha256': pruefsumme(pfad(out, 'Jamovi_Daten.csv')), 'tabellen_csv': {'datei': 'Uebersichtliche_Daten.csv', 'trennzeichen': ';', 'dezimalzeichen': ',', 'encoding': 'utf-8-sig', 'sha256': pruefsumme(pfad(out, 'Uebersichtliche_Daten.csv'))}, 'config': cfg})
    return frame
