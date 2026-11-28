"""Data analysis B3: Comparison - one outcome across the groups of one column.

Every number comes from scipy / numpy; no AI model is used. The test is picked
by fixed rules (Readme/readme_data_analysis_pipeline.txt, section 3.7).
Printed: group labels (only from columns with at most CATEGORICAL_MAX_LEVELS
groups) and summaries per group; never a single cell value.
Works on scipy 1.13.1 (CI pins) and newer (s53_look4): Shapiro-Wilk is only
called with 3 or more values that are not all equal (1.13.1 raises below 3),
and Fisher's exact test only on 2 x 2 tables (1.13.1 has no larger tables).
No category dtype is used (pandas 2.2.2 warns about observed=False).
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
from scipy import stats

from .table import CATEGORICAL_MAX_LEVELS, describe_column

ALPHA = 0.05        # Shapiro-Wilk: p below this = does not look normal
MIN_EXPECTED = 5    # chi-square: expected counts below this are small
LABEL_WIDTH = 20


class CompareError(Exception):
    """The comparison cannot be run; the message says why."""


def format_p(p) -> str:
    """p below 0.001 as '< 0.001', else three decimals."""
    if p is None or math.isnan(float(p)):
        return "not available"
    p = float(p)
    return "< 0.001" if p < 0.001 else f"{p:.3f}"


def fmt(x) -> str:
    """A summary number: two decimals, or three significant digits below 1."""
    x = float(x)
    if math.isnan(x):
        return "-"
    if x == 0 or abs(x) >= 1:
        return f"{x:.2f}"
    return f"{x:.3g}"


def label(v) -> str:
    """A group or outcome value as printed; whole floats (1.0) print as 1."""
    if isinstance(v, (bool, np.bool_)):
        return str(bool(v))
    if isinstance(v, (int, np.integer)):
        return str(int(v))
    if isinstance(v, (float, np.floating)) and float(v).is_integer():
        return str(int(v))
    s = str(v)
    return s if len(s) <= LABEL_WIDTH else s[:LABEL_WIDTH - 3] + "..."


def ordered(values) -> list:
    """Numbers by size, text alphabetically (not '1', '10', '2')."""
    values = list(values)
    try:
        return sorted(values)
    except TypeError:
        return sorted(values, key=str)


def check_normal(values):
    """(looks normal?, reason) for one group, by Shapiro-Wilk."""
    x = np.asarray(values, dtype=float)
    if len(x) < 3:
        return False, "fewer than 3 values"
    if np.ptp(x) == 0:
        return False, "all values equal"
    p = float(stats.shapiro(x)[1])
    return p >= ALPHA, f"Shapiro-Wilk p = {format_p(p)}"


def _grid(header, rows, left=(0,)):
    table = [header] + rows
    w = [max(len(str(r[i])) for r in table) for i in range(len(header))]
    lines = []
    for r in table:
        cells = [str(c).ljust(w[i]) if i in left else str(c).rjust(w[i])
                 for i, c in enumerate(r)]
        lines.append(("  " + "  ".join(cells)).rstrip())
    return lines


def _result(stat_name, stat, df, p) -> str:
    parts = []
    if stat_name:
        parts.append(f"{stat_name} = {fmt(stat)}")
    if df is not None:
        if isinstance(df, tuple):
            parts.append("df = " + ", ".join(str(d) for d in df))
        elif isinstance(df, float):
            parts.append(f"df = {fmt(df)}")
        else:
            parts.append(f"df = {df}")
    ps = format_p(p)
    parts.append(f"p {ps}" if ps.startswith("<") else f"p = {ps}")
    return ", ".join(parts)


def _continuous(y, g, levels) -> dict:
    data = [(lv, y[(g == lv).to_numpy()].astype(float).to_numpy()) for lv in levels]
    for lv, x in data:
        if len(x) < 2:
            raise CompareError(f"group {label(lv)} has fewer than 2 values; "
                               "the test needs at least 2 per group.")
    xs = [x for _, x in data]
    if np.ptp(np.concatenate(xs)) == 0:
        raise CompareError("the outcome has the same value in every row used; "
                           "nothing to compare.")
    checks = [check_normal(x) for x in xs]
    all_normal = all(ok for ok, _ in checks)
    k = len(xs)
    if k == 2 and all_normal:
        r = stats.ttest_ind(xs[0], xs[1], equal_var=False)
        test, sname, stat, df = "Welch t test", "t", float(r.statistic), float(r.df)
    elif k == 2:
        r = stats.mannwhitneyu(xs[0], xs[1], alternative="two-sided")
        test, sname, stat, df = "Mann-Whitney U", "U", float(r.statistic), None
    elif all_normal:
        r = stats.f_oneway(*xs)
        n = sum(len(x) for x in xs)
        test, sname, stat, df = "One-way ANOVA", "F", float(r.statistic), (k - 1, n - k)
    else:
        r = stats.kruskal(*xs)
        test, sname, stat, df = "Kruskal-Wallis", "H", float(r.statistic), k - 1
    p = float(r.pvalue)
    why = (f"every group looks normal (Shapiro-Wilk p >= {ALPHA})" if all_normal
           else "at least one group does not look normal")
    rows = []
    for (lv, x), (ok, reason) in zip(data, checks):
        q1, med, q3 = (float(v) for v in np.percentile(x, [25, 50, 75]))
        rows.append([label(lv), str(len(x)), fmt(x.mean()), fmt(x.std(ddof=1)), fmt(med),
                     f"{fmt(q1)} - {fmt(q3)}", ("yes" if ok else "no") + f" ({reason})"])
    lines = _grid(["Group", "n", "Mean", "SD", "Median", "IQR (Q1 - Q3)", "Normal?"],
                  rows, left=(0, 6))
    lines += ["", f"Test: {test} - {why}", "Result: " + _result(sname, stat, df, p)]
    return {"test": test, "why": why, "stat_name": sname, "stat": stat, "df": df,
            "p": p, "warning": None, "lines": lines}


def _categorical(y, g, levels, yname) -> dict:
    outs = ordered(y.unique())
    if len(outs) < 2:
        raise CompareError(f"{yname} has only one value in the rows used; nothing to compare.")
    if len(outs) > CATEGORICAL_MAX_LEVELS:
        raise CompareError(f"{yname} has {len(outs)} values; a categorical outcome may "
                           f"have at most {CATEGORICAL_MAX_LEVELS}.")
    table = np.array([[int(((y == o) & (g == lv)).sum()) for lv in levels] for o in outs])
    expected = stats.contingency.expected_freq(table)
    small = int((expected < MIN_EXPECTED).sum())
    warning = None
    if table.shape == (2, 2) and small:
        p = float(stats.fisher_exact(table)[1])
        test, sname, stat, df = "Fisher's exact test", None, None, None
        why = f"2 x 2 table with an expected count below {MIN_EXPECTED}"
    else:
        r = stats.chi2_contingency(table)
        stat, p, df = float(r[0]), float(r[1]), int(r[2])
        sname = "chi-square"
        test = "Chi-square test" + (" with Yates continuity correction"
                                    if table.shape == (2, 2) else "")
        if small:
            why = f"{small} of {table.size} expected counts below {MIN_EXPECTED}"
            warning = (f"Warning: {small} of {table.size} cells have an expected count below "
                       f"{MIN_EXPECTED}, so the chi-square p value may not be reliable. "
                       "Fisher's exact test is only used for 2 x 2 tables; consider merging "
                       "groups or outcome values.")
        else:
            why = f"all expected counts are {MIN_EXPECTED} or more"
    totals = table.sum(axis=0)
    rows = [[label(o)] + [f"{n} ({n / t * 100:.1f}%)" if t else "0"
                          for n, t in zip(row, totals)]
            for o, row in zip(outs, table)]
    rows.append(["Total"] + [str(t) for t in totals])
    lines = _grid([label(yname)] + [label(lv) for lv in levels], rows)
    lines += ["", f"Test: {test} - {why}", "Result: " + _result(sname, stat, df, p)]
    if warning:
        lines.append(warning)
    return {"test": test, "why": why, "stat_name": sname, "stat": stat, "df": df,
            "p": p, "warning": warning, "lines": lines}


def compare(y: pd.Series, g: pd.Series) -> dict:
    """Compare outcome y across the groups of column g; the lines say what was done."""
    y = y.reset_index(drop=True)
    g = g.reset_index(drop=True)
    yname, gname = str(y.name), str(g.name)
    gk = describe_column(g)["kind"]
    if gk != "categorical":
        raise CompareError(f"the group column must be categorical; {gname} is {gk}.")
    yk = describe_column(y)["kind"]
    if yk not in ("continuous", "categorical"):
        raise CompareError(f"the outcome must be continuous or categorical; {yname} is {yk}.")
    mask = (y.notna() & g.notna()).to_numpy()
    y_used = y[mask].reset_index(drop=True)
    g_used = g[mask].reset_index(drop=True)
    n_all, n_used = int(len(y)), int(mask.sum())
    levels = ordered(g_used.unique())
    if len(levels) < 2:
        raise CompareError(f"{gname} has fewer than 2 groups in the rows used.")
    if len(levels) > CATEGORICAL_MAX_LEVELS:
        raise CompareError(f"{gname} has {len(levels)} groups; at most "
                           f"{CATEGORICAL_MAX_LEVELS} can be compared.")
    if yk == "continuous":
        res = _continuous(y_used, g_used, levels)
    else:
        res = _categorical(y_used, g_used, levels, yname)
    left = n_all - n_used
    used = f"Rows used: {n_used} of {n_all}"
    if left:
        used += f" ({left} left out: outcome or group missing)"
    res["lines"] = [f"Comparison: {yname} by {gname}", used, f"Outcome: {yk}", ""] + res["lines"]
    res.update(n_used=n_used, n_left=left, groups=[label(v) for v in levels])
    return res
