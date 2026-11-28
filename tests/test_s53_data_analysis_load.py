"""Session 53 B2: data_analysis reads one CSV/XLSX table and describes its columns.

Pinned:
- Type rule: true/false -> categorical; whole numbers with at most
  CATEGORICAL_MAX_LEVELS (10) distinct values -> categorical; other numbers ->
  continuous; text -> categorical; dates -> date; no values -> empty.
- Missing: empty cells, pandas' NA words, whitespace-only text.
- CSV must be UTF-8 (a BOM is fine); a clear message otherwise. .xlsx via
  openpyxl; several sheets -> the user picks one.
- One file is used without a question; several -> number, Enter = 1, 0 = stop.
- Screen and run.log show names and counts only, never a cell value.
- openpyxl pinned in requirements-local.txt, floor in requirements-base.txt.
"""
import ast
import re
from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest

import main

ROOT = Path(main.__file__).resolve().parents[1]
README = ROOT / "Readme" / "readme_data_analysis_pipeline.txt"
PKG = ROOT / "SOURCE_CODE" / "pipelines" / "data_analysis"
NOW = datetime(2026, 11, 28, 9, 30, 0)


def _t():
    from pipelines.data_analysis import table
    return table


def _cli():
    from pipelines.data_analysis import cli
    return cli


def _kind(values):
    return _t().describe_column(pd.Series(values, name="c"))["kind"]


def _folder(tmp_path):
    d = tmp_path / "input" / "data_analysis"
    d.mkdir(parents=True)
    return d


def _run(tmp_path, answers=()):
    answers = list(answers)
    asked = []

    def fake_input(prompt):
        asked.append(prompt)
        if not answers:
            raise AssertionError(f"unexpected question: {prompt}")
        return answers.pop(0)
    lines = []
    _cli().run(tmp_path, say=lines.append, input_fn=fake_input, now=NOW)
    return "\n".join(lines), asked


def _log(tmp_path):
    p = tmp_path / "reports" / "data_analysis" / "20261128_093000" / "run.log"
    return p.read_text(encoding="utf-8")


# --- column types -------------------------------------------------------------

def test_decimals_are_continuous():
    assert _kind([1.5, 2.25, 3.0, 4.75]) == "continuous"


def test_codes_are_categorical():
    assert _kind([0, 1, 1, 0, 1]) == "categorical"


@pytest.mark.parametrize("levels, kind", [(10, "categorical"), (11, "continuous")])
def test_threshold_is_ten_levels(levels, kind):
    assert _kind(list(range(levels)) * 2) == kind


def test_text_is_categorical():
    assert _kind(["a", "b", "a"]) == "categorical"


def test_true_false_is_categorical():
    assert _kind([True, False, True]) == "categorical"


def test_dates_are_not_analysed():
    assert _kind(pd.to_datetime(["2024-01-01", "2024-02-01"])) == "date"


def test_no_values_is_empty():
    assert _kind([None, None]) == "empty"


# --- missing values -----------------------------------------------------------

def _gappy():
    return pd.DataFrame({"a": [1.0, None, 3.0], "b": ["x", "  ", None]})


def test_missing_counts_include_blank_text():
    t = _t()
    cols = {c["name"]: c["missing"] for c in t.describe_table(t.clean_blanks(_gappy()))}
    assert cols == {"a": 1, "b": 2}


def test_rows_with_a_missing_value():
    t = _t()
    assert t.rows_with_missing(t.clean_blanks(_gappy())) == 2


# --- notes --------------------------------------------------------------------

def test_mostly_numbers_note_counts_without_values():
    d = _t().describe_column(pd.Series(["1", "2", "<3", "4", "5"], name="lab"))
    notes = " ".join(d["notes"])
    assert d["kind"] == "categorical"
    assert "1 of 5" in notes
    assert "<3" not in notes


def test_id_column_note():
    d = _t().describe_column(pd.Series([f"P{i:03d}" for i in range(12)], name="id"))
    assert any("every value is different" in n for n in d["notes"])


# --- reading ------------------------------------------------------------------

def test_csv_with_bom_and_chinese_header(tmp_path):
    p = tmp_path / "a.csv"
    p.write_bytes("\u5e74\u9f61,group\n30,A\n41,B\n".encode("utf-8-sig"))
    assert list(_t().read_table(p).columns) == ["\u5e74\u9f61", "group"]


def test_csv_not_utf8_says_so(tmp_path):
    p = tmp_path / "a.csv"
    p.write_bytes(b"name\ncaf\xe9\n")
    t = _t()
    with pytest.raises(t.TableError, match="UTF-8"):
        t.read_table(p)


def test_empty_csv_says_so(tmp_path):
    p = tmp_path / "a.csv"
    p.write_bytes(b"")
    t = _t()
    with pytest.raises(t.TableError, match="empty"):
        t.read_table(p)


