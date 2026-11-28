"""Data analysis B2: read one table and describe its columns (Session 53).

Every number here comes from pandas; no AI model is used. Nothing in this
module returns or prints a cell value: only column names and counts, so the
screen and run.log can be shared without exposing patient data.
Works on the venv (pandas 3) and the CI pins (pandas 2.2.2): column types are
judged with pandas' own type checks, never by dtype names ('str' vs 'object').
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from pandas.api.types import (is_bool_dtype, is_datetime64_any_dtype,
                              is_numeric_dtype)

CATEGORICAL_MAX_LEVELS = 10   # whole numbers with at most this many values = codes
MOSTLY_NUMBERS = 0.8          # a text column this full of numbers gets a note
NAME_WIDTH = 30
KINDS = ("continuous", "categorical", "date", "empty")


class TableError(Exception):
    """The file could not be read as a table; the message says why."""


def _xlsx_error(e) -> TableError:
    return TableError(f"not a readable .xlsx file ({type(e).__name__})")


def sheet_names(path) -> list[str]:
    """Sheet names of an .xlsx workbook, in workbook order."""
    try:
        with pd.ExcelFile(path, engine="openpyxl") as book:
            return [str(s) for s in book.sheet_names]
    except Exception as e:
        raise _xlsx_error(e) from e


def read_table(path, sheet=None) -> pd.DataFrame:
    """One table; the first row gives the column names. Blank text = missing."""
    path = Path(path)
    if path.suffix.lower() == ".xlsx":
        try:
            df = pd.read_excel(path, sheet_name=0 if sheet is None else sheet,
                               engine="openpyxl")
        except Exception as e:
            raise _xlsx_error(e) from e
    else:
        try:
            df = pd.read_csv(path, encoding="utf-8-sig")
        except UnicodeDecodeError as e:
            raise TableError("the file is not UTF-8 text. In Excel use Save As > "
                             "CSV UTF-8 (Comma delimited).") from e
        except pd.errors.EmptyDataError as e:
            raise TableError("the file is empty") from e
        except pd.errors.ParserError as e:
            raise TableError("the rows do not all have the same number of columns "
                             f"({type(e).__name__})") from e
    return clean_blanks(df)


def clean_blanks(df: pd.DataFrame) -> pd.DataFrame:
    """Text cells holding only spaces become missing (a copy is returned)."""
    df = df.copy()
    for c in df.columns:
        s = df[c]
        if is_numeric_dtype(s) or is_datetime64_any_dtype(s):
            continue
        blank = s.map(lambda v: isinstance(v, str) and not v.strip()).astype(bool)
        if blank.any():
            df[c] = s.mask(blank)
    return df


def describe_column(s: pd.Series) -> dict:
    """Type, reason, missing count and notes for one column (no cell values)."""
    n = int(len(s))
    missing = int(s.isna().sum())
    vals = s.dropna()
    levels = int(vals.nunique())
    notes = []
    if vals.empty:
        kind, why = "empty", "no values"
    elif is_bool_dtype(s):
        kind, why = "categorical", "true/false values"
    elif is_datetime64_any_dtype(s):
        kind, why = "date", "dates (not analysed)"
    elif is_numeric_dtype(s):
        whole = bool((vals == vals.round()).all())
        if whole and levels <= CATEGORICAL_MAX_LEVELS:
            kind, why = "categorical", (f"whole numbers, {levels} distinct values "
                                        f"(at most {CATEGORICAL_MAX_LEVELS})")
        elif whole:
            kind, why = "continuous", (f"whole numbers, {levels} distinct values "
                                       f"(more than {CATEGORICAL_MAX_LEVELS})")
        else:
            kind, why = "continuous", "numbers with decimals"
    else:
        kind, why = "categorical", f"text, {levels} distinct values"
        numeric = int(pd.to_numeric(vals, errors="coerce").notna().sum())
        bad = len(vals) - numeric
        if bad and numeric >= MOSTLY_NUMBERS * len(vals):
            notes.append(f"{bad} of {len(vals)} values are not numbers - check for "
                         "text such as '<5' or 'n/a'")
        if levels == len(vals) and len(vals) > CATEGORICAL_MAX_LEVELS:
            notes.append(f"every value is different ({levels} values) - "
                         "an ID or name column?")
    return {"name": str(s.name), "kind": kind, "why": why, "n": n,
            "missing": missing, "notes": notes}


def describe_table(df: pd.DataFrame) -> list[dict]:
    return [describe_column(df.iloc[:, i]) for i in range(df.shape[1])]


def rows_with_missing(df: pd.DataFrame) -> int:
    return int(df.isna().any(axis=1).sum())


def _short(name: str) -> str:
    return name if len(name) <= NAME_WIDTH else name[:NAME_WIDTH - 3] + "..."


def report_lines(file_name: str, df: pd.DataFrame, sheet=None) -> list[str]:
    """The column table as printed and logged: names, types, counts only."""
    cols = describe_table(df)
    n_rows = int(df.shape[0])
    where = f", sheet {sheet}" if sheet is not None else ""
    lines = [f"Table: {file_name}{where} - {n_rows} rows, {len(cols)} columns"]
    if n_rows == 0:
        lines.append("No data rows below the header row.")
    lines.append(f"Rows with at least one missing value: {rows_with_missing(df)} of {n_rows}")
    lines.append("")
    w = max([6] + [len(_short(c["name"])) for c in cols])
    lines.append(f"  #  {'Column':<{w}}  {'Type':<11}  {'Missing':<14}  Why")
    for i, c in enumerate(cols, 1):
        m = c["missing"]
        miss = f"{m} ({m / c['n'] * 100:.1f}%)" if m and c["n"] else str(m)
        lines.append(f"{i:3d}  {_short(c['name']):<{w}}  {c['kind']:<11}  {miss:<14}  {c['why']}")
    noted = [(c["name"], note) for c in cols for note in c["notes"]]
    if noted:
        lines.append("")
        lines.append("Notes:")
        for name, note in noted:
            lines.append(f"  {_short(name)}: {note}")
    counts = ", ".join(f"{sum(c['kind'] == k for c in cols)} {k}" for k in KINDS)
    lines.append("")
    lines.append(f"Types: {counts}")
    return lines
