"""Data analysis mode (launcher menu 7, Session 53).

Statistics on a table of data. Every number is computed by Python on this
machine; no AI model is called, so the launcher asks for no provider, model
or time limit and main.py runs no cloud gate.

B1: list the .csv and .xlsx files in input/data_analysis/.
B2 (this step): pick one file (and sheet), read it, show each column's type
with the reason and its missing values (table.py); save run.log in
reports/data_analysis/<run_id>/. No cell value is printed or logged.
Next: B3-B6 add the Comparison, Effect size, Correlation and Random forest
submenus; B7 writes the report.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

INPUT_EXT = {".csv", ".xlsx"}
LOCAL_LINE = ("[LOCAL] No AI model is used: every number is computed by "
              "Python on this machine. Your data does not leave it.")
XLS_HINT = " - old Excel format: open it in Excel and save it as .xlsx"


def input_dir(base_dir) -> Path:
    return Path(base_dir) / "input" / "data_analysis"


def reports_dir(base_dir) -> Path:
    return Path(base_dir) / "reports" / "data_analysis"


def new_run_id(now=None) -> str:
    """Run folder name, same shape as SR and SaMD runs: YYYYMMDD_HHMMSS."""
    return (now or datetime.now()).strftime("%Y%m%d_%H%M%S")


def _is_hidden(name: str) -> bool:
    # ~$name.xlsx is the lock file Excel keeps while a workbook is open.
    return name.startswith((".", "~$"))


def list_inputs(folder: Path) -> tuple[list[str], list[str]]:
    """(usable, skipped) file names, sorted without regard to case."""
    usable, skipped = [], []
    for p in sorted(folder.iterdir(), key=lambda q: q.name.lower()):
        if not p.is_file() or _is_hidden(p.name):
            continue
        if p.suffix.lower() in INPUT_EXT:
            usable.append(p.name)
        else:
            skipped.append(p.name)
    return usable, skipped


def choose_file(files, input_fn=input, say=print):
    """One file: used without a question. Several: number, Enter = 1, 0 = stop."""
    if len(files) == 1:
        say(f"Using the only data file: {files[0]}")
        return files[0]
    answer = input_fn("File number (Enter = 1, 0 = stop): ").strip()
    if not answer:
        return files[0]
    if answer == "0":
        say("Stopped. Nothing was read.")
        return None
    if answer.isdigit() and 1 <= int(answer) <= len(files):
        return files[int(answer) - 1]
    say(f"Not a valid file number: {answer}. Nothing was read.")
    return None


def choose_sheet(sheets, input_fn=input, say=print):
    """One sheet: used. Several: number, Enter = 1."""
    if len(sheets) == 1:
        return sheets[0]
    say("Sheets in this workbook:")
    for i, name in enumerate(sheets, 1):
        say(f"  {i}. {name}")
    answer = input_fn("Sheet number (Enter = 1): ").strip()
    if not answer:
        return sheets[0]
    if answer.isdigit() and 1 <= int(answer) <= len(sheets):
        return sheets[int(answer) - 1]
    say(f"Not a valid sheet number: {answer}. Nothing was read.")
    return None


def _write_log(run_dir: Path, lines) -> Path:
    run_dir.mkdir(parents=True, exist_ok=True)
    p = run_dir / "run.log"
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    return p


def run(base_dir, *, say=print, input_fn=input, now=None) -> list[str]:
    """List the data files, read the chosen one, describe its columns.

    Returns the usable file names in input/data_analysis/.
    """
    log = []

    def show(msg=""):
        log.append(msg)
        say(msg)

    folder = input_dir(base_dir)
    folder.mkdir(parents=True, exist_ok=True)
    show("")
    show("DATA ANALYSIS")
    show(LOCAL_LINE)
    show("")
    usable, skipped = list_inputs(folder)
    show(f"Folder: {folder}")
    if usable:
        show(f"Data files ({len(usable)}):")
        for i, name in enumerate(usable, 1):
            show(f"  {i}. {name}")
    else:
        show("No .csv or .xlsx file found. Put your data table in the folder above.")
    if skipped:
        show(f"Skipped ({len(skipped)}; only .csv and .xlsx are read):")
        for name in skipped:
            hint = XLS_HINT if name.lower().endswith(".xls") else ""
            show(f"  {name}{hint}")
    if not usable:
        return usable

    name = choose_file(usable, input_fn, show)
    if name is None:
        return usable
    from . import table

    path = folder / name
    sheet = None
    run_dir = reports_dir(base_dir) / new_run_id(now)
    try:
        if path.suffix.lower() == ".xlsx":
            sheet = choose_sheet(table.sheet_names(path), input_fn, show)
            if sheet is None:
                return usable
        df = table.read_table(path, sheet)
    except table.TableError as e:
        show(f"Could not read {name}: {e}")
        _write_log(run_dir, log)
        return usable

    show("")
    for line in table.report_lines(name, df, sheet):
        show(line)
    show("")
    show("The analysis menus (Comparison, Effect size, Correlation, Random forest) "
         "come in the next updates.")
    p = _write_log(run_dir, log)
    say(f"Run log: {p}")
    return usable
