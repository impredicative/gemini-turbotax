import pathlib
import re
from typing import Optional
import warnings

import pandas as pd
import fire

warnings.formatwarning = lambda message, category, filename, lineno, line=None: f'{category.__name__}: {message}\n'


def convert(input_path: str, output_path: Optional[str] = None) -> None:
    # Define paths
    input_path = pathlib.Path(input_path)
    if output_path is None:
        output_path = input_path.parent / f'{input_path.stem}_turbotax.csv'
    print(f'Converting {input_path} to {output_path}.')

    # Read Gemini dataframe
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning, module=re.escape('openpyxl.styles.stylesheet'))
        df_gemini = pd.read_excel(input_path, engine='openpyxl')
    print(f'Read Gemini file with {len(df_gemini)} rows.')

    # Cleanup Gemini dataframe
    num_gemini_na_rows = df_gemini['Date'].isna().sum()
    df_gemini.dropna(subset='Date', inplace=True)  # Removes last row which just has "USD Balance USD".
    if num_gemini_na_rows > 0:
        warnings.warn(f'Skipped {num_gemini_na_rows} empty rows from the Gemini file, leaving {len(df_gemini)} rows.')

    # Validate Gemini dataframe
    if df_gemini.empty:
        warnings.warn(f'Aborting because there are no Gemini rows.')
        return

    # Create TurboTax dataframe
    df_turbotax = pd.DataFrame()
    df_turbotax['Date'] = df_gemini['Time (UTC)']
    df_turbotax['Type'] = df_gemini['Type'].replace('Sell', 'Sale')


def main() -> None:  # Used as target by pyproject.toml
    fire.Fire(convert)


if __name__ == '__main__':
    main()
