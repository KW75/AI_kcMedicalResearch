"""Session 53 B3: data_analysis Comparison (compare.py and the analysis menu).

Pinned:
- Continuous outcome: 2 groups -> Welch t test if every group passes
  Shapiro-Wilk (p >= 0.05), else Mann-Whitney U; 3+ groups -> one-way ANOVA,
  else Kruskal-Wallis. Categorical outcome -> chi-square (Yates for 2 x 2);
  Fisher's exact for a 2 x 2 table with an expected count < 5; a larger table
  with small expected counts gets a warning.
- Fewer than 3 values or all values equal = not normal; Shapiro-Wilk is not
  called then (scipy 1.13.1 raises below 3).
- The numbers pinned here were identical on the venv (scipy 1.17.1) and the
  CI pins (scipy 1.13.1) in s53_look4.
- Group labels and per-group summaries are printed; single cells never.
- main.run_cli: --mode data_analysis needs no API key (no AI call), even when
  the provider named is a cloud one with no key set.
"""
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from scipy import stats

import main

ROOT = Path(main.__file__).resolve().parents[1]
README = ROOT / "Readme" / "readme_data_analysis_pipeline.txt"
NOW = datetime(2026, 11, 28, 9, 30, 0)
A = [5.1, 4.9, 6.2, 5.8, 6.0, 5.5, 5.3, 6.1]
B = [6.8, 7.1, 6.5, 7.4, 6.9, 7.0, 7.3, 6.6]
C = [5.9, 6.3, 6.1, 6.7, 6.0, 6.4, 6.2, 6.5]
SKEW = [1, 1, 1, 2, 2, 3, 9, 15]


def _c():
    from pipelines.data_analysis import compare
    return compare


def _cli():
    from pipelines.data_analysis import cli
    return cli


def _groups(*samples):
    y, g = [], []
    for lab, s in zip("ABCDEFGHIJ", samples):
        y += [float(v) for v in s]
        g += [lab] * len(s)
    return pd.Series(y, name="score"), pd.Series(g, name="group")


def _from_table(table, groups):
    y, g = [], []
    for o, row in zip(("neg", "pos", "unk"), table):
        for lab, n in zip(groups, row):
            y += [o] * n
            g += [lab] * n
    return pd.Series(y, name="outcome"), pd.Series(g, name="group")


# --- main.py: no API key for data_analysis --------------------------------------------

def test_run_cli_needs_no_api_key(monkeypatch):
    for var in main.PROVIDER_ENV_VARS.values():
        if var:
            monkeypatch.delenv(var, raising=False)
    cli = _cli()
    calls = []
    monkeypatch.setattr(cli, "run", lambda base_dir, **kw: calls.append(base_dir))
    main.run_cli(main.parse_args(["--mode", "data_analysis", "--provider", "deepseek"]))
    assert len(calls) == 1


# --- helpers ----------------------------------------------------------------------

def test_format_p():
    c = _c()
    assert c.format_p(0.0004) == "< 0.001"
    assert c.format_p(0.0493) == "0.049"


def test_label_prints_whole_floats_as_integers():
    c = _c()
    assert [c.label(v) for v in (1.0, np.float64(2.0), 2.5, True, np.int64(3))] == \
        ["1", "2", "2.5", "True", "3"]


def test_ordered_sorts_numbers_by_size():
    c = _c()
    assert c.ordered([np.int64(2), np.int64(10), np.int64(1)]) == [1, 2, 10]
    assert c.ordered(["b", "a"]) == ["a", "b"]


def test_fewer_than_three_values_is_not_normal():
    assert _c().check_normal([1.0, 2.0]) == (False, "fewer than 3 values")


def test_all_values_equal_is_not_normal():
    assert _c().check_normal([3.0, 3.0, 3.0, 3.0]) == (False, "all values equal")


# --- continuous outcome -------------------------------------------------------------

def test_welch_when_both_groups_normal():
    r = _c().compare(*_groups(A, B))
    assert r["test"] == "Welch t test"
    assert r["stat"] == pytest.approx(-6.5308454677, rel=1e-8)
    assert r["df"] == pytest.approx(12.0361139615, rel=1e-8)
    assert r["p"] == pytest.approx(2.76676e-05, rel=1e-3)


