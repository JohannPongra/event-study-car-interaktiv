from Programm.sentiment.kontext.methoden import METHODEN
import itertools
import pandas as pd

def vergleichskennzahlen(data, coefficients):
    correlations = []
    for left, right in itertools.combinations(METHODEN, 2):
        correlations.append({'left': left, 'right': right, 'n': len(data), 'pearson': data[left].corr(data[right]), 'spearman': data[left].rank(method='average').corr(data[right].rank(method='average')), 'mean_difference_right_minus_left': (data[right] - data[left]).mean(), 'mean_absolute_difference': (data[right] - data[left]).abs().mean()})
    corr = pd.DataFrame(correlations)
    coefs = pd.concat(coefficients, ignore_index=True)
    deviations = data[list(METHODEN)].std(ddof=1).to_dict()
    coefs['tone_sd'] = coefs.sentiment_method.map(deviations)
    for source, target in [('coefficient', 'effect_one_tone_sd'), ('ci_lower', 'ci_lower_one_tone_sd'), ('ci_upper', 'ci_upper_one_tone_sd')]:
        coefs[target] = coefs[source] * coefs.tone_sd
    return (corr, coefs)
