from Programm.ausgabe.bericht.vorlagen import vorlage_fuellen
import os
from Programm.sentiment.kontext.methoden import METHODEN
from Programm.grundlagen.pfade import pfad
from Programm.grundlagen.pfade import ERGEBNISSE
import html
import numpy as np

def vergleichsbericht(out, data, corr, coefs, distribution, results):
    summary = data[list(METHODEN)].describe().T[['count', 'mean', 'std', 'min', '50%', 'max']]
    summary.index = summary.index.map(METHODEN)
    summary.columns = ['N', 'Mittelwert', 'Standardabweichung', 'Minimum', 'Median', 'Maximum']
    summary['N'] = summary.N.astype(int)
    corr_display = corr.replace({'left': METHODEN, 'right': METHODEN}).rename(columns={'left': 'Verfahren 1', 'right': 'Verfahren 2', 'n': 'N', 'pearson': 'Pearson', 'spearman': 'Spearman', 'mean_difference_right_minus_left': 'Mittlere Differenz (2−1)', 'mean_absolute_difference': 'Mittlerer absoluter Unterschied'})
    full = coefs.loc[coefs.model.eq('Vollmodell')].copy()
    full['sentiment_method'] = full.sentiment_method.map(METHODEN)
    full = full[['sentiment_method', 'outcome', 'coefficient', 'standard_error', 'p', 'ci_lower', 'ci_upper', 'effect_one_tone_sd', 'n']].rename(columns={'sentiment_method': 'Verfahren', 'outcome': 'Zielgröße', 'coefficient': 'TONE-Koeffizient', 'standard_error': 'Standardfehler', 'p': 'p-Wert', 'ci_lower': '95%-KI unten', 'ci_upper': '95%-KI oben', 'effect_one_tone_sd': 'Effekt je 1 SD TONE', 'n': 'N'})
    format_number = lambda value: f'{value:.5f}'.replace('.', ',') if np.isfinite(value) else '–'
    table = lambda frame, index=False: frame.to_html(index=index, border=0, float_format=format_number, escape=True)
    label_display = distribution[['sentiment_method', 'n_units', 'n_sentences']].copy()
    label_display['sentiment_method'] = label_display.sentiment_method.map(METHODEN)
    for label, title in [('positive', 'Positive Einheiten (%)'), ('neutral', 'Neutrale Einheiten (%)'), ('negative', 'Negative Einheiten (%)')]:
        label_display[title] = 100 * distribution[f'n_{label}_units'] / distribution.n_units
    label_display = label_display.rename(columns={'sentiment_method': 'Verfahren', 'n_units': 'Bewertete Einheiten', 'n_sentences': 'Erfasste Sätze'})
    label_table = label_display.to_html(index=False, border=0, float_format=lambda value: f'{value:.2f}'.replace('.', ','), escape=True)
    links = ''.join(('<li><a href="' + html.escape(os.path.relpath(pfad(ERGEBNISSE, r['ordner'], 'bericht.html'), out).replace(os.sep, '/'), quote=True) + '">' + html.escape(METHODEN[m]) + ': vollständiger Bericht</a></li>' for m, r in results.items()))
    body = vorlage_fuellen('sentimentvergleich.html', {'inhalt_1': f'{len(data)}', 'inhalt_2': f'{data.ticker.nunique()}', 'inhalt_3': f'{table(summary, True)}', 'inhalt_4': f'{label_table}', 'inhalt_5': f'{table(corr_display)}', 'inhalt_6': f'{table(full)}', 'inhalt_7': f'{links}'})
    pfad(out, 'bericht.html').write_text(body, encoding='utf-8')
