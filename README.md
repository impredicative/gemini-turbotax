# gemini-turbotax
Convert a [Gemini exchange transaction history XLSX](https://exchange.gemini.com/settings/documents/transaction-history) file to a [TurboTax CSV](https://ttlc.intuit.com/turbotax-support/en-us/help-article/cryptocurrency/create-csv-file-unsupported-source/L1yhp71Nt_US_en_US) file using Python Pandas.

## Usage
* Obtain the Exchange `transaction_history.xlsx` file from Gemini for a given tax year, e.g. from Jan 1, 2023 to Dec 31, 2023, although historical values also can optionally be included as necessary.
* Clone this repo.
* Ensure that [`rye`](https://rye-up.com/) is installed, available, and updated.
* From the repo directory, run `rye sync`.
* To convert the file, from the repo directory, run a command such as:
```
rye run convert --input-path=~/Downloads/transaction_history.xlsx --output-path=~/Downloads/transaction_history_turbotax.csv
```
Here, `--output-path` is optional and automatic.

## Limitations
* Grow transaction history is not supported.