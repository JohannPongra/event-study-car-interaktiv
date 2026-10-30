"""berechnung · handelsvolumen – klar abgegrenzter Projektbaustein."""
import numpy as np

def handelsvolumen(volume, index):
    """Formeln 8–11: SAV[-60,-10], VOL[0,+1], PREVOL[-3,-1]."""
    if index - 60 < 0 or index + 1 >= len(volume):
        return {'vol': np.nan, 'prevol': np.nan, 'volume_log_mean': np.nan, 'volume_log_std': np.nan}
    logvolume = np.log(volume.where(volume > 0))
    baseline = logvolume.iloc[index - 60:index - 9]
    event, pre = (logvolume.iloc[index:index + 2], logvolume.iloc[index - 3:index])
    mu = float(baseline.mean()) if baseline.notna().sum() == 51 else np.nan
    sigma = float(baseline.std(ddof=1)) if baseline.notna().sum() == 51 else np.nan
    valid = np.isfinite(sigma) and sigma > 0
    return {'volume_log_mean': mu, 'volume_log_std': sigma, 'vol': float(((event - mu) / sigma).mean()) if valid and event.notna().all() else np.nan, 'prevol': float(((pre - mu) / sigma).mean()) if valid and pre.notna().all() else np.nan}
