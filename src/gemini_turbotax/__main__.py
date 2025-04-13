from collections import deque
import pathlib
import re
from typing import Literal, Optional, TypedDict
import warnings

import pandas as pd
import fire

import gemini_turbotax.config as config

warnings.formatwarning = lambda message, category, filename, lineno, line=None: f"{category.__name__}: {message}\n"


def set_pandas_display_options() -> None:
    """Set pandas display options."""
    # Ref: https://stackoverflow.com/a/52432757/
    display = pd.options.display

    display.max_columns = 1000
    display.max_rows = 10_000
    display.max_colwidth = 199
    display.width = 1000
    display.precision = 2
    display.float_format = lambda x: "{:,.2f}".format(x)  # Ref: https://stackoverflow.com/a/47614756/


set_pandas_display_options()


def _process_gemini(df_gemini: pd.DataFrame) -> None:
    """Process the Gemini dataframe in-place."""
    # Remove empty rows (with no date)
    num_gemini_na_rows = df_gemini["Date"].isna().sum()
    if num_gemini_na_rows > 0:
        df_gemini.dropna(subset="Date", inplace=True)  # Removes last row which just has "USD Balance USD".
        printer = warnings.warn if (num_gemini_na_rows > 1) else print  # Removing 1 row is normal.
        printer(f"Skipped {num_gemini_na_rows} empty rows from the Gemini file, keeping {len(df_gemini)} rows.")

    # Remove rows with unsupported types
    gemini_unsupported_types_mask = ~df_gemini["Type"].isin(config.GEMINI_SUPPORTED_TYPES)
    num_gemini_unsupported_type_rows = gemini_unsupported_types_mask.sum()
    gemini_unsupported_types = df_gemini.loc[gemini_unsupported_types_mask, "Type"].unique()
    if num_gemini_unsupported_type_rows > 0:
        df_gemini.drop(df_gemini[gemini_unsupported_types_mask].index, inplace=True)
        warnings.warn(
            f"Skipped {num_gemini_unsupported_type_rows} rows with unsupported types from the Gemini file, keeping {len(df_gemini)} rows. The {len(config.GEMINI_SUPPORTED_TYPES)} supported types are: {', '.join(config.GEMINI_SUPPORTED_TYPES)}. The {len(gemini_unsupported_types)} observed unsupported types are: {', '.join(gemini_unsupported_types)}."
        )

    # Remove rows with unsupported symbols
    gemini_unsupported_symbol_mask = ~df_gemini["Symbol"].str.endswith(config.GEMINI_SUPPORTED_SYMBOL_SUFFIX)
    num_gemini_unsupported_symbol_rows = gemini_unsupported_symbol_mask.sum()
    if num_gemini_unsupported_symbol_rows:
        df_gemini.drop(df_gemini[gemini_unsupported_symbol_mask].index, inplace=True)
        warnings.warn(f"Skipped {num_gemini_unsupported_symbol_rows} rows with unsupported symbols from the Gemini file, keeping {len(df_gemini)} rows. Only symbols ending in {config.GEMINI_SUPPORTED_SYMBOL_SUFFIX} are supported.")

    # Enhance Gemini dataframe
    df_gemini["Symbol Prefix"] = df_gemini["Symbol"].str.removesuffix(config.GEMINI_SUPPORTED_SYMBOL_SUFFIX)
    df_gemini["Symbol Prefix Amount"] = df_gemini.apply(lambda row: row[row["Symbol Prefix"] + " Amount " + row["Symbol Prefix"]], axis=1)

    # Validate Gemini dataframe
    assert not df_gemini.empty, "Gemini dataframe has no processable rows."
    assert df_gemini["Date"].is_monotonic_increasing, "Gemini dataframe is not chronologically sorted."


