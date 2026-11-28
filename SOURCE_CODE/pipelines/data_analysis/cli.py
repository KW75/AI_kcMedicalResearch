"""Data analysis mode (launcher menu 7, Session 53).

Statistics on a table of data. Every number is computed by Python on this
machine; no AI model is called, so the launcher asks for no provider, model
or time limit and main.py runs no cloud gate and checks no API key.

B1: list the .csv and .xlsx files in input/data_analysis/.
B2: pick one file (and sheet), read it, show each column's type with the
reason and its missing values (table.py); save run.log in
reports/data_analysis/<run_id>/.
B3 (this step): analysis menu, 1 = Comparison (compare.py): an outcome column
across the groups of a categorical column. Group labels and summaries per
group are printed; a single cell value never is.
Next: B4-B6 add Effect size, Correlation and Random forest; B7 writes the
report.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

INPUT_EXT = {".csv", ".xlsx"}
LOCAL_LINE = ("[LOCAL] No AI model is used: every number is computed by "
              "Python on this machine. Your data does not leave it.")
XLS_HINT = " - old Excel format: open it in Excel and save it as .xlsx"
MENU_PROMPT = "Analysis (1 = Comparison, Enter or 0 = stop): "


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


def pick_column(df, prompt, input_fn=input, say=print):
    """A column by its # in the column table; None if the answer is not valid."""
    answer = input_fn(prompt).strip()
    if answer.isdigit() and 1 <= int(answer) <= df.shape[1]:
        return int(answer) - 1
    say(f"Not a valid column number: {answer or '(empty)'}.")
    return None


def analysis_menu(df, input_fn=input, say=print) -> None:
    """1 = Comparison (repeatable); Enter or 0 = stop."""
    from . import compare

    while True:
        say("")
        answer = input_fn(MENU_PROMPT).strip()
        if answer in ("", "0"):
            return
        if answer != "1":
            say(f"Not a valid choice: {answer}.")
            continue
        say("Comparison: choose the columns by their # in the table above.")
        oi = pick_column(df, "Outcome column number: ", input_fn, say)
        if oi is None:
            continue
        gi = pick_column(df, "Group column number (categorical): ", input_fn, say)
        if gi is None:
            continue
        if oi == gi:
            say("Outcome and group must be different columns.")
            continue
        try:
            res = compare.compare(df.iloc[:, oi], df.iloc[:, gi])
        except compare.CompareError as e:
            say(f"Comparison not run: {e}")
            continue
        say("")
        for line in res["lines"]:
            say(line)


def _write_log(run_dir: Path, lines) -> Path:
    run_dir.mkdir(parents=True, exist_ok=True)
    p = run_dir / "run.log"
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    return p


def run(base_dir, *, say=print, input_fn=input, now=None) -> list[str]:
    """List the data files, read the chosen one, describe it, run the menu.

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
    analysis_menu(df, input_fn, show)
    show("")
    show("Effect size, Correlation and Random forest come in the next updates.")
    p = _write_log(run_dir, log)
    say(f"Run log: {p}")
    return usable
