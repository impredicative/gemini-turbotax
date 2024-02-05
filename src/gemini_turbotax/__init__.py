import pathlib
from typing import Optional

import pandas as pd
import fire


def convert(input_path: str, output_path: Optional[str] = None) -> None:
    # Ref: https://ttlc.intuit.com/turbotax-support/en-us/help-article/cryptocurrency/create-csv-file-unsupported-source/L1yhp71Nt_US_en_US
    input_path = pathlib.Path(input_path)
    if output_path is None:
        output_path = input_path.parent / f'{input_path.stem}_gemini.csv'
    print(f'Converting {input_path} to {output_path}.')


def main() -> None:
    fire.Fire(convert)
