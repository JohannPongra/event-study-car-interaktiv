from Programm.sentiment.kontext.methoden import METHODEN
from Programm.grundlagen.pfade import pfad
import itertools
import numpy as np
import matplotlib.pyplot as plt

def vergleichsgrafiken(out, data, coefs):
    fig, axes = plt.subplots(1, 3, figsize=(13, 4), constrained_layout=True)
    low, high = (data[list(METHODEN)].min().min(), data[list(METHODEN)].max().max())
    margin = max(0.02, 0.05 * (high - low))
    limits = (max(-1.0, low - margin), min(1.0, high + margin))
    for ax, (left, right) in zip(axes, itertools.combinations(METHODEN, 2)):
        ax.scatter(data[left], data[right], s=18, alpha=0.6, color='#257a69')
        ax.plot(limits, limits, color='#777777', linestyle='--', linewidth=0.8)
        ax.set(xlabel=METHODEN[left], ylabel=METHODEN[right], xlim=limits, ylim=limits)
        ax.set_aspect('equal')
        ax.grid(alpha=0.15)
    fig.savefig(pfad(out, 'Tonwerte_Vergleich.png'), dpi=180)
    fig.savefig(pfad(out, 'Tonwerte_Vergleich.pdf'))
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), constrained_layout=True)
    for ax, outcome in zip(axes, ['car', 'abs_car']):
        part = coefs.loc[coefs.model.eq('Vollmodell') & coefs.outcome.eq(outcome)].set_index('sentiment_method').loc[list(METHODEN)]
        estimates = part.effect_one_tone_sd.to_numpy() * 100
        intervals = np.vstack([estimates - part.ci_lower_one_tone_sd.to_numpy() * 100, part.ci_upper_one_tone_sd.to_numpy() * 100 - estimates])
        ax.errorbar(estimates, np.arange(3), xerr=intervals, fmt='o', color='#257a69', capsize=4)
        ax.set_yticks(np.arange(3), list(METHODEN.values()))
        ax.invert_yaxis()
        ax.axvline(0, color='#777777', linewidth=0.8)
        ax.set(title=outcome.upper(), xlabel='Effekt je 1 SD TONE (Prozentpunkte)')
        ax.grid(axis='x', alpha=0.15)
    fig.savefig(pfad(out, 'TONE_Effekte.png'), dpi=180)
    fig.savefig(pfad(out, 'TONE_Effekte.pdf'))
    plt.close(fig)
