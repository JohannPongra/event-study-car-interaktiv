from statsmodels.regression.linear_model import OLS
from Programm.statistik.regression import fit
import numpy as np
import pandas as pd

def wild_bootstrap(data, cfg, predictors):
    bootstrap = []
    if data.event_trading_day.nunique() < 2:
        return pd.DataFrame([{'note': 'Wild-Cluster-Bootstrap: mindestens zwei Ereignisdatumscluster erforderlich'}])
    _, observed, x = fit(data, 'abs_car', predictors, {**cfg, 'covariance': 'cluster'})
    codes = pd.factorize(data.event_trading_day)[0]
    draws = np.random.default_rng(20261002).choice([-1, 1], size=(999, len(np.unique(codes))))
    for variable in predictors:
        restricted_x = x.drop(columns=variable)
        restricted = OLS(data.abs_car, restricted_x).fit()
        j = x.columns.get_loc(variable)
        statistics = []
        for draw in draws:
            y_star = restricted.fittedvalues.to_numpy() + restricted.resid.to_numpy() * draw[codes]
            result = OLS(y_star, x).fit().get_robustcov_results(cov_type='cluster', groups=data.event_trading_day, use_correction=True, df_correction=True, use_t=True)
            statistics.append(result.tvalues[j])
        valid = np.asarray(statistics)[np.isfinite(statistics)]
        bootstrap.append({'variable': variable, 't_observed': observed.tvalues[j], 'draws': len(draws), 'valid_draws': len(valid), 'wild_p': (1 + np.sum(abs(valid) >= abs(observed.tvalues[j]))) / (1 + len(valid)) if len(valid) and np.isfinite(observed.tvalues[j]) else np.nan, 'cluster': 'event_trading_day', 'seed': 20261002})
    return pd.DataFrame(bootstrap)
