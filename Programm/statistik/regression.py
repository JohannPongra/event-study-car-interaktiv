"""statistik · regression – klar abgegrenzter Projektbaustein."""
from statsmodels.regression.linear_model import OLS
from Programm.statistik.modelldesign import design
from Programm.grundlagen.konfiguration import modell_predictors
import numpy as np

def fit(data, outcome, predictors, cfg):
    predictors = modell_predictors(cfg, outcome, predictors)
    data = data.copy()
    data['abs_sue'] = data.sue.abs()
    x = design(data, predictors, cfg['fixed_effects'])
    y = data[outcome].astype(float)
    if not np.isfinite(x.to_numpy()).all() or not np.isfinite(y.to_numpy()).all():
        raise ValueError('Regressionsstichprobe enthält fehlende/ungültige Werte.')
    if len(data) <= x.shape[1] + 2 or np.linalg.matrix_rank(x) < x.shape[1]:
        raise ValueError('Zu wenige Beobachtungen oder linear abhängige Einflussgrößen/Feste Effekte.')
    ordinary = OLS(y, x).fit()
    if cfg['covariance'] == 'cluster':
        if data.event_trading_day.nunique() < 2:
            raise ValueError('Mindestens zwei Ereignishandelstage für Datumscluster erforderlich.')
        robust = ordinary.get_robustcov_results(cov_type='cluster', groups=data.event_trading_day, use_correction=True, df_correction=True, use_t=True)
    else:
        robust = ordinary.get_robustcov_results(cov_type='HC3', use_t=True)
    return (ordinary, robust, x)