def test_mann_whitney_when_a_group_is_skewed():
    r = _c().compare(*_groups(A, SKEW))
    assert r["test"] == "Mann-Whitney U"
    assert r["stat"] == pytest.approx(48.0)
    assert r["p"] == pytest.approx(0.1022917247, rel=1e-8)


def test_anova_for_three_normal_groups():
    r = _c().compare(*_groups(A, B, C))
    assert r["test"] == "One-way ANOVA"
    assert r["stat"] == pytest.approx(26.3928884987, rel=1e-8)
    assert r["df"] == (2, 21)
    assert r["p"] == pytest.approx(1.8603e-06, rel=1e-3)


def test_kruskal_when_not_all_normal():
    r = _c().compare(*_groups(A, B, SKEW))
    assert r["test"] == "Kruskal-Wallis"
    assert r["stat"] == pytest.approx(8.9795206972, rel=1e-8)
    assert r["df"] == 2
    assert r["p"] == pytest.approx(0.0112233332, rel=1e-8)


def test_group_with_one_value_stops():
    c = _c()
    y = pd.Series([1.5, 2.5, 3.5, 4.5, 5.5], name="score")
    g = pd.Series(["A", "A", "A", "A", "B"], name="group")
    with pytest.raises(c.CompareError, match="fewer than 2 values"):
        c.compare(y, g)


def test_same_value_everywhere_stops():
    c = _c()
    y = pd.Series([2.5] * 6, name="score")
    g = pd.Series(["A", "A", "A", "B", "B", "B"], name="group")
    with pytest.raises(c.CompareError, match="same value in every row"):
        c.compare(y, g)


def test_group_column_must_be_categorical():
    c = _c()
    y = pd.Series(A + B, name="score")
    g = pd.Series([i + 0.25 for i in range(16)], name="height")
    with pytest.raises(c.CompareError, match="must be categorical"):
        c.compare(y, g)


def test_more_than_ten_groups_stops():
    c = _c()
    y = pd.Series([i + 0.5 for i in range(24)], name="score")
    g = pd.Series([f"G{i:02d}" for i in range(12)] * 2, name="ward")
    with pytest.raises(c.CompareError, match="12 groups"):
        c.compare(y, g)


def test_rows_with_missing_outcome_or_group_are_left_out():
    y = pd.Series([None] + A[1:] + B, name="score", dtype=float)
    g = pd.Series(["A"] * 8 + ["B"] * 7 + [None], name="group")
    r = _c().compare(y, g)
    assert (r["n_used"], r["n_left"]) == (14, 2)
    assert "(2 left out: outcome or group missing)" in "\n".join(r["lines"])


# --- categorical outcome ------------------------------------------------------------

def test_chi_square_2x3():
    r = _c().compare(*_from_table([[10, 12, 8], [14, 6, 10]], "ABC"))
    assert r["test"] == "Chi-square test"
    assert r["stat"] == pytest.approx(2.8888888889, rel=1e-8)
    assert r["p"] == pytest.approx(0.235877083, rel=1e-8)
    assert r["df"] == 2
    assert r["warning"] is None


def test_fisher_for_small_2x2():
    r = _c().compare(*_from_table([[3, 1], [1, 3]], "AB"))
    assert r["test"] == "Fisher's exact test"
    assert r["stat"] is None
    assert r["p"] == pytest.approx(0.4857142857, rel=1e-8)


def test_chi_square_2x2_uses_yates():
    r = _c().compare(*_from_table([[10, 20], [20, 10]], "AB"))
    assert r["test"] == "Chi-square test with Yates continuity correction"
    want = stats.chi2_contingency(np.array([[10, 20], [20, 10]]))
    assert r["p"] == pytest.approx(float(want[1]), rel=1e-10)


def test_small_expected_counts_in_larger_table_warn():
    r = _c().compare(*_from_table([[3, 1, 2], [1, 3, 0]], "ABC"))
    assert r["test"] == "Chi-square test"
    assert "may not be reliable" in r["warning"]
    assert r["warning"] in r["lines"]


def test_categorical_outcome_with_one_value_stops():
    c = _c()
    y = pd.Series(["pos"] * 4, name="outcome")
    g = pd.Series(["A", "A", "B", "B"], name="group")
    with pytest.raises(c.CompareError, match="only one value"):
        c.compare(y, g)


