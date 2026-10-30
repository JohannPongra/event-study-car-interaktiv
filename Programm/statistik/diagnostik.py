"""statistik · diagnostik – klar abgegrenzter Projektbaustein."""
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.stattools import jarque_bera
import numpy as np
import pandas as pd
from statsmodels.stats.outliers_influence import variance_inflation_factor

def diagnose(ordinary, x, data, model, outcome):
    bp = het_breuschpagan(ordinary.resid, x)
    jb = jarque_bera(ordinary.resid)
    influence = ordinary.get_influence()
    residuals = pd.DataFrame({'event_id': data.event_id, 'ticker': data.ticker, 'outcome': outcome, 'actual': data[outcome], 'fitted': ordinary.fittedvalues, 'residual': ordinary.resid, 'studentized_residual': influence.resid_studentized_internal, 'leverage': influence.hat_matrix_diag, 'cooks_distance': influence.cooks_distance[0]})
    vif = [{'model': model, 'variable': col, 'vif': variance_inflation_factor(x.to_numpy(), i)} for i, col in enumerate(x.columns) if col != 'const']
    info = {'model': model, 'outcome': outcome, 'n': len(data), 'parameters': x.shape[1], 'r_squared': ordinary.rsquared, 'adjusted_r_squared': ordinary.rsquared_adj, 'rmse': np.sqrt(np.mean(ordinary.resid ** 2)), 'mae': np.mean(abs(ordinary.resid)), 'bp_lm_p': bp[1], 'bp_f_p': bp[3], 'jb_p': jb[1], 'skewness': jb[2], 'kurtosis': jb[3], 'cook_threshold': 4 / len(data), 'cook_flagged': int((influence.cooks_distance[0] > 4 / len(data)).sum())}
    return (info, residuals, vif)
