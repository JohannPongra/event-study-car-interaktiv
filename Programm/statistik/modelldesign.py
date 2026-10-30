"""statistik · modelldesign – klar abgegrenzter Projektbaustein."""
from statsmodels.tools.tools import add_constant
import pandas as pd

def design(data, predictors, fixed_effects):
    x = data[predictors].astype(float).copy()
    if fixed_effects:
        for name in ['ticker', 'year', 'quarter']:
            x = pd.concat([x, pd.get_dummies(data[name].astype(str), prefix=name, drop_first=True, dtype=float)], axis=1)
    return add_constant(x, has_constant='add')
