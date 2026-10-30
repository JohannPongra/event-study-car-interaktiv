"""ausgabe · export · sqlite – klar abgegrenzter Projektbaustein."""
from Programm.grundlagen.pfade import pfad
from contextlib import closing
from Programm.ausgabe.export.jamovi import jamovi_export
import json
import pandas as pd
import sqlite3

def datenbank(result, out, cfg):
    """SQLite bewahrt Detaildaten; PSPP erhält eine rechteckige Ereignistabelle."""
    out.mkdir(parents=True, exist_ok=True)
    temp = pfad(out, 'event_study.neu.sqlite')
    if temp.exists():
        temp.unlink()
    with closing(sqlite3.connect(temp)) as connection, connection:
        for name, frame in result.items():
            frame.to_sql(name, connection, index=False, if_exists='replace')
        pd.DataFrame([{'key': k, 'value': json.dumps(v, ensure_ascii=False)} for k, v in cfg.items()]).to_sql('settings', connection, index=False, if_exists='replace')
    temp.replace(pfad(out, 'event_study.sqlite'))
    from Programm.ausgabe.export.pspp import pspp_export
    pspp_export(result, out, cfg)
    jamovi_export(result['data'], out, cfg)
