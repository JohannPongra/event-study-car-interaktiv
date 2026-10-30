"""statistik · auswertung – klar abgegrenzter Projektbaustein."""
from Programm.grundlagen.pfade import schreibziel_pruefen
from Programm.grundlagen.pfade import struktur_vorbereiten
from Programm.grundlagen.pfade import pfad
from Programm.grundlagen.pfade import ERGEBNISSE
from Programm.statistik.robustheit.einzelereignisse import abs_car_zusatz
from Programm.ausgabe.bericht.erstellen import bericht
from Programm.grundlagen.pfade import bestand_ordner
from contextlib import closing
from Programm.statistik.diagnostik import diagnose
from importlib.metadata import distributions
from Programm.grundlagen.konfiguration import einstellungen
from Programm.statistik.ereignistests import event_study
from Programm.statistik.regression import fit
from Programm.ausgabe.grafiken.erstellen import grafiken
from Programm.ausgabe.export.jamovi import jamovi_export
import json
from Programm.grundlagen.laufkennungen import kennung
from Programm.statistik.koeffizienten import koeffizienten
from Programm.grundlagen.tabellen import lesen
import matplotlib
from Programm.grundlagen.konfiguration import modell_predictors
import numpy as np
import pandas as pd
import platform
from Programm.grundlagen.pruefsummen import pruefsumme
from Programm.grundlagen.tabellen import schreiben
import scipy
from Programm.grundlagen.json_dateien import speichern
import sqlite3
import statsmodels
from Programm.statistik.robustheit.modellvarianten import varianten
from Programm.grundlagen.laufkennungen import zeit

