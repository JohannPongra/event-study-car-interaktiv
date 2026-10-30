from Programm.ausgabe.grafiken.speichern import speichern_grafik
from Programm.grundlagen.pfade import pfad
from Programm.ausgabe.formatierung import renditeeinheit
from Programm.ausgabe.formatierung import GOLD
from Programm.ausgabe.formatierung import GRUEN
from Programm.grundlagen.konfiguration import modell_predictors
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

def diagnostik(out, data, coefficients, models, cfg, variants, outcome, title):
    predictors = modell_predictors(cfg, outcome)
    ordinary, robust, x = models[outcome]
    selected = coefficients.loc[coefficients.model.eq('Vollmodell') & coefficients.outcome.eq(outcome) & coefficients.variable.isin(predictors)].set_index('variable').loc[predictors]
    res, fitted = (np.asarray(ordinary.resid) * 100, np.asarray(ordinary.fittedvalues) * 100)
    cooks = ordinary.get_influence().cooks_distance[0]
    order = data.reset_index(drop=True).sort_values(['event_trading_day', 'event_id']).index.to_numpy()
    fig, axes = plt.subplots(2, 2, figsize=(11, 7.5))
    axes[0, 0].scatter(fitted, res, s=19, alpha=0.65, color=GRUEN)
    axes[0, 0].axhline(0, color=GOLD)
    axes[0, 0].set(xlabel='Geschätzte ' + outcome.upper() + f' ({renditeeinheit(cfg)})', ylabel=f'Residuum ({renditeeinheit(cfg)})', title='Residuen und Modellwerte')
    (theory, ordered), (slope, intercept, _) = stats.probplot(res, dist='norm')
    axes[0, 1].scatter(theory, ordered, s=17, color=GRUEN)
    axes[0, 1].plot(theory, slope * theory + intercept, color=GOLD)
    axes[0, 1].set(xlabel='Theoretische Normalquantile', ylabel=f'Geordnete Residuen ({renditeeinheit(cfg)})', title='Normal-Quantil-Diagramm')
    marker, stems, _ = axes[1, 0].stem(np.arange(1, len(res) + 1), cooks[order], basefmt=' ')
    plt.setp(marker, color=GRUEN, markersize=3)
    plt.setp(stems, color=GRUEN)
    axes[1, 0].axhline(4 / len(res), color=GOLD, ls='--', label='4/n')
    axes[1, 0].set(xlabel='Ereignis (nach Datum sortiert)', ylabel='Cook-Distanz', title='Einfluss einzelner Ereignisse')
    axes[1, 0].legend(frameon=False)
    axes[1, 1].hist(res, bins='auto', color=GRUEN, alpha=0.85)
    axes[1, 1].set(xlabel=f'Residuum ({renditeeinheit(cfg)})', ylabel='Anzahl', title='Verteilung der Residuen')
    fig.suptitle(title + ' · Modelldiagnostik', fontsize=13)
    speichern_grafik(fig, pfad(out, outcome + '_diagnostik'))
