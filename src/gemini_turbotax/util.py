import pandas as pd

import gemini_turbotax.config as config


def turbotax_round(series: pd.Series) -> pd.Series:
    """Return the given Pandas series rounded to the TurboTax required number of decimal places."""
    return series.round(config.TURBOTAX_DECIMAL_PLACES)