def _convert_gemini_to_turbotax_web(df_gemini: pd.DataFrame) -> pd.DataFrame:
    """Return the TurboTax web dataframe from the Gemini dataframe."""
    # Create TurboTax web dataframe
    df_turbotax_web = pd.DataFrame()
    df_turbotax_web["Date"] = df_gemini["Time (UTC)"]
    df_turbotax_web["Type"] = df_gemini["Type"].replace("Sell", "Sale")
    df_turbotax_web["Sent Asset"] = df_gemini["Type"].case_when([(lambda s: s.eq("Buy"), config.GEMINI_SUPPORTED_SYMBOL_SUFFIX), (lambda s: s.eq("Sell"), df_gemini["Symbol Prefix"])])
    df_turbotax_web["Sent Amount"] = df_gemini["Type"].case_when([(lambda s: s.eq("Buy"), -df_gemini["USD Amount USD"]), (lambda s: s.eq("Sell"), -df_gemini["Symbol Prefix Amount"])]).astype(float)
    df_turbotax_web["Received Asset"] = df_gemini["Type"].case_when([(lambda s: s.eq("Buy"), df_gemini["Symbol Prefix"]), (lambda s: s.eq("Sell"), config.GEMINI_SUPPORTED_SYMBOL_SUFFIX)])
    df_turbotax_web["Received Amount"] = df_gemini["Type"].case_when([(lambda s: s.eq("Buy"), df_gemini["Symbol Prefix Amount"]), (lambda s: s.eq("Sell"), df_gemini["USD Amount USD"])]).astype(float)
    df_turbotax_web["Fee Asset"] = config.GEMINI_SUPPORTED_SYMBOL_SUFFIX
    df_turbotax_web["Fee Amount"] = -df_gemini["Fee (USD) USD"]
    df_turbotax_web["Market Value Currency"] = config.GEMINI_SUPPORTED_SYMBOL_SUFFIX
    df_turbotax_web["Market Value"] = df_gemini["Type"].case_when([(lambda s: s.eq("Buy"), -df_gemini["USD Amount USD"] + -df_gemini["Fee (USD) USD"]), (lambda s: s.eq("Sell"), df_gemini["USD Amount USD"] - -df_gemini["Fee (USD) USD"])]).astype(float)
    df_turbotax_web["Description"] = df_gemini["Type"] + " " + df_gemini["Symbol Prefix"]
    df_turbotax_web["Transaction Hash"] = df_gemini["Tx Hash"]
    df_turbotax_web["Transaction ID"] = df_gemini["Trade ID"]

    # Validate TurboTax web dataframe
    positive_columns = ("Sent Amount", "Received Amount", "Market Value")
    for col in positive_columns:
        assert (df_turbotax_web[col] > 0).all(), (col, df_turbotax_web[col].min())
    nonnegative_columns = ("Fee Amount",)
    for col in nonnegative_columns:
        assert (df_turbotax_web[col] >= 0).all(), (col, df_turbotax_web[col].min())

    return df_turbotax_web


def _convert_turbotax_web_to_desktop(df_turbotax_web: pd.DataFrame) -> pd.DataFrame:
    """Return the TurboTax desktop dataframe from the TurboTax web dataframe using FIFO accounting."""

    BuyLot = TypedDict("BuyLot", {"Purchase Date": pd.Timestamp, "Quantity": float, "Unit Cost": float})
    ResultRow = TypedDict("ResultRow", {"Currency Name": str, "Purchase Date": pd.Timestamp, "Cost Basis": float, "Date Sold": pd.Timestamp, "Proceeds": float})

    buy_lots: dict[str, deque[BuyLot]] = {}
    result_rows: list[ResultRow] = []

    # Process each transaction
    for i, row in df_turbotax_web.iterrows():
        date = row["Date"]

        match row["Type"]:
            case "Buy":
                asset = row["Received Asset"]
                quantity = row["Received Amount"]
                assert quantity > 0, f"Buy quantity was expected to be positive but it is {quantity:.8f}."
                cost = row["Sent Amount"]
                fee = row["Fee Amount"]
                total_cost = cost + fee
                unit_cost = total_cost / quantity

                buy_lot: BuyLot = {"Purchase Date": date, "Quantity": quantity, "Unit Cost": unit_cost}
                buy_lots.setdefault(asset, deque()).append(buy_lot)
            case "Sale":
                asset = row["Sent Asset"]
                quantity_to_match = row["Sent Amount"]
                assert quantity_to_match > 0, f"Sale quantity was expected to be positive but it is {quantity_to_match:.8f}."
                gross_proceeds = row["Received Amount"]
                fee = row["Fee Amount"]
                net_proceeds = gross_proceeds - fee
                unit_proceeds = net_proceeds / quantity_to_match

                while quantity_to_match > 0:
                    if (asset in buy_lots) and buy_lots[asset]:
                        lot = buy_lots[asset][0]
                        lot_qty = lot["Quantity"]
                        match_qty = min(quantity_to_match, lot_qty)
                        assert match_qty > 0, f"Matched quantity was expected to be positive but it is {match_qty:.8f}."
                        cost_basis = match_qty * lot["Unit Cost"]
                        proceeds = match_qty * unit_proceeds

                        result_row: ResultRow = {"Currency Name": asset, "Purchase Date": lot["Purchase Date"], "Cost Basis": cost_basis, "Date Sold": date, "Proceeds": proceeds}
                        result_rows.append(result_row)

                        quantity_to_match -= match_qty
                        if match_qty == lot_qty:
                            buy_lots[asset].popleft()
                        else:
                            lot["Quantity"] -= match_qty
                            assert lot["Quantity"] > 0, f"Remaining buy lot quantity was expected to be positive but it is {lot['Quantity']:.8f}."
                    else:
                        unmatched_qty = quantity_to_match
                        assert unmatched_qty > 0, f"Unmatched quantity was expected to be positive but it is {unmatched_qty:.8f}."
                        proceeds = unmatched_qty * unit_proceeds

                        purchase_date = pd.Timestamp(year=date.year, month=1, day=1)  # Prevents TurboTax validation error with value of pd.NaT.
                        cost_basis = 0.01  # Prevents TurboTax validation error with value of 0.0 or 0.000_000_01.
                        # Note: The proceeds are intentionally not incremented by the cost basis to avoid breaking standard auditability.
                        result_row: ResultRow = {"Currency Name": asset, "Purchase Date": purchase_date, "Cost Basis": cost_basis, "Date Sold": date, "Proceeds": proceeds}
                        if result_row["Proceeds"] > 0:
                            warnings.warn(f"No buy lot was found for {unmatched_qty:.8f} {asset} sold on {date.strftime('%Y-%m-%d')} for {proceeds:.2f}, so a same-year purchase date of {purchase_date.strftime('%Y-%m-%d')} and a cost basis of {cost_basis:.2f} are used to prevent TurboTax validation errors.")
                        result_rows.append(result_row)

                        quantity_to_match = 0
            case _:
                raise ValueError(f"Unsupported transaction type: {row['Type']}")

    assert result_rows, "No matched transactions produced."
    return pd.DataFrame(result_rows)


