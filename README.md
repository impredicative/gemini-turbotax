# gemini-turbotax
Convert a [Gemini exchange transaction history XLSX](https://exchange.gemini.com/settings/documents/transaction-history) file to a [TurboTax CSV](https://ttlc.intuit.com/turbotax-support/en-us/help-article/cryptocurrency/create-csv-file-unsupported-source/L1yhp71Nt_US_en_US) file using Python Pandas.

## Contents
1. [gemini-turbotax](#gemini-turbotax)
2. [Limitations](#limitations)
3. [Usage](#usage)
4. [Disclaimer](#disclaimer)

## Limitations
* **Grow** transaction history file is not supported.
* **Type** column: Only "Buy" and "Sell" values are supported. Others are skipped.
* **Symbol** column: Only values ending in "USD" are supported. Others are skipped.

## Usage
* Obtain the Exchange `transaction_history.xlsx` file from Gemini for a given tax year, e.g. from Jan 1, 2023 to Dec 31, 2023, although historical values also can optionally be included as necessary.
* Clone or download this repo.
* Ensure that [`rye`](https://rye-up.com/) is installed, available, and updated.
* From the repo directory, run `rye sync`.
* To convert the file, from the repo directory, run a command such as the following, with `--output-path` being optional and automatic:
```
rye run convert --input-path=~/Downloads/transaction_history.xlsx --output-path=~/Downloads/transaction_history_turbotax.csv
```

Sample status output:
```text
Converting ~/Downloads/transaction_history.xlsx to ~/Downloads/transaction_history_turbotax.csv.
Read Gemini file (~/Downloads/transaction_history.xlsx) with 45 rows.
UserWarning: Skipped 1 empty rows from the Gemini file, keeping 44 rows.
Wrote TurboTax file (~/Downloads/transaction_history_turbotax.csv) with 44 rows.
```

## Disclaimer
This tool, "gemini-turbotax," is provided as is, without warranty of any kind, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose, and noninfringement. In no event shall the authors or copyright holders be liable for any claim, damages, or other liability, whether in an action of contract, tort or otherwise, arising from, out of, or in connection with the software or the use or other dealings in the software.

The usage of "gemini-turbotax" for converting Gemini exchange transaction history files to TurboTax CSV format is intended for informational and convenience purposes only. It does not constitute legal, tax, or financial advice. The accuracy of the generated CSV files is not guaranteed, and users are responsible for verifying the correctness of their tax documents before submission.

By using this tool, you acknowledge that you understand its limitations, including but not limited to the support for specific transaction types and symbols as outlined in the Limitations section of this document. You also acknowledge that you are responsible for any and all compliance with applicable laws and regulations regarding tax reporting and filing.

This tool is not affiliated with, endorsed, or sponsored by Gemini, TurboTax, or any related entities. Trademarks and company names mentioned herein are the property of their respective owners.

Users are encouraged to consult with a professional tax advisor or accountant for advice tailored to their specific circumstances.