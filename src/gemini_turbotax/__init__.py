import pathlib
import re
from typing import Optional
import warnings

import pandas as pd
import fire


def convert(input_path: str, output_path: Optional[str] = None) -> None:
    input_path = pathlib.Path(input_path)
    if output_path is None:
        output_path = input_path.parent / f'{input_path.stem}_turbotax.csv'
    print(f'Converting {input_path} to {output_path}.')

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning, module=re.escape('openpyxl.styles.stylesheet'))
        df_gemini = pd.read_excel(input_path, engine='openpyxl')

    df_gemini.dropna(subset='Date', inplace=True)  # Removes last row which just has "USD Balance USD".


def main() -> None:  # Used as target by pyproject.toml
    fire.Fire(convert)


if __name__ == '__main__':
    main()
