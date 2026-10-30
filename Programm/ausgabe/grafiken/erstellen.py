"""ausgabe · grafiken · erstellen – klar abgegrenzter Projektbaustein."""
from Programm.ausgabe.grafiken.partielle_zusammenhaenge import partielle_zusammenhaenge
from Programm.ausgabe.grafiken.koeffizienten import koeffizienten
from Programm.ausgabe.grafiken.diagnostik import diagnostik
from Programm.ausgabe.grafiken.robustheit import robustheit
from Programm.ausgabe.grafiken.ereignisverlauf import ereignisverlauf
from Programm.ausgabe.formatierung import ZIELE
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def grafiken(out, data, coefficients, models, daily, cfg, variants):
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False, 'axes.labelcolor': '#17312f', 'text.color': '#17312f', 'axes.titleweight': 'bold', 'figure.facecolor': 'white', 'savefig.facecolor': 'white', 'axes.grid': True, 'grid.alpha': 0.15, 'pdf.fonttype': 42})
    for outcome, title in ZIELE.items():
        partielle_zusammenhaenge(out, data, coefficients, models, cfg, variants, outcome, title)
        koeffizienten(out, data, coefficients, models, cfg, variants, outcome, title)
        diagnostik(out, data, coefficients, models, cfg, variants, outcome, title)
        robustheit(out, data, coefficients, models, cfg, variants, outcome, title)
    ereignisverlauf(out, data, daily, cfg)