# --- printed lines ----------------------------------------------------------------

def test_continuous_lines_show_labels_and_summaries():
    text = "\n".join(_c().compare(*_groups(A, B))["lines"])
    assert "Comparison: score by group" in text
    assert "6.95" in text          # mean of B
    assert "5.25" in text          # Q1 of A
    assert "Normal?" in text
    assert "Result: t = -6.53, df = 12.04, p < 0.001" in text


def test_categorical_lines_show_counts_and_percent():
    text = "\n".join(_c().compare(*_from_table([[3, 1], [1, 3]], "AB"))["lines"])
    assert "3 (75.0%)" in text
    assert "Total" in text
    assert "Test: Fisher's exact test" in text


def test_numeric_codes_print_without_decimals():
    y = pd.Series(A + B + [5.0], name="score")
    g = pd.Series([0, 1] * 8 + [None], name="arm", dtype=float)
    r = _c().compare(y, g)
    assert r["groups"] == ["0", "1"]
    assert r["n_left"] == 1


# --- the analysis menu in run() -------------------------------------------------------

def _csv():
    rows = [f"{v},A" for v in A] + [f"{v},B" for v in B]
    return "score,group\n" + "\n".join(rows) + "\n"


def _run_cli(tmp_path, text, answers):
    d = tmp_path / "input" / "data_analysis"
    d.mkdir(parents=True)
    (d / "a.csv").write_text(text, encoding="utf-8")
    answers = list(answers)
    asked = []

    def fake_input(prompt):
        asked.append(prompt)
        if not answers:
            raise AssertionError(f"unexpected question: {prompt}")
        return answers.pop(0)
    lines = []
    _cli().run(tmp_path, say=lines.append, input_fn=fake_input, now=NOW)
    log = tmp_path / "reports" / "data_analysis" / "20261128_093000" / "run.log"
    return "\n".join(lines), asked, (log.read_text(encoding="utf-8") if log.exists() else "")


def test_menu_runs_a_comparison_and_logs_it(tmp_path):
    out, asked, log = _run_cli(tmp_path, _csv(), ["1", "1", "2", "0"])
    assert "Welch t test" in out and "Welch t test" in log
    assert sum(p.startswith("Analysis") for p in asked) == 2


def test_menu_enter_stops(tmp_path):
    out, asked, _ = _run_cli(tmp_path, _csv(), [""])
    assert len(asked) == 1 and asked[0].startswith("Analysis")
    assert "Comparison:" not in out


def test_menu_invalid_column_returns_to_menu(tmp_path):
    out, _, _ = _run_cli(tmp_path, _csv(), ["1", "9", "0"])
    assert "Not a valid column number: 9" in out


def test_menu_same_column_refused(tmp_path):
    out, _, _ = _run_cli(tmp_path, _csv(), ["1", "1", "1", "0"])
    assert "must be different" in out


def test_menu_shows_why_a_comparison_was_not_run(tmp_path):
    out, _, _ = _run_cli(tmp_path, _csv(), ["1", "2", "1", "0"])
    assert "Comparison not run" in out and "must be categorical" in out


def test_menu_invalid_choice(tmp_path):
    out, _, _ = _run_cli(tmp_path, _csv(), ["5", "0"])
    assert "Not a valid choice: 5" in out


def test_menu_never_shows_a_single_cell(tmp_path):
    text = ("name,weight,group\nZebedee Quill,123.456,A\nAnn Lee,80.5,A\n"
            "Bo Chan,70.25,B\nCy Wu,90.75,B\n")
    out, _, log = _run_cli(tmp_path, text, ["1", "2", "3", "0"])
    assert "Mann-Whitney U" in out
    for secret in ("Zebedee", "123.456"):
        assert secret not in out and secret not in log


# --- readme -------------------------------------------------------------------------

def test_readme_describes_the_comparison_rules():
    flat = " ".join(README.read_text(encoding="utf-8").split())
    for s in ("3.7 Comparison", "Welch t test", "Mann-Whitney U", "one-way ANOVA",
              "Kruskal-Wallis", "Fisher's exact test", "Yates continuity correction",
              "fewer than 3 values", f"p below {_c().ALPHA}"):
        assert s in flat, s
