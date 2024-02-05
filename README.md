# gemini-turbotax
Convert a Gemini transaction history XLSX file to a TurboTax CSV file.

## Usage
* Obtain the `transaction_history.xlsx` file from Gemini for a given tax year, e.g. from Jan 1, 2023 to Dec 31, 2023.
* Ensure that [`rye`](https://rye-up.com/) is installed, available, and updated.
* Run `rye sync`.
* Run a command such as:
```
rye run convert --input-path=~/Downloads/transaction_history.xlsx --output-path=~/Downloads/transaction_history_turbotax.csv
```
Here, `--output-path` is optional and automatic.
