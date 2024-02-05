from typing import Optional
import fire


def convert(input_path: str, output_path: Optional[str] = None) -> None:
    print(f'Converting {input_path} to {output_path}.')


def main() -> None:
    fire.Fire(convert)
