from Programm.ausgabe.grafiken.speichern import speichern_grafik
from Programm.grundlagen.pfade import pfad
from Programm.ausgabe.formatierung import renditeeinheit
from Programm.ausgabe.formatierung import GRUEN
from Programm.ausgabe.formatierung import label
import math
from Programm.grundlagen.konfiguration import modell_predictors
import numpy as np
import matplotlib.pyplot as plt
from Programm.ausgabe.formatierung import pwert
from Programm.ausgabe.formatierung import zahl

def partielle_zusammenhaenge(out, data, coefficients, models, cfg, variants, outcome, title):
    predictors = modell_predictors(cfg, outcome)
    ordinary, robust, x = models[outcome]
    selected = coefficients.loc[coefficients.model.eq('Vollmodell') & coefficients.outcome.eq(outcome) & coefficients.variable.isin(predictors)].set_index('variable').loc[predictors]
    cols = min(2, len(predictors))
    rows = math.ceil(len(predictors) / cols)
    fig, axes = plt.subplots(rows, cols, figsize=(11, rows * 3.6 + 0.7), squeeze=False)
    for ax, variable in zip(axes.flat, predictors):
        other = x.drop(columns=variable).to_numpy()
        raw = x[variable].to_numpy()
        residual_x = raw - other @ np.linalg.lstsq(other, raw, rcond=None)[0]
        y = data[outcome].to_numpy()
        residual_y = y - other @ np.linalg.lstsq(other, y, rcond=None)[0]
        for ticker in sorted(data.ticker.unique()):
            mask = data.ticker.eq(ticker).to_numpy()
            ax.scatter(residual_x[mask], residual_y[mask] * 100, s=23, alpha=0.65, label=ticker, edgecolors='none')
        line = np.linspace(residual_x.min(), residual_x.max(), 100)
        c = selected.loc[variable]
        low, high = (c.ci_lower * line * 100, c.ci_upper * line * 100)
        ax.plot(line, c.coefficient * line * 100, color=GRUEN, lw=2)
        ax.fill_between(line, np.minimum(low, high), np.maximum(low, high), color=GRUEN, alpha=0.13)
        ax.axhline(0, color='#999999', lw=0.7)
        ax.set(xlabel=label(variable) + ' (bereinigt)', ylabel=outcome.upper() + f' (bereinigt, {renditeeinheit(cfg)})', title=f"β = {zahl(c.coefficient)} · p {('' if c.p < 0.0001 else '= ')}{pwert(c.p)}")
    for ax in list(axes.flat)[len(predictors):]:
        ax.set_visible(False)
    axes.flat[0].legend(fontsize=8, ncol=3, frameon=False)
    fig.suptitle(f"{title}\nn = {len(data)} · R² = {zahl(ordinary.rsquared, 3)} · korr. R² = {zahl(ordinary.rsquared_adj, 3)} · {cfg['covariance']}", fontsize=13)
    speichern_grafik(fig, pfad(out, outcome + '_partiell'))
