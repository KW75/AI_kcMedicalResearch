"""Data analysis mode (launcher menu 7, Session 53).

Statistics on a table of data. Every number is computed by Python on this
machine; no AI model is called, so the launcher asks for no provider, model
or time limit and main.py runs no cloud gate.

B1 (this step): list the .csv and .xlsx files in input/data_analysis/.
Next: B2 loads a table and describes its columns; B3-B6 add the Comparison,
Effect size, Correlation and Random forest submenus; B7 writes the report.
"""
from __future__ import annotations

from pathlib import Path

INPUT_EXT = {".csv", ".xlsx"}
LOCAL_LINE = ("[LOCAL] No AI model is used: every number is computed by "
              "Python on this machine. Your data does not leave it.")
XLS_HINT = " - old Excel format: open it in Excel and save it as .xlsx"


def input_dir(base_dir) -> Path:
    return Path(base_dir) / "input" / "data_analysis"


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


def run(base_dir, *, say=print) -> list[str]:
    """List the data files in input/data_analysis/; return the usable names."""
    folder = input_dir(base_dir)
    folder.mkdir(parents=True, exist_ok=True)
    say("")
    say("DATA ANALYSIS")
    say(LOCAL_LINE)
    say("")
    usable, skipped = list_inputs(folder)
    say(f"Folder: {folder}")
    if usable:
        say(f"Data files ({len(usable)}):")
        for i, name in enumerate(usable, 1):
            say(f"  {i}. {name}")
    else:
        say("No .csv or .xlsx file found. Put your data table in the folder above.")
    if skipped:
        say(f"Skipped ({len(skipped)}; only .csv and .xlsx are read):")
        for name in skipped:
            hint = XLS_HINT if name.lower().endswith(".xls") else ""
            say(f"  {name}{hint}")
    say("")
    say("Loading a table and the analysis menus come in the next updates.")
    return usable
