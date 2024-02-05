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
    if num_gemini_na_rows > 0:
        df_gemini.dropna(subset='Date', inplace=True)  # Removes last row which just has "USD Balance USD".
        warnings.warn(f'Skipped {num_gemini_na_rows} empty rows from the Gemini file, keeping {len(df_gemini)} rows.')

    gemini_supported_types = ['Buy', 'Sell']
    gemini_unsupported_types_mask = ~df_gemini['Type'].isin(gemini_supported_types)
    num_gemini_unsupported_type_rows = gemini_unsupported_types_mask.sum()
    if num_gemini_unsupported_type_rows > 0:
        df_gemini.drop(df_gemini[gemini_unsupported_types_mask].index, inplace=True)
        warnings.warn(f'Skipped {num_gemini_unsupported_type_rows} rows with unsupported types from the Gemini file, keeping {len(df_gemini)} rows. The supported types are: {", ".join(gemini_supported_types)}')

    gemini_supported_symbol_suffix = 'USD'
    gemini_unsupported_symbol_mask = ~df_gemini['Symbol'].str.endswith(gemini_supported_symbol_suffix)
    num_gemini_unsupported_symbol_rows = gemini_unsupported_symbol_mask.sum()
    if num_gemini_unsupported_symbol_rows:
        df_gemini.drop(df_gemini[gemini_unsupported_symbol_mask].index, inplace=True)
        warnings.warn(f'Skipped {num_gemini_unsupported_symbol_rows} rows with unsupported symbols from the Gemini file, keeping {len(df_gemini)} rows. Only symbols ending in {gemini_supported_symbol_suffix} are supported.')

    # Validate Gemini dataframe
    if df_gemini.empty:
        warnings.warn('Aborting because there are no Gemini rows to convert.')
        return

    # Create TurboTax dataframe
    df_turbotax = pd.DataFrame()
    df_turbotax['Date'] = df_gemini['Time (UTC)']
    df_turbotax['Type'] = df_gemini['Type'].replace('Sell', 'Sale')
    df_turbotax['Sent Asset'] = df_gemini['Type'].case_when([(lambda s: s.eq('Buy'), gemini_supported_symbol_suffix), (lambda s: s.eq('Sell'), df_gemini['Symbol'].str.removesuffix(gemini_supported_symbol_suffix))])


def main() -> None:  # Used as target by pyproject.toml
    fire.Fire(convert)


if __name__ == '__main__':
    main()
