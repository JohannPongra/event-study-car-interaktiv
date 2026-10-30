"""statistik · ereignistests – klar abgegrenzter Projektbaustein."""
from statsmodels.regression.linear_model import OLS
import numpy as np
import pandas as pd

def mittelwert_test(values, groups, label):
    """AAR/CAAR gegen Null; CR1 nach Datum mit G-1 Freiheitsgraden."""
    if len(values) < 3 or pd.Series(groups).nunique() < 2:
        return {'statistic': label, 'n': len(values), 'mean': np.mean(values), 'p': np.nan, 'note': 'Zu wenige Beobachtungen/Cluster'}
    result = OLS(np.asarray(values, dtype=float), np.ones((len(values), 1))).fit().get_robustcov_results(cov_type='cluster', groups=np.asarray(groups), use_correction=True, df_correction=True, use_t=True)
    low, high = result.conf_int()[0]
    return {'statistic': label, 'n': len(values), 'clusters': pd.Series(groups).nunique(), 'mean': result.params[0], 'standard_error': result.bse[0], 't': result.tvalues[0], 'p': result.pvalues[0], 'ci_lower': low, 'ci_upper': high, 'note': 'CR1 nach Ereignishandelstag'}

def event_study(data, daily):
    daily = daily.loc[daily.event_id.isin(data.event_id)].copy()
    daily.sort_values(['event_id', 'relative_day'], inplace=True)
    daily['cumulative_ar'] = daily.groupby('event_id').ar.cumsum()
    rows = [mittelwert_test(data.car, data.event_trading_day, 'CAAR gesamtes Ereignisfenster')]
    for day, part in daily.groupby('relative_day'):
        rows.append(mittelwert_test(part.ar, part.event_trading_day, f'AAR Tag {day:+d}'))
        rows.append(mittelwert_test(part.cumulative_ar, part.event_trading_day, f'CAAR bis Tag {day:+d}'))
    return (pd.DataFrame(rows), daily)
