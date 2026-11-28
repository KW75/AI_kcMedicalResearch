==============================================================================
 AI_kcMedicalResearch - Data analysis mode (statistics, no AI)
 How it works, and why it was built this way
==============================================================================

This file explains the logic of data analysis mode: what happens to a data
table from the moment it is chosen, which method is used at each step, and
why. It is not a user guide. To start a run: launcher menu 7, or main.py
--mode data_analysis. The code is in SOURCE_CODE/pipelines/data_analysis/
(cli.py = the steps and questions; table.py = reading the table, column
types, missing values).

Status: being built (Session 53). Built so far: B1 (file list) and B2 (read
one table, column types, missing values). Planned: B3 Comparison, B4 Effect
size, B5 Correlation, B6 Random forest, B7 report files.

Contents
  1. What this mode is, and what it is not
  2. Design principles
  3. The pipeline, step by step
       3.1 Choose the file
       3.2 Read the table
       3.3 Missing values
       3.4 Column types
       3.5 Notes on a column
       3.6 Run log
  4. Honest limitations


------------------------------------------------------------------------------
1. What this mode is, and what it is not
------------------------------------------------------------------------------

Data analysis mode reads one table of data (one row per participant or
sample, one column per variable) and, step by step, will run standard
statistical tests on it. Every number is computed by Python: pandas and
scipy (scikit-learn for the random forest, from B6). No AI model is called,
so the launcher asks no provider, model or time limit, and main.py runs no
cloud gate.

It is not a replacement for a statistician. It checks the data and runs the
tests chosen by fixed rules; the user decides whether a test fits the study
design.


------------------------------------------------------------------------------
2. Design principles
------------------------------------------------------------------------------

- No AI, local only. The data never leaves the machine.
- Every number from Python, never from a language model.
- The screen and run.log show column names and counts only, never a cell
  value, so the output can be shared without exposing patient data.
- Pinned versions: requirements-local.txt pins pandas, numpy, scipy and
  openpyxl. The code is tested on those pins (CI job test-local-pins) and on
  newer versions (the development venv).
- Show the decision: each column's type is printed with its reason.


------------------------------------------------------------------------------
3. The pipeline, step by step
------------------------------------------------------------------------------

3.1 Choose the file

list_inputs() lists the .csv and .xlsx files in input/data_analysis/. Other
files are named as skipped; an old .xls file gets the hint to save it as
.xlsx in Excel. Excel lock files (~$name.xlsx) and hidden files are ignored.
choose_file(): one data file is used without a question. With several, the
user types a number: Enter = 1, 0 = stop. A wrong number stops the job and
nothing is read.

3.2 Read the table

read_table() reads the first row as the column names.
- CSV: read as UTF-8; a byte order mark (Excel's CSV UTF-8) is accepted.
  Any other encoding stops with a message: in Excel use Save As > CSV UTF-8
  (Comma delimited). The program does not guess an encoding, because a wrong
  guess silently changes text such as Chinese labels.
- .xlsx: read with openpyxl. sheet_names() lists the sheets; with more than
  one, choose_sheet() asks for a number (Enter = 1).
- A file that cannot be read stops the job with the reason: the file name
  and the kind of error, never its content.

3.3 Missing values

A cell counts as missing when it is empty, when it holds only spaces
(clean_blanks()), or when it holds one of the words pandas treats as
missing, such as NA, N/A, NULL, NaN or #N/A. For each column the count and
the percentage are shown; rows_with_missing() counts the rows with at least
one missing cell. Missing values are reported, never filled in.

3.4 Column types

describe_column() gives each column one type, judged on the values that are
not missing:
- true/false values: categorical.
- dates: date. Dates are listed but not analysed.
- numbers, all whole, at most 10 distinct values: categorical. These are
  usually codes (0/1 for sex, 1-5 for a grade).
- other numbers: continuous.
- text: categorical.
- no values at all: empty.
The limit of 10 is CATEGORICAL_MAX_LEVELS in table.py. describe_table()
applies the rule to every column; report_lines() prints the table with each
column's type and the reason.

3.5 Notes on a column

Two notes point at likely data-entry problems, with counts only:
- A text column in which at least 80% of the values are numbers: "N of M
  values are not numbers". A lab column with entries such as <5 or n/a is
  read as text; fix those cells (or empty them) and it becomes continuous.
- A text column in which every value is different (more than 10 values): it
  may be an ID or name column, which is not analysed as a group.

3.6 Run log

After a file is chosen, everything printed is also saved in
reports/data_analysis/<run_id>/run.log (run_id = YYYYMMDD_HHMMSS). Like the
screen, it holds no cell values.


------------------------------------------------------------------------------
4. Honest limitations
------------------------------------------------------------------------------

- The type rule is a rule, not judgement. A 0-10 pain score has 11 distinct
  values and is treated as continuous; a numeric patient number is treated
  as continuous too. There is no manual override yet.
- Only the first row is read as column names; titles or merged cells above
  the header in Excel confuse the reading.
- One table per run. Paired tests are not in the first version.
- .xls (old Excel) and other formats are not read.
