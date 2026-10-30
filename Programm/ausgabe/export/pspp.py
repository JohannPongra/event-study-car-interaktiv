from Programm.grundlagen.pfade import pfad
from Programm.ausgabe.formatierung import renditeeinheit
import pandas as pd
from Programm.grundlagen.tabellen import schreiben
from Programm.berechnung.tonalitaet import tondefinition

def pspp_export(result, out, cfg):
    base = ['event_id', 'ticker', 'reported_date', 'event_trading_day', 'year', 'quarter', 'car', 'abs_car', 'ue', 'sue', 'sue_raw', 'vol', 'prevol', 'tone', 'search', 'search_raw', 'abs_sue']
    frame = result['data'].reindex(columns=base).copy()
    if cfg['fixed_effects']:
        for name in ['ticker', 'year', 'quarter']:
            frame = pd.concat([frame, pd.get_dummies(frame[name].astype(str), prefix='fe_' + name, drop_first=True, dtype=int)], axis=1)
    schreiben(frame, pfad(out, 'PSPP_Daten.csv'))
    formats = {'event_id': 'A80', 'ticker': 'A16', 'reported_date': 'A10', 'event_trading_day': 'A10'}
    variables = '\n'.join((' ' + col + ' ' + formats.get(col, 'F40.0') for col in frame))
    input_file = 'PSPP_Daten.csv'
    output_file = 'PSPP_Daten.sav'
    predictor_names = cfg['predictors'] + [col for col in frame if col.startswith('fe_')]
    display_variables = [col for col in frame if col not in formats and col not in ['year', 'quarter'] and (not col.startswith('fe_'))]
    syntax = f"""* Von python -m Programm berechnen erzeugt. Arbeitsverzeichnis auf diesen Ergebnisordner setzen.\nSET DECIMAL=DOT.\nGET DATA /TYPE=TXT\n /FILE='{input_file}'\n /ENCODING='UTF-8'\n /ARRANGEMENT=DELIMITED /DELCASE=LINE\n /DELIMITERS=',' /QUALIFIER='"' /FIRSTCASE=2\n /VARIABLES=\n{variables}.\nFORMATS {' '.join(display_variables)} (F20.10).\nEXECUTE.\nSAVE OUTFILE='{output_file}'.\n"""
    for outcome in ['car', 'abs_car']:
        from Programm.grundlagen.konfiguration import modell_predictors
        predictor_names = modell_predictors(cfg, outcome) + [col for col in frame if col.startswith('fe_')]
        syntax += f"\nREGRESSION /VARIABLES={outcome} {' '.join(predictor_names)}\n /DEPENDENT={outcome}\n /STATISTICS=COEFF R ANOVA CI(95).\n"
    syntax += '\n* PSPP-Standardregression verwendet klassische Standardfehler.\n* HC3/Datumscluster und Robustheitsanalysen stammen aus python -m Programm regression.\n'
    pfad(out, 'PSPP_Import.sps').write_text(syntax, encoding='utf-8')
    descriptions = {'car': 'Kumulative abnormale Rendite', 'abs_car': 'Betrag der CAR', 'ue': 'EPS tatsächlich minus erwartet', 'sue': 'UE / SD der acht vorherigen UE', 'vol': 'Mittlere SAV an [0,+1]', 'prevol': 'Mittlere SAV an [-3,-1]', 'tone': tondefinition(cfg), 'search': 'ln(SVI Ereigniswoche / Median acht Vorwochen)', 'sue_raw': 'SUE vor Winsorisierung', 'search_raw': 'SEARCH vor Winsorisierung', 'abs_sue': 'Betrag SUE'}
    units = {'car': f'Dezimalrendite (0,01 = 1 {renditeeinheit(cfg, singular=True)})', 'abs_car': 'Dezimalrendite', 'ue': 'EPS-Einheit der Quelle', 'tone': '[-1,+1]'}
    codebook = pd.DataFrame([{'variable': col, 'description': descriptions.get(col, 'Festes Effekt-Dummy' if col.startswith('fe_') else col), 'unit': units.get(col, 'dimensionslos / Kennung'), 'missing': 'leere CSV-Zelle / SQL NULL'} for col in frame])
    schreiben(codebook, pfad(out, 'Variablenverzeichnis.csv'))