def convert(input_path: str, year: int, output_format: Literal["web", "desktop"], output_path: Optional[str] = None) -> None:
    # Define paths
    input_path = pathlib.Path(input_path)
    if output_path is None:
        output_path = input_path.parent / f"{input_path.stem}_turbotax-{output_format}_{year}.csv"
    print(f"Converting {input_path} to {output_path} in {output_format} output format.")

    # Read Gemini dataframe
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning, module=re.escape("openpyxl.styles.stylesheet"))
        df_gemini = pd.read_excel(
            input_path,
            dtype={"Trade ID": "UInt64", "Order ID": "UInt64"},  # Read as float64 if unspecified. Int32 and UInt32 are insufficient.
            engine="openpyxl",
        )
    print(f"Read Gemini file ({input_path}) with {len(df_gemini)} rows.")

    # Create and write TurboTax output dataframe
    _process_gemini(df_gemini)
    df_turbotax_web = _convert_gemini_to_turbotax_web(df_gemini)  # Needed for both web and desktop formats.
    match output_format:
        case "web":
            warnings.warn("Filtering by year is not performed for TurboTax web.")
            df_turbotax_web.to_csv(output_path, index=False, float_format="%.8f", date_format="%Y-%m-%d %H:%M:%S")
            print(f"Wrote {year} TurboTax {output_format} file ({output_path}) with {len(df_turbotax_web)} rows.")
        case "desktop":
            df_turbotax_desktop = _convert_turbotax_web_to_desktop(df_turbotax_web)
            num_rows_for_all_years = len(df_turbotax_desktop)
            df_turbotax_desktop = df_turbotax_desktop[df_turbotax_desktop["Date Sold"].dt.year == year]
            num_rows_for_year = len(df_turbotax_desktop)
            print(f"Filtered {num_rows_for_all_years:,} output rows for all years to {num_rows_for_year:,} output rows for the year {year}.")
            df_turbotax_desktop.to_csv(output_path, index=False, float_format="%.8f", date_format="%Y-%m-%d")
            print(f"Wrote {year} TurboTax {output_format} file ({output_path}) with {len(df_turbotax_desktop)} rows.")
        case _:
            raise ValueError(f"Invalid output format: {output_format}")


def main() -> None:  # Used as execution target configured in pyproject.toml.
    fire.Fire(convert)


if __name__ == "__main__":
    main()
