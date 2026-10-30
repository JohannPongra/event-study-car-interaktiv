"""statistik · koeffizienten – klar abgegrenzter Projektbaustein."""

def koeffizienten(robust, x, model, outcome, data, cfg):
    interval = robust.conf_int(alpha=0.05)
    return [{'model': model, 'outcome': outcome, 'variable': col, 'coefficient': robust.params[i], 'standard_error': robust.bse[i], 't': robust.tvalues[i], 'p': robust.pvalues[i], 'ci_lower': interval[i, 0], 'ci_upper': interval[i, 1], 'n': len(data), 'clusters': data.event_trading_day.nunique(), 'covariance': cfg['covariance']} for i, col in enumerate(x.columns)]
