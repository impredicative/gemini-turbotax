from typing import Optional
import fire


def convert(input_path: str, output_path: Optional[str] = None) -> None:
    # Ref: https://ttlc.intuit.com/turbotax-support/en-us/help-article/cryptocurrency/create-csv-file-unsupported-source/L1yhp71Nt_US_en_US
    print(f'Converting {input_path} to {output_path}.')


def main() -> None:
    fire.Fire(convert)
