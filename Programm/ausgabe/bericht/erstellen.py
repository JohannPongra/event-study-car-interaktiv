"""ausgabe · bericht · erstellen – klar abgegrenzter Projektbaustein."""
from Programm.ausgabe.bericht.vorlagen import vorlage_fuellen
from pathlib import Path
from Programm.ausgabe.bericht.verweise import bericht_speichern
from Programm.grundlagen.pfade import pfad
from Programm.ausgabe.formatierung import ZIELE, renditeeinheit
import html
from Programm.ausgabe.bericht.tabellen import koeffiziententabelle
from Programm.ausgabe.formatierung import label
from Programm.grundlagen.konfiguration import modell_predictors
from Programm.ausgabe.formatierung import pwert
from Programm.ausgabe.bericht.tabellen import tabelle
from Programm.ausgabe.formatierung import zahl
from Programm.grundlagen.laufkennungen import zeit

def grafik(out, name, caption):
    if not pfad(out, name + '.png').exists():
        return ''
    return f'<figure><img src="{name}.png" alt="{html.escape(caption)}"><figcaption><span>{html.escape(caption)}</span><a href="{name}.pdf" target="_blank" rel="noreferrer">PDF öffnen ↗</a></figcaption></figure>'

def bericht(out, coefficients, diagnostics, study, variants, errors, loo_summary, wild, cfg, warnings_list, data, events):
    einheit = renditeeinheit(cfg)
    rendite_hinweis = ('Logarithmische Tagesrenditen; CAR × 100 ist in logarithmischen Prozentpunkten angegeben.' if cfg['return_type'] == 'log' else 'Einfache Tagesrenditen: r_t = P_t / P_(t−1) − 1. CAR = Summe der täglichen abnormalen Renditen; CAR × 100 ist in Prozentpunkten angegeben. Es wird nicht aufgezinst.')
    esc = html.escape
    sections = []
    for outcome, title in ZIELE.items():
        predictors = modell_predictors(cfg, outcome)
        d = diagnostics.loc[diagnostics.outcome.eq(outcome)].iloc[0]
        main = coefficients.loc[coefficients.model.eq('Vollmodell') & coefficients.outcome.eq(outcome) & coefficients.variable.isin(predictors)]
        cards = [('Ereignisse im Modell', str(len(data)), f'{len(events) - len(data)} nicht in der Regression'), ('Unternehmen', str(data.ticker.nunique()), f'{data.event_trading_day.nunique()} Ereignishandelstage'), ('Erklärte Streuung · R²', zahl(d.r_squared * 100, 1) + ' %', 'Anpassung in dieser Stichprobe'), ('Korrigiertes R²', zahl(d.adjusted_r_squared * 100, 1) + ' %', 'Berücksichtigt die Modellgröße')]
        kpis = ''.join((f'<div><span>{a}</span><strong>{b}</strong><small>{c}</small></div>' for a, b, c in cards))
        se = 'Nach Ereignishandelstag gruppierte Standardfehler (CR1).' if cfg['covariance'] == 'cluster' else 'Heteroskedastizitätsrobuste Standardfehler (HC3).'
        controls = 'Unternehmen, Jahr und Kalenderquartal werden als Kategorien berücksichtigt.' if cfg['fixed_effects'] else 'Dieser Lauf enthält keine zusätzlichen Kategorienkontrollen.'
        singles = []
        for variable in predictors:
            part = coefficients.loc[coefficients.model.eq('Einzelmodell ' + variable) & coefficients.outcome.eq(outcome) & coefficients.variable.eq(variable)]
            singles.append(f'<details><summary>{esc(label(variable))} · Einzelregression</summary>{koeffiziententabelle(part)}</details>')
        diagnostics_cards = [('RMSE · ' + einheit, zahl(d.rmse * 100, 2)), ('Breusch–Pagan · p', pwert(d.bp_lm_p)), ('Jarque–Bera · p', pwert(d.jb_p)), ('Ereignisse mit Cook > 4/n', str(int(d.cook_flagged)))]
        diag_html = ''.join((f'<div><strong>{esc(b)}</strong><span>{a}</span></div>' for a, b in diagnostics_cards))
        hidden = ' hidden' if outcome != 'car' else ''
        sections.append(f'''<section id="{outcome}" class="outcome" role="tabpanel" aria-labelledby="tab-{outcome}"{hidden}>\n<div class="kpis">{kpis}</div><article><span class="eyebrow">GEMEINSAMES MODELL · {outcome.upper()}</span><h2>{title}</h2>\n<p>{se} Koeffizienten je Einheit der Einflussgröße. CAR ist als Dezimalrendite gespeichert. {rendite_hinweis}</p>\n<p class="muted">{controls} Die Tabelle zeigt die ausgewählten Einflussgrößen.</p>{koeffiziententabelle(main)}\n{grafik(out, outcome + '_partiell', 'Partielle Zusammenhänge im gemeinsamen Modell')}\n<p class="muted">Partielle Regression: übrige Modellvariablen herausgerechnet. Schattierung: punktweises 95%-Intervall der Steigung, kein Vorhersageintervall. Keine Kausalinterpretation.</p>\n{grafik(out, outcome + '_koeffizienten', 'Vergleich der Einflussgrößen je Standardabweichung')}\n{grafik(out, outcome + '_diagnostik', 'Residuen, Verteilung und Einfluss einzelner Ereignisse')}\n<div class="diagnostic-grid">{diag_html}</div><p class="muted">Cook-Distanz über 4/n kennzeichnet Prüfbedarf, keinen automatischen Ausschluss. Diagnose-p-Werte sind kein alleiniger Maßstab für die Modellqualität.</p></article>\n<article><h2>Einzelne Zusammenhänge</h2><p>Diese Modelle betrachten jeweils eine Einflussgröße. {controls} Die jeweils anderen Einflussgrößen werden hier nicht berücksichtigt.</p>{''.join(singles)}</article></section>''')
    robustness = ''
    for outcome in ZIELE:
        for covariance in ['HC3', 'cluster']:
            robustness += grafik(out, f'{outcome}_unternehmen_{covariance}', f'{outcome.upper()} · Unternehmensauswahl · {covariance}')
    variant_details = ''
    if not variants.empty:
        for (model, outcome, covariance), frame in variants.groupby(['model', 'outcome', 'covariance'], sort=False):
            part = frame.loc[frame.variable.isin(cfg['predictors'] + ['abs_sue'])]
            variant_details += f'<details><summary>{esc(outcome.upper())} · {esc(model)} · {esc(covariance)} · n = {int(frame.n.iloc[0])}</summary>{koeffiziententabelle(part)}</details>'
    renamed_study = study.rename(columns={'statistic': 'Kennzahl', 'n': 'Ereignisse', 'clusters': 'Datumsgruppen', 'mean': 'Mittelwert', 'standard_error': 'Standardfehler', 'p': 'p-Wert', 'ci_lower': '95% unten', 'ci_upper': '95% oben', 'note': 'Hinweis'})
    loo_table = loo_summary.copy()
    if 'variable' in loo_table:
        loo_table['variable'] = loo_table.variable.map(label)
    loo_table = loo_table.rename(columns={'variable': 'Einflussgröße', 'coefficient_min': 'Koeffizient min.', 'coefficient_max': 'Koeffizient max.', 'p_min': 'p min.', 'p_max': 'p max.', 'models': 'Modelle'})
    wild_table = wild.copy()
    if 'variable' in wild_table:
        wild_table['variable'] = wild_table.variable.map(label)
    wild_table = wild_table.rename(columns={'variable': 'Einflussgröße', 'wild_p': 'Bootstrap-p', 't_observed': 'Beobachtetes t', 'draws': 'Ziehungen', 'valid_draws': 'Gültige Ziehungen', 'cluster': 'Gruppierung', 'seed': 'Zufallsstartwert'})
    notices = ''.join(('<li>' + esc(w) + '</li>' for w in warnings_list))
    links = {'Übersichtliche CSV · Excel': 'Uebersichtliche_Daten.csv', 'Daten für jamovi': 'Jamovi_Daten.csv', 'Variablen erklärt': 'Jamovi_Anleitung.md', 'Alle Koeffizienten': 'koeffizienten.csv', 'Diagnostik': 'diagnostik.csv', 'Analysedaten vollständig': 'analysedaten.csv', 'Ausschlüsse': 'ausschluesse.csv', 'Kollinearität': 'vif.csv', 'Korrelationsmatrix': 'korrelationen.csv', 'Robustheit vollständig': 'robustheit.csv', 'Unternehmensauswahl': 'unternehmensauswahl.csv', 'Datenbank': 'event_study.sqlite', 'Quellen & Prüfsummen': 'manifest.json'}
    downloads = ''.join((f'<a class="button" href="{v}" download>{k}</a>' for k, v in links.items()))
    css = pfad(pfad(Path(__file__).parent, 'vorlagen'), 'bericht.css').read_text(encoding='utf-8')
    script = pfad(pfad(Path(__file__).parent, 'vorlagen'), 'bericht.js').read_text(encoding='utf-8')
    css += '.embedded main{margin:0;max-width:none;padding:0}.embedded .report-header{display:none}.embedded body{background:transparent}'
    settings = f"{' · '.join(sorted(data.ticker.unique()))} · {cfg['start']} bis {cfg['end']} · {cfg['benchmark']} · Fenster {cfg['window']} · " + ('logarithmische Renditen' if cfg['return_type'] == 'log' else 'einfache Renditen')
    text = vorlage_fuellen('analyse.html', {'inhalt_1': f'{css}', 'inhalt_2': f'{esc(zeit())}', 'inhalt_3': f'{esc(out.name)}', 'inhalt_4': f'{esc(settings)}', 'inhalt_5': f"{''.join(sections)}", 'inhalt_6': f"{grafik(out, 'ueberblick', 'Mittlere Kursreaktion und Korrelationen')}", 'inhalt_7': f'{tabelle(renamed_study)}', 'inhalt_8': f'{robustness}', 'inhalt_9': f"{variant_details or '<p>In diesem Lauf nicht angefordert.</p>'}", 'inhalt_10': f'{tabelle(loo_table)}', 'inhalt_11': f'{tabelle(wild_table)}', 'inhalt_12': f'{len(errors)}', 'inhalt_13': f'{tabelle(errors)}', 'inhalt_14': f'{notices}', 'inhalt_15': f'{downloads}', 'inhalt_16': f'{script}'})
    bericht_speichern(out, text)
