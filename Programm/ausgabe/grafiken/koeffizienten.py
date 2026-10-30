from Programm.ausgabe.grafiken.speichern import speichern_grafik
from Programm.grundlagen.pfade import pfad
from Programm.ausgabe.formatierung import renditeeinheit
from Programm.ausgabe.formatierung import GOLD
from Programm.ausgabe.formatierung import GRUEN
from Programm.ausgabe.formatierung import label
from Programm.grundlagen.konfiguration import modell_predictors
import numpy as np
import matplotlib.pyplot as plt

def koeffizienten(out, data, coefficients, models, cfg, variants, outcome, title):
    predictors = modell_predictors(cfg, outcome)
    ordinary, robust, x = models[outcome]
    selected = coefficients.loc[coefficients.model.eq('Vollmodell') & coefficients.outcome.eq(outcome) & coefficients.variable.isin(predictors)].set_index('variable').loc[predictors]
    scale = data[predictors].std(ddof=1) * 100
    b, lo, hi = (selected.coefficient * scale, selected.ci_lower * scale, selected.ci_upper * scale)
    fig, ax = plt.subplots(figsize=(10, 3 + len(predictors) * 0.38))
    pos = np.arange(len(selected))
    ax.errorbar(b, pos, xerr=np.vstack([b - lo, hi - b]), fmt='o', capsize=4, color=GRUEN)
    ax.axvline(0, color=GOLD)
    ax.set(yticks=pos, yticklabels=[label(p) for p in predictors], xlabel=f'Zusammenhang je zusätzlicher Standardabweichung ({renditeeinheit(cfg)})', title=title + '\nPunktschätzung und 95%-Konfidenzintervall')
    ax.invert_yaxis()
    speichern_grafik(fig, pfad(out, outcome + '_koeffizienten'))
