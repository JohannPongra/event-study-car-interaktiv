"""berechnung · marktmodell – klar abgegrenzter Projektbaustein."""
import numpy as np
from scipy import stats

def marktmodell(stock, market, estimation, event):
    """Formeln 2–4: OLS-Marktmodell, erwartete Rendite, AR und CAR."""
    x = np.column_stack([np.ones(len(estimation)), market.iloc[estimation].to_numpy()])
    y = stock.iloc[estimation].to_numpy()
    future = np.column_stack([np.ones(len(event)), market.iloc[event].to_numpy()])
    actual = stock.iloc[event].to_numpy()
    if not np.isfinite(x).all() or not np.isfinite(y).all() or (not np.isfinite(future).all()) or (not np.isfinite(actual).all()):
        raise ValueError('Lücken oder ungültige Kurse im Schätz-/Ereignisfenster')
    if np.linalg.matrix_rank(x) < 2:
        raise ValueError('Marktrenditen ohne ausreichende Variation')
    alpha, beta = np.linalg.lstsq(x, y, rcond=None)[0]
    expected = future @ np.array([alpha, beta])
    abnormal = actual - expected
    car = float(abnormal.sum())
    residuals = y - x @ np.array([alpha, beta])
    sigma2 = float(residuals @ residuals / (len(y) - 2))
    v = future.sum(axis=0)
    car_se = np.sqrt(sigma2 * (len(event) + v @ np.linalg.inv(x.T @ x) @ v))
    statistic = car / car_se if car_se > 0 else np.nan
    pvalue = float(2 * stats.t.sf(abs(statistic), len(y) - 2))
    return ({'alpha': alpha, 'beta': beta, 'car': car, 'abs_car': abs(car), 'car_se_classic': car_se, 'car_t_classic': statistic, 'car_p_classic': pvalue, 'estimation_n': len(y), 'sigma_estimation': np.sqrt(sigma2)}, expected, abnormal)
