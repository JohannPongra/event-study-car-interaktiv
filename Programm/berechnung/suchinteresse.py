"""berechnung · suchinteresse – klar abgegrenzter Projektbaustein."""
from datetime import date, timedelta
import numpy as np
import pandas as pd
from Programm.grundlagen.konfiguration import suchbegriff

def suchinteresse(row, weeks, cfg):
    """SEARCH: genau neun Wochen desselben Exports, niemals Skalen zusammenfügen."""
    result = {'search': np.nan, 'search_source': 'nicht verfügbar', 'search_export': '', 'search_event_svi': np.nan, 'search_baseline_median': np.nan}
    if pd.isna(row.event_trading_day):
        return result
    event_day = date.fromisoformat(str(row.event_trading_day)[:10])
    sunday = event_day - timedelta(days=(event_day.weekday() + 1) % 7)
    required = [(sunday - timedelta(weeks=8 - i)).isoformat() for i in range(9)]
    query = suchbegriff(cfg, row.ticker, row.reported_date)
    candidates = weeks.loc[weeks.ticker.eq(row.ticker) & weeks['query'].eq(query)]
    exports = [(bool(part.supplemental.iloc[0]), part.week.min(), name, part) for name, part in candidates.groupby('export_id')]
    for _, _, name, part in sorted(exports, key=lambda item: item[:3]):
        values = part.set_index('week').svi.reindex(required)
        if not np.isfinite(values).all() or not values.gt(0).all():
            continue
        median, event_svi = (float(values.iloc[:8].median()), float(values.iloc[8]))
        result.update({'search': float(np.log(event_svi / median)), 'search_source': 'ein Rohdatenexport', 'search_export': name, 'search_event_week': sunday.strftime('%Y-%m-%d'), 'search_query': query, 'search_event_svi': event_svi, 'search_baseline_median': median, 'search_baseline_values': ';'.join((str(v) for v in values.iloc[:8])), 'search_export_sha256': part.source_sha256.iloc[0]})
        break
    return result
