"""berechnung · gewinnueberraschung – klar abgegrenzter Projektbaustein."""

def gewinnueberraschungen(history):
    """Formeln 5–7: UE und SUE mit genau den acht vorherigen Berichten."""
    history = history.sort_values(['ticker', 'reported_date']).copy()
    history['ue'] = history.reported_eps - history.estimated_eps
    grouped = history.groupby('ticker')['ue']
    history['sue_history_std'] = grouped.transform(lambda s: s.shift(1).rolling(8, min_periods=8).std(ddof=1))
    history['sue_history_n'] = grouped.transform(lambda s: s.shift(1).rolling(8, min_periods=1).count())
    history['sue'] = history.ue / history.sue_history_std.where(history.sue_history_std > 0)
    return history