def regressieren(werte=None, fortschritt=print):
    cfg = einstellungen(werte)
    folder = bestand_ordner(cfg)
    schreibziel_pruefen(folder)
    calculated = pfad(folder, 'berechnet')
    if not pfad(calculated, 'berechnung.json').exists():
        raise ValueError('Zuerst python -m Programm berechnen ausführen.')
    meta = json.loads(pfad(calculated, 'berechnung.json').read_text(encoding='utf-8'))
    keys = [k for k in cfg if k not in ['robustness', 'abs_car_robustness', 'covariance', 'pause_seconds', 'request_limit', 'download_trends', 'download_transcripts', 'finbert_batch_size']]
    if any((meta['config'].get(key, 'sentence' if key == 'sentiment_method' else None) != cfg[key] for key in keys)):
        raise ValueError('Berechnung gehört zu anderen Einstellungen. Berechnung erneut ausführen.')
    for name, expected in meta['inputs'].items():
        path = pfad(folder, name)
        if not path.exists() or pruefsumme(path) != expected:
            raise ValueError('Eingangsdaten verändert. Berechnung erneut ausführen.')
    if pruefsumme(pfad(calculated, 'data.csv')) != meta['data_sha256'] or pruefsumme(pfad(calculated, 'daily.csv')) != meta['daily_sha256']:
        raise ValueError('Berechnete Tabellen verändert. Berechnung erneut ausführen.')
    if pruefsumme(pfad(calculated, 'events.csv')) != meta['events_sha256']:
        raise ValueError('Ereignistabelle verändert. Berechnung erneut ausführen.')
    data, daily = (lesen(pfad(calculated, 'data.csv')), lesen(pfad(calculated, 'daily.csv')))
    events = lesen(pfad(calculated, 'events.csv'))
    if data.empty:
        raise ValueError('Keine vollständigen Ereignisse für die gewählte Regression.')
    out = pfad(ERGEBNISSE, kennung('analyse'))
    out.mkdir(parents=True)
    struktur_vorbereiten(out)
    models, coefficients, diagnostics, residuals, vifs, errors = ({}, [], [], [], [], [])
    messages = ['Feste Effekte: Unternehmen, Berichtsjahr und Kalenderquartal.' if cfg['fixed_effects'] else 'Keine festen Effekte.', 'Robuste Standardfehler: ' + ('CR1 nach Ereignishandelstag, t-Verteilung mit G−1 Freiheitsgraden.' if cfg['covariance'] == 'cluster' else 'HC3, t-Verteilung mit Residualfreiheitsgraden.'), 'Klassische Einzelereignistests setzen zeitlich unkorrelierte Marktmodellfehler voraus. Überlappende Ereignisfenster können zusätzliche Abhängigkeiten erzeugen.']
    messages.append('CAR mit SUE; ABS_CAR mit |SUE|.' if cfg.get('abs_sue_for_abs_car') else 'Beide Modelle mit vorzeichenbehafteter SUE.')
    messages.append('Ausgangsmodelle ohne Winsorisierung; Robustheit: SUE, VOL und PREVOL 1/99. Zusatzprüfungen explorativ ohne Mehrfachtestkorrektur.' if not cfg['winsorize'] else 'Winsorisierung von SUE, VOL und PREVOL im Ausgangsmodell aktiviert.')
    messages.append('Datumscluster erfassen keine gezielte Abhängigkeit zwischen zeitlich getrennten Berichten desselben Unternehmens.')
    event_sample = events.loc[events.event_study_ready.astype(str).str.lower().isin(['true', '1'])].copy()
    messages.append(f'Event Study: {len(event_sample)} Ereignisse mit gültiger CAR; Regressionen: {len(data)} vollständig beobachtete Ereignisse. Alle Einzel- und Vollregressionen verwenden dieselbe Stichprobe.')
    if data.event_trading_day.nunique() < 20:
        messages.append('Weniger als 20 Ereignisdatumscluster: Cluster-Inferenz vorsichtig interpretieren.')
    for name in ['sue_source', 'search_source', 'tone_source']:
        if name in data:
            messages.append(name + ': ' + ', '.join(sorted(data[name].dropna().unique())))
    if 'report_time_verified' in data:
        unverified = ~data.report_time_verified.astype(str).str.lower().isin(['true', '1'])
        messages.append(f'Veröffentlichungszeiten ohne unabhängig belegte Prüfung: {int(unverified.sum())} von {len(data)}.')
    for outcome in ['car', 'abs_car']:
        predictors = modell_predictors(cfg, outcome)
        fortschritt(outcome.upper() + ': Vollmodell und Einzelmodelle …')
        ordinary, robust, x = fit(data, outcome, predictors, cfg)
        models[outcome] = (ordinary, robust, x)
        coefficients.extend(koeffizienten(robust, x, 'Vollmodell', outcome, data, cfg))
        info, resid, vif = diagnose(ordinary, x, data, 'Vollmodell', outcome)
        info.update({'robust_f': float(robust.fvalue), 'robust_f_p': float(robust.f_pvalue), 'covariance': cfg['covariance']})
        diagnostics.append(info)
        residuals.append(resid)
        vifs.extend(vif)
        pfad(out, outcome + '_modell.txt').write_text(str(robust.summary()), encoding='utf-8')
        for variable in predictors:
            try:
                _, single, single_x = fit(data, outcome, [variable], cfg)
                coefficients.extend(koeffizienten(single, single_x, 'Einzelmodell ' + variable, outcome, data, cfg))
            except ValueError as exc:
                errors.append({'variant': 'Einzelmodell ' + variable, 'outcome': outcome, 'message': str(exc)})
    coefs, diag = (pd.DataFrame(coefficients), pd.DataFrame(diagnostics))
    study, daily = event_study(event_sample, daily)
    variants, variant_errors = varianten(data, cfg, models, fortschritt)
    error_frame = pd.concat([pd.DataFrame(errors, columns=['variant', 'outcome', 'message']), variant_errors], ignore_index=True)
    loo, wild = (pd.DataFrame(columns=['omitted_event', 'variable', 'coefficient', 'p']), pd.DataFrame(columns=['variable', 'wild_p']))
    if cfg['abs_car_robustness']:
        loo, wild = abs_car_zusatz(data, cfg, fortschritt)
    loo_summary = pd.DataFrame(columns=['variable', 'coefficient_min', 'coefficient_max', 'p_min', 'p_max', 'models'])
    if not loo.empty and 'variable' in loo:
        loo_summary = loo.groupby('variable').agg(coefficient_min=('coefficient', 'min'), coefficient_max=('coefficient', 'max'), p_min=('p', 'min'), p_max=('p', 'max'), models=('coefficient', 'count')).reset_index()
    tables = {'koeffizienten': coefs, 'diagnostik': diag, 'residuen': pd.concat(residuals), 'vif': pd.DataFrame(vifs), 'event_study': study, 'robustheit': variants, 'nicht_schaetzbar': error_frame, 'unternehmensauswahl': variants.loc[variants.model.str.startswith('Unternehmen: ')] if not variants.empty else pd.DataFrame(columns=coefs.columns), 'ABS_CAR_einzelereignisse': loo, 'ABS_CAR_wild_bootstrap': wild, 'ABS_CAR_einzelereignisse_spannweite': loo_summary, 'beschreibung': data[list(dict.fromkeys(['car', 'abs_car', *cfg['predictors'], *modell_predictors(cfg, 'abs_car')]))].describe().T.rename_axis('variable').reset_index(), 'korrelationen': data[list(dict.fromkeys(['car', 'abs_car', *cfg['predictors'], *modell_predictors(cfg, 'abs_car')]))].corr().rename_axis('variable').reset_index()}
    for name, frame in tables.items():
        schreiben(frame, pfad(out, name + '.csv'))
    grafiken(out, data, coefs, models, daily, cfg, variants)
    bericht(out, coefs, diag, study, variants, error_frame, loo_summary, wild, cfg, messages, data, events)
    import shutil
    shutil.copy2(pfad(calculated, 'data.csv'), pfad(out, 'analysedaten.csv'))
    shutil.copy2(pfad(calculated, 'events.csv'), pfad(out, 'alle_ereignisse.csv'))
    shutil.copy2(pfad(calculated, 'exclusions.csv'), pfad(out, 'ausschluesse.csv'))
    for name in ['event_study.sqlite', 'PSPP_Daten.csv', 'Variablenverzeichnis.csv']:
        shutil.copy2(pfad(calculated, name), pfad(out, name))
    jamovi_export(data, out, cfg)
    with closing(sqlite3.connect(pfad(out, 'event_study.sqlite'))) as connection, connection:
        for name, frame in tables.items():
            if len(frame.columns):
                frame.to_sql(name, connection, index=False, if_exists='replace')
        pd.DataFrame([{'key': k, 'value': json.dumps(v, ensure_ascii=False)} for k, v in cfg.items()]).to_sql('regression_settings', connection, index=False, if_exists='replace')
    syntax = pfad(calculated, 'PSPP_Import.sps').read_text(encoding='utf-8')
    syntax = syntax.replace(calculated.resolve().as_posix().replace("'", "''"), out.resolve().as_posix().replace("'", "''"))
    pfad(out, 'PSPP_Import.sps').write_text(syntax, encoding='utf-8')
    from Programm.ausgabe.programmstand import sichern
    sichern(out)
    packages = sorted({d.metadata['Name'] + '==' + d.version for d in distributions() if d.metadata['Name']})
    pfad(out, 'paketversionen.txt').write_text('\n'.join(packages) + '\n', encoding='utf-8')
    speichern(pfad(out, 'manifest.json'), {'created_at': zeit(), 'config': cfg, 'berechnung': meta, 'plattform': platform.platform(), 'python_implementation': platform.python_implementation(), 'hinweise': messages, 'software': {'python': platform.python_version(), 'numpy': np.__version__, 'pandas': pd.__version__, 'scipy': scipy.__version__, 'statsmodels': statsmodels.__version__, 'matplotlib': matplotlib.__version__}, 'dateien': {str(p.relative_to(out)): pruefsumme(p) for p in sorted(out.rglob('*')) if p.is_file()}})
    speichern(pfad(folder, 'letzte_analyse.json'), {'ordner': out.name, 'created_at': zeit(), 'n': len(data)})
    from Programm.ausgabe.verzeichnis import aktualisieren
    aktualisieren()
    fortschritt('Analyse gespeichert: ' + str(out))
    return {'ordner': out.name, 'n': len(data), 'bericht': str(pfad(out, 'bericht.html'))}
