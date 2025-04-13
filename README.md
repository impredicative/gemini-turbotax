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
* Obtain the Exchange `transaction_history.xlsx` file from Gemini for a given tax year, e.g. from Jan 1, 2024 to Dec 31, 2024, although historical values such as from Jan 1, 2015 also can optionally be included as necessary. Historical values are of course strictly necessary if buys were made in prior years for positions held in the relevant year.
* Clone or download this repo.
* Build and provision the defined devcontainer - this is the preferred way. Alternatively, ensure that [`rye`](https://rye-up.com/) is installed, available, and updated, then run `rye sync` or more narrowly just `rye sync --no-lock` if on Linux.
* To convert the file, from the repo directory, run a command such as the following
```
rye run convert --input-path=~/Downloads/transaction_history.xlsx --year=2024 --output-format=web|desktop --output-path=~/Downloads/transaction_history_turbotax.csv
```

Sample status output for `--output-format=web`:
```text
Read Gemini file (transaction_history.xlsx) with 260 rows.
Skipped 1 empty rows from the Gemini file, keeping 259 rows.
UserWarning: Skipped 73 rows with unsupported types from the Gemini file, keeping 186 rows. The 2 supported types are: Buy, Sell. The 2 observed unsupported types are: Credit, Debit.
UserWarning: Filtering by year is not performed for TurboTax web.
Wrote 2024 TurboTax web file (transaction_history_turbotax-web_2024.csv) with 186 rows.
```

Sample status output for `--output-format=desktop`:
```
Read Gemini file (transaction_history.xlsx) with 260 rows.
Skipped 1 empty rows from the Gemini file, keeping 259 rows.
UserWarning: Skipped 73 rows with unsupported types from the Gemini file, keeping 186 rows. The 2 supported types are: Buy, Sell. The 2 observed unsupported types are: Credit, Debit.
UserWarning: No buy lot was found for 40.35000000 GUSD sold on 2021-11-09 for 40.35, so a same-year purchase date of 2021-01-01 and a cost basis of 0.01 are used to prevent TurboTax validation errors.
UserWarning: No buy lot was found for 0.02245847 PAXG sold on 2024-06-21 for 42.69, so a same-year purchase date of 2024-01-01 and a cost basis of 0.01 are used to prevent TurboTax validation errors.
Filtered 131 output rows for all years to 9 output rows for the year 2024.
Wrote 2024 TurboTax desktop file (transaction_history_turbotax-desktop_2024.csv) with 9 rows.
```

## Disclaimer
<sub>This tool, "gemini-turbotax," is provided as is, without warranty of any kind, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose, and noninfringement. In no event shall the authors or copyright holders be liable for any claim, damages, or other liability, whether in an action of contract, tort or otherwise, arising from, out of, or in connection with the software or the use or other dealings in the software.</sub>

<sub>The usage of "gemini-turbotax" for converting Gemini exchange transaction history files to TurboTax CSV format is intended for informational and convenience purposes only. It does not constitute legal, tax, or financial advice. The accuracy of the generated CSV files is not guaranteed, and users are responsible for verifying the correctness of their tax documents before submission.</sub>

<sub>By using this tool, you acknowledge that you understand its limitations, including but not limited to the support for specific transaction types and symbols as outlined in the Limitations section of this document. You also acknowledge that you are responsible for any and all compliance with applicable laws and regulations regarding tax reporting and filing.</sub>

<sub>This tool is not affiliated with, endorsed, or sponsored by Gemini, TurboTax, or any related entities. Trademarks and company names mentioned herein are the property of their respective owners.</sub>

<sub>Users are encouraged to consult with a professional tax advisor or accountant for advice tailored to their specific circumstances.</sub>
