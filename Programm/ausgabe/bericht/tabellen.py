"""ausgabe · bericht · tabellen – klar abgegrenzter Projektbaustein."""
from Programm.ausgabe.formatierung import label
import pandas as pd
from Programm.ausgabe.formatierung import pwert
from Programm.ausgabe.formatierung import zahl

def tabelle(frame):
    if frame.empty:
        return '<p>Keine Einträge für diesen Lauf.</p>'
    return '<div class="table-wrap">' + frame.to_html(index=False, border=0, escape=True, na_rep='–', float_format=zahl) + '</div>'

def koeffiziententabelle(frame):
    if frame.empty:
        return tabelle(frame)
    table = pd.DataFrame({'Einflussgröße': frame.variable.map(label), 'Koeffizient': frame.coefficient.map(zahl), 'Standardfehler': frame.standard_error.map(zahl), 'p-Wert': frame.p.map(pwert), '95%-Intervall': [f'[{zahl(a)}; {zahl(b)}]' for a, b in zip(frame.ci_lower, frame.ci_upper)]})
    return tabelle(table)
