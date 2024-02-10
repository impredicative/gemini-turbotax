import pathlib
import re
from typing import Optional
import warnings

import pandas as pd
import fire

import gemini_turbotax.config as config

warnings.formatwarning = lambda message, category, filename, lineno, line=None: f"{category.__name__}: {message}\n"


def convert(input_path: str, output_path: Optional[str] = None) -> None:
    # Define paths
    input_path = pathlib.Path(input_path)
    if output_path is None:
        output_path = input_path.parent / f"{input_path.stem}_turbotax.csv"
    print(f"Converting {input_path} to {output_path}.")

    # Read Gemini dataframe
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning, module=re.escape("openpyxl.styles.stylesheet"))
        df_gemini = pd.read_excel(input_path, engine="openpyxl")
    print(f"Read Gemini file ({input_path}) with {len(df_gemini)} rows.")

    # Filter Gemini dataframe
    num_gemini_na_rows = df_gemini["Date"].isna().sum()
    if num_gemini_na_rows > 0:
        df_gemini.dropna(subset="Date", inplace=True)  # Removes last row which just has "USD Balance USD".
        printer = warnings.warn if (num_gemini_na_rows > 1) else print  # Removing 1 row is normal.
        printer(f"Skipped {num_gemini_na_rows} empty rows from the Gemini file, keeping {len(df_gemini)} rows.")

    gemini_unsupported_types_mask = ~df_gemini["Type"].isin(config.GEMINI_SUPPORTED_TYPES)
    num_gemini_unsupported_type_rows = gemini_unsupported_types_mask.sum()
    if num_gemini_unsupported_type_rows > 0:
        df_gemini.drop(df_gemini[gemini_unsupported_types_mask].index, inplace=True)
        warnings.warn(f'Skipped {num_gemini_unsupported_type_rows} rows with unsupported types from the Gemini file, keeping {len(df_gemini)} rows. The supported types are: {", ".join(config.GEMINI_SUPPORTED_TYPES)}')

    gemini_unsupported_symbol_mask = ~df_gemini["Symbol"].str.endswith(config.GEMINI_SUPPORTED_SYMBOL_SUFFIX)
    num_gemini_unsupported_symbol_rows = gemini_unsupported_symbol_mask.sum()
    if num_gemini_unsupported_symbol_rows:
        df_gemini.drop(df_gemini[gemini_unsupported_symbol_mask].index, inplace=True)
        warnings.warn(f"Skipped {num_gemini_unsupported_symbol_rows} rows with unsupported symbols from the Gemini file, keeping {len(df_gemini)} rows. Only symbols ending in {config.GEMINI_SUPPORTED_SYMBOL_SUFFIX} are supported.")

    # Validate Gemini dataframe
    if df_gemini.empty:
        warnings.warn("Aborting because there are no Gemini rows to convert.")
        return

    # Enhance Gemini dataframe
    df_gemini["Symbol Prefix"] = df_gemini["Symbol"].str.removesuffix(config.GEMINI_SUPPORTED_SYMBOL_SUFFIX)
    df_gemini["Symbol Prefix Amount"] = df_gemini.apply(lambda row: row[row["Symbol Prefix"] + " Amount " + row["Symbol Prefix"]], axis=1)

    # Create TurboTax dataframe
    df_turbotax = pd.DataFrame()
    df_turbotax["Date"] = df_gemini["Time (UTC)"]
    df_turbotax["Type"] = df_gemini["Type"].replace("Sell", "Sale")
    df_turbotax["Sent Asset"] = df_gemini["Type"].case_when([(lambda s: s.eq("Buy"), config.GEMINI_SUPPORTED_SYMBOL_SUFFIX), (lambda s: s.eq("Sell"), df_gemini["Symbol Prefix"])])
    df_turbotax["Sent Amount"] = df_gemini["Type"].case_when([(lambda s: s.eq("Buy"), -df_gemini["USD Amount USD"]), (lambda s: s.eq("Sell"), -df_gemini["Symbol Prefix Amount"])]).astype(float)
    df_turbotax["Received Asset"] = df_gemini["Type"].case_when([(lambda s: s.eq("Buy"), df_gemini["Symbol Prefix"]), (lambda s: s.eq("Sell"), config.GEMINI_SUPPORTED_SYMBOL_SUFFIX)])
    df_turbotax["Received Amount"] = df_gemini["Type"].case_when([(lambda s: s.eq("Buy"), df_gemini["Symbol Prefix Amount"]), (lambda s: s.eq("Sell"), df_gemini["USD Amount USD"])]).astype(float)
    df_turbotax["Fee Asset"] = config.GEMINI_SUPPORTED_SYMBOL_SUFFIX
    df_turbotax["Fee Amount"] = -df_gemini["Fee (USD) USD"].astype(float)
    df_turbotax["Market Value Currency"] = config.GEMINI_SUPPORTED_SYMBOL_SUFFIX
    df_turbotax["Market Value"] = df_gemini["Type"].case_when([(lambda s: s.eq("Buy"), -df_gemini["USD Amount USD"] + -df_gemini["Fee (USD) USD"]), (lambda s: s.eq("Sell"), df_gemini["USD Amount USD"] - -df_gemini["Fee (USD) USD"])]).astype(float)
    df_turbotax["Description"] = df_gemini["Type"] + " " + df_gemini["Symbol Prefix"]
    df_turbotax["Transaction Hash"] = df_gemini["Tx Hash"]
    df_turbotax["Transaction ID"] = df_gemini["Trade ID"].astype(int)

    # Validate TurboTax dataframe
    number_columns = ("Sent Amount", "Received Amount", "Fee Amount")
    for number_column in number_columns:
        assert (df_turbotax[number_column] > 0).all(), number_column

    # Write TurboTax dataframe
    df_turbotax.to_csv(output_path, index=False, float_format="%.8f", date_format="%Y-%m-%d %H:%M:%S")
    print(f"Wrote TurboTax file ({output_path}) with {len(df_turbotax)} rows.")


def main() -> None:  # Used as target by pyproject.toml
    fire.Fire(convert)


if __name__ == "__main__":
    main()
