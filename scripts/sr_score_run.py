#!/usr/bin/env python
"""F7 (Session 37): score a real SR run against reviewer hand-checked values.

Usage:
    python scripts/sr_score_run.py 20261110_120707
    python scripts/sr_score_run.py "reports/sr/20260901_164801_without override"

Reads <run>/data/results/meta_analysis_results.csv (the values actually
pooled, after study_overrides) and compares each study with
tests/fixtures/sr_truth.yaml. Exit 1 if any hand-checked study was POOLED
with a wrong or missing value; 0 otherwise; 2 if the folder is not a run.
A MATCH means "equals the reviewer's reading" for these papers only.
The report is also saved as <run>/score.txt (replaced on every rerun).
"""
import argparse
import csv
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TRUTH = ROOT / "tests" / "fixtures" / "sr_truth.yaml"
FIELDS = ("n_intervention", "n_control", "mean_intervention",
          "sd_intervention", "mean_control", "sd_control")
_EMPTY = ("", "none", "nan", "null")


def load_truth(path=DEFAULT_TRUTH):
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    data.setdefault("tolerance", 0.1)
    data.setdefault("studies", {})
    return data


def _num(value):
    s = str(value if value is not None else "").strip()
    if s.lower() in _EMPTY:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _truthy(value):
    return str(value).strip().lower() in ("true", "1", "yes")


def _find_truth(author, truth):
    a = str(author or "").strip().casefold()
    for name, entry in truth["studies"].items():
        if name.casefold() == a:
            return name, entry
    return None, None


def score_row(row, truth):
    """Score one meta_analysis_results.csv row.

    status: "scored" | "not_checked" | "no_truth"
    fields: {field: "MATCH" | "WRONG" | "MISSING"} (scored rows only)
    """
    author = row.get("first_author") or "?"
    name, entry = _find_truth(author, truth)
    out = {"author": name or author,
           "included_in_meta": _truthy(row.get("included_in_meta")),
           "skip_reason": row.get("skip_reason") or "",
           "fields": {}, "values": {}, "override": False}
    if entry is None:
        out["status"] = "no_truth"
        return out
    if not entry.get("checked"):
        out["status"] = "not_checked"
        out["note"] = entry.get("note", "")
        return out
    tol = float(truth.get("tolerance", 0.1))
    for f in FIELDS:
        want = entry.get(f)
        if want is None:
            continue
        got = _num(row.get(f))
        out["values"][f] = (got, float(want))
        if got is None:
            out["fields"][f] = "MISSING"
        elif abs(got - float(want)) <= tol + 1e-9:
            out["fields"][f] = "MATCH"
        else:
            out["fields"][f] = "WRONG"
    out["status"] = "scored"
    return out


def _overridden_authors(folder):
    ext = Path(folder) / "data" / "extracted" / "extracted_data.csv"
    if not ext.exists():
        return set()
    names = set()
    with open(ext, newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            if str(r.get("override_fields") or "").strip():
                a = r.get("study_metadata.first_author") or r.get("first_author") or ""
                names.add(a.strip().casefold())
    return names


def score_run_folder(folder, truth):
    res = Path(folder) / "data" / "results" / "meta_analysis_results.csv"
    if not res.exists():
        raise FileNotFoundError(f"{res} not found - is this an SR run folder?")
    overridden = _overridden_authors(folder)
    with open(res, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    results = []
    for row in rows:
        r = score_row(row, truth)
        r["override"] = str(row.get("first_author") or "").strip().casefold() in overridden
        results.append(r)
    return results


def _fully_correct(r):
    return (r["status"] == "scored" and bool(r["fields"])
            and all(v == "MATCH" for v in r["fields"].values()))


def _fmt(v):
    return "empty" if v is None else f"{v:g}"


def format_report(results):
    lines = []
    pad = " " * 22
    for r in results:
        pooled = "POOLED" if r["included_in_meta"] else "not pooled"
        head = f"{r['author']:<10} {pooled:<10} "
        if r["status"] == "no_truth":
            lines.append(head + "no truth entry - not scored")
        elif r["status"] == "not_checked":
            lines.append((head + "not hand-checked - not scored. " + r.get("note", "")).rstrip())
        else:
            bad = [f"{f} {s} (run {_fmt(r['values'][f][0])}, truth {_fmt(r['values'][f][1])})"
                   for f, s in r["fields"].items() if s != "MATCH"]
            lines.append(head + ("ALL MATCH" if not bad else bad[0]))
            lines.extend(pad + b for b in bad[1:])
        if r.get("override"):
            lines.append(pad + "values from study_overrides.yaml (manual override) - "
                               "this scores the reviewer, not the model")
        if not r["included_in_meta"] and r.get("skip_reason"):
            lines.append(pad + "skip_reason: " + r["skip_reason"])
    checked = [r for r in results if r["status"] == "scored"]
    ok = [r for r in checked if _fully_correct(r)]
    bad_pooled = [r for r in checked if r["included_in_meta"] and not _fully_correct(r)]
    lines.append("")
    lines.append(f"SUMMARY: {len(checked)} checked, {len(ok)} fully correct, "
                 f"{len(bad_pooled)} wrong or missing AND POOLED.")
    if bad_pooled:
        lines.append("The pooled estimate uses values that differ from the "
                     "hand-checked truth: " + ", ".join(r["author"] for r in bad_pooled))
    return "\n".join(lines)


def exit_code(results):
    """1 if a hand-checked study was pooled with a wrong/missing value."""
    return 1 if any(r["status"] == "scored" and r["included_in_meta"]
                    and not _fully_correct(r) for r in results) else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Score an SR run against sr_truth.yaml (F7).")
    ap.add_argument("run", help="run folder, or a run id under reports/sr")
    ap.add_argument("--truth", default=str(DEFAULT_TRUTH))
    a = ap.parse_args(argv)
    folder = Path(a.run)
    if not folder.exists():
        folder = ROOT / "reports" / "sr" / a.run
    truth = load_truth(a.truth)
    try:
        results = score_run_folder(folder, truth)
    except FileNotFoundError as e:
        print(f"[SCORE] {e}")
        return 2
    text = (f"[SCORE] {folder.name} vs {Path(a.truth).name} (tolerance {truth['tolerance']})\n"
            + format_report(results) + "\n")
    print(text, end="")
    # Session 38: also keep the score with the run (UTF-8, no BOM, LF);
    # a rerun replaces the file.
    path = folder / "score.txt"
    path.write_bytes(text.encode("utf-8"))
    print(f"[SCORE] saved {path}")
    return exit_code(results)


if __name__ == "__main__":
    sys.exit(main())