def test_xlsx_reads_and_types(tmp_path):
    p = tmp_path / "a.xlsx"
    pd.DataFrame({"age": [30.5, 41.2, 55.0], "sex": ["F", "M", "F"]}).to_excel(
        p, index=False, engine="openpyxl")
    t = _t()
    kinds = {c["name"]: c["kind"] for c in t.describe_table(t.read_table(p))}
    assert kinds == {"age": "continuous", "sex": "categorical"}


def _two_sheets(p):
    with pd.ExcelWriter(p, engine="openpyxl") as w:
        pd.DataFrame({"height": [1.7, 1.8]}).to_excel(w, sheet_name="first", index=False)
        pd.DataFrame({"weight": [70.5, 80.1]}).to_excel(w, sheet_name="second", index=False)


def test_sheet_names_in_order(tmp_path):
    p = tmp_path / "a.xlsx"
    _two_sheets(p)
    assert _t().sheet_names(p) == ["first", "second"]


def test_read_table_by_sheet_name(tmp_path):
    p = tmp_path / "a.xlsx"
    _two_sheets(p)
    assert list(_t().read_table(p, "second").columns) == ["weight"]


def test_bad_xlsx_says_so(tmp_path):
    p = tmp_path / "a.xlsx"
    p.write_text("x", encoding="utf-8")
    t = _t()
    with pytest.raises(t.TableError, match=r"\.xlsx"):
        t.read_table(p)
    with pytest.raises(t.TableError, match=r"\.xlsx"):
        t.sheet_names(p)


# --- run(): questions, screen, run.log -----------------------------------------

def test_run_one_file_asks_nothing_and_writes_log(tmp_path):
    (_folder(tmp_path) / "a.csv").write_text("age,group\n30.5,A\n41.0,B\n", encoding="utf-8")
    out, asked = _run(tmp_path)
    assert asked == []
    assert "2 rows" in out and "continuous" in out
    assert "a.csv" in _log(tmp_path)


def test_run_picks_file_by_number(tmp_path):
    d = _folder(tmp_path)
    (d / "a.csv").write_text("height\n1.7\n", encoding="utf-8")
    (d / "b.csv").write_text("weight\n70.5\n", encoding="utf-8")
    out, asked = _run(tmp_path, ["2"])
    assert len(asked) == 1
    assert "weight" in out and "height" not in out


def test_run_zero_stops_without_reading(tmp_path):
    d = _folder(tmp_path)
    (d / "a.csv").write_text("x\n1\n", encoding="utf-8")
    (d / "b.csv").write_text("y\n2\n", encoding="utf-8")
    out, _ = _run(tmp_path, ["0"])
    assert "Nothing was read" in out
    assert not (tmp_path / "reports").exists()


def test_run_invalid_number_stops(tmp_path):
    d = _folder(tmp_path)
    (d / "a.csv").write_text("x\n1\n", encoding="utf-8")
    (d / "b.csv").write_text("y\n2\n", encoding="utf-8")
    out, _ = _run(tmp_path, ["5"])
    assert "Not a valid file number" in out


def test_run_asks_for_sheet(tmp_path):
    _two_sheets(_folder(tmp_path) / "a.xlsx")
    out, asked = _run(tmp_path, ["2"])
    assert len(asked) == 1 and "Sheet" in asked[0]
    assert "weight" in out


def test_run_shows_no_cell_values(tmp_path):
    (_folder(tmp_path) / "a.csv").write_text(
        "name,weight\nZebedee Quill,123.456\nAnn Lee,80.5\n", encoding="utf-8")
    out, _ = _run(tmp_path)
    log = _log(tmp_path)
    for secret in ("Zebedee", "123.456"):
        assert secret not in out and secret not in log


def test_run_bad_file_says_could_not_read(tmp_path):
    (_folder(tmp_path) / "a.csv").write_bytes(b"name\ncaf\xe9\n")
    out, _ = _run(tmp_path)
    assert "Could not read a.csv" in out and "UTF-8" in out


# --- readme and pins ------------------------------------------------------------

def test_readme_utf8_lf_and_threshold():
    raw = README.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf")
    assert b"\r\n" not in raw and raw.endswith(b"\n")
    flat = " ".join(raw.decode("utf-8").split())
    assert f"at most {_t().CATEGORICAL_MAX_LEVELS} distinct values" in flat


def test_readme_function_names_exist():
    names = set(re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\(\)", README.read_text(encoding="utf-8")))
    defined = set()
    for p in PKG.glob("*.py"):
        tree = ast.parse(p.read_text(encoding="utf-8"))
        defined |= {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
    assert names, "the readme names no function"
    assert names <= defined, sorted(names - defined)


def test_openpyxl_pinned():
    local = (ROOT / "requirements-local.txt").read_text(encoding="utf-8").split()
    base = (ROOT / "requirements-base.txt").read_text(encoding="utf-8").split()
    assert "openpyxl==3.1.5" in local
    assert "openpyxl>=3.1.5" in base
