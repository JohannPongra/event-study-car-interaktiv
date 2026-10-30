"""statistik · robustheit · einzelereignisse – klar abgegrenzter Projektbaustein."""
from Programm.statistik.regression import fit
from Programm.statistik.koeffizienten import koeffizienten
from Programm.grundlagen.konfiguration import modell_predictors
import pandas as pd

def abs_car_zusatz(data, cfg, fortschritt):
    predictors = modell_predictors(cfg, 'abs_car')
    leave_out = einzelereignisse(data, cfg, predictors)
    fortschritt('ABS_CAR: Einzelereignisse und Wild-Cluster-Bootstrap …')
    from Programm.statistik.robustheit.wild_bootstrap import wild_bootstrap
    return (leave_out, wild_bootstrap(data, cfg, predictors))

def einzelereignisse(data, cfg, predictors):
    leave_out = []
    for index in data.index:
        subset = data.drop(index)
        try:
            _, model, x = fit(subset, 'abs_car', predictors, cfg)
            for record in koeffizienten(model, x, 'ohne Einzelereignis', 'abs_car', subset, cfg):
                if record['variable'] in predictors:
                    record['omitted_event'] = data.loc[index, 'event_id']
                    leave_out.append(record)
        except ValueError as exc:
            leave_out.append({'omitted_event': data.loc[index, 'event_id'], 'message': str(exc)})
    return pd.DataFrame(leave_out)
