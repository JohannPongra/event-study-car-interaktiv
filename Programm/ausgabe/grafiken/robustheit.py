from Programm.ausgabe.grafiken.speichern import speichern_grafik
from Programm.grundlagen.pfade import pfad
from Programm.ausgabe.formatierung import GOLD
from Programm.ausgabe.formatierung import GRUEN
from Programm.ausgabe.formatierung import label
import math
from Programm.grundlagen.konfiguration import modell_predictors
import numpy as np
import matplotlib.pyplot as plt

def robustheit(out, data, coefficients, models, cfg, variants, outcome, title):
    predictors = modell_predictors(cfg, outcome)
    ordinary, robust, x = models[outcome]
    selected = coefficients.loc[coefficients.model.eq('Vollmodell') & coefficients.outcome.eq(outcome) & coefficients.variable.isin(predictors)].set_index('variable').loc[predictors]
    cols = min(2, len(predictors))
    rows = math.ceil(len(predictors) / cols)
    for covariance in ['HC3', 'cluster']:
        if variants.empty:
            continue
        frame = variants.loc[variants.model.str.startswith('Unternehmen: ') & variants.outcome.eq(outcome) & variants.covariance.eq(covariance)]
        if frame.empty:
            continue
        fig, axes = plt.subplots(rows, cols, figsize=(12, rows * 3.3 + 0.5), squeeze=False)
        for ax, variable in zip(axes.flat, predictors):
            part = frame.loc[frame.variable.eq(variable)]
            ax.errorbar(part.coefficient, np.arange(len(part)), xerr=[part.coefficient - part.ci_lower, part.ci_upper - part.coefficient], fmt='o', capsize=3, color=GRUEN)
            ax.axvline(0, color=GOLD)
            names = part.model.str.removeprefix('Unternehmen: ').replace({'alle': 'Alle Unternehmen'})
            ax.set(yticks=np.arange(len(part)), yticklabels=names, title=label(variable), xlabel='Koeffizient mit 95%-Intervall')
            ax.invert_yaxis()
        for ax in list(axes.flat)[len(predictors):]:
            ax.set_visible(False)
        fig.suptitle(outcome.upper() + ' · Empfindlichkeit gegenüber der Unternehmensauswahl · ' + covariance, fontsize=13)
        speichern_grafik(fig, pfad(out, f'{outcome}_unternehmen_{covariance}'))
