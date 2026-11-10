# tests/test_sr_score_run.py
"""F7 (Session 37): score a real SR run against reviewer hand-checked values.

scripts/sr_score_run.py reads a run folder's meta_analysis_results.csv (the
values actually pooled, after overrides) and compares each study with
tests/fixtures/sr_truth.yaml. Tests use small synthetic run folders - real
run folders are not in git.
"""
import csv
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "sr_score_run.py"
TRUTH = ROOT / "tests" / "fixtures" / "sr_truth.yaml"

RESULT_FIELDS = ["run_id", "first_author", "year", "filename",
                 "n_intervention", "n_control", "mean_intervention",
                 "sd_intervention", "mean_control", "sd_control",
                 "included_in_meta", "skip_reason", "nondet_flag"]


@pytest.fixture(scope="module")
def sc():
    assert SCRIPT.exists(), "scripts/sr_score_run.py missing (F7)"
    spec = importlib.util.spec_from_file_location("sr_score_run", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def truth(sc):
    return sc.load_truth(TRUTH)


def _row(author, ni, nc, mi, si, mc, sdc, included="True", skip=""):
    return {"run_id": "t", "first_author": author, "year": "",
            "filename": f"{author}.pdf",
            "n_intervention": ni, "n_control": nc,
            "mean_intervention": mi, "sd_intervention": si,
            "mean_control": mc, "sd_control": sdc,
            "included_in_meta": included, "skip_reason": skip,
            "nondet_flag": "unanimous"}


def _run_folder(tmp_path, rows, overrides=None):
    res = tmp_path / "data" / "results" / "meta_analysis_results.csv"
    res.parent.mkdir(parents=True)
    with open(res, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=RESULT_FIELDS)
        w.writeheader()
        w.writerows(rows)
    if overrides:
        ext = tmp_path / "data" / "extracted" / "extracted_data.csv"
        ext.parent.mkdir(parents=True)
        with open(ext, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["study_metadata.first_author",
                                              "override_fields"])
            w.writeheader()
            w.writerows({"study_metadata.first_author": a, "override_fields": o}
                        for a, o in overrides.items())
    return tmp_path


def test_truth_file_has_four_checked_studies(truth):
    checked = sorted(a for a, s in truth["studies"].items() if s["checked"])
    assert checked == ["Ang", "Jensen", "Lami", "McCrae"]


def test_exact_values_match(sc, truth):
    r = sc.score_row(_row("Lami", "28", "36", "7.35", "2.08", "7.4", "1.29"), truth)
    assert r["status"] == "scored"
    assert set(r["fields"].values()) == {"MATCH"}


def test_within_tolerance_matches_and_outside_is_wrong(sc, truth):
    r = sc.score_row(_row("Lami", "28", "36", "7.4", "2.08", "7.4", "1.29"), truth)
    assert r["fields"]["mean_intervention"] == "MATCH"      # 0.05 off, tolerance 0.1
    r = sc.score_row(_row("Lami", "38", "41", "4.8", "2.1", "6.2", "2.3"), truth)
    assert r["fields"]["mean_intervention"] == "WRONG"
    assert r["fields"]["mean_control"] == "WRONG"
    assert r["fields"]["n_intervention"] == "WRONG"


def test_ang_wrong_n_is_caught_while_means_match(sc, truth):
    r = sc.score_row(_row("Ang", "17", "15", "-20.2", "23.9", "-14.9", "16.4"), truth)
    assert r["fields"]["n_intervention"] == "WRONG"
    assert r["fields"]["n_control"] == "WRONG"
    assert r["fields"]["mean_intervention"] == "MATCH"
    assert r["fields"]["sd_control"] == "MATCH"


def test_empty_cell_is_missing(sc, truth):
    r = sc.score_row(_row("Jensen", "19", "15", "", "", "", ""), truth)
    assert r["fields"]["mean_intervention"] == "MISSING"
    assert r["fields"]["n_intervention"] == "WRONG"


def test_unchecked_and_unknown_studies_are_not_scored(sc, truth):
    k = sc.score_row(_row("Karlsson", "24", "24", "3.88", "1.05", "3.67", "0.75"), truth)
    assert k["status"] == "not_checked"
    u = sc.score_row(_row("Nobody", "1", "1", "1", "1", "1", "1"), truth)
    assert u["status"] == "no_truth"


def test_baseline_run_flags_wrong_pooled_studies(sc, truth, tmp_path):
    # values pooled in the real baseline 20261110_120707 (override OFF)
    folder = _run_folder(tmp_path, [
        _row("Ang", "17", "15", "-20.2", "23.9", "-14.9", "16.4"),
        _row("Jensen", "19", "15", "45.6", "20.1", "57.8", "21.9"),
        _row("Lami", "38", "41", "4.8", "2.1", "6.2", "2.3"),
        _row("Karlsson", "24", "24", "3.88", "1.05", "3.67", "0.75"),
        _row("McCrae", "37", "37", "47.14", "2.36", "52.67", "",
             included="False", skip="excluded"),
    ])
    results = sc.score_run_folder(folder, truth)
    by = {r["author"]: r for r in results}
    assert by["Jensen"]["included_in_meta"] is True
    assert by["McCrae"]["included_in_meta"] is False
    report = sc.format_report(results)
    assert "WRONG" in report
    assert "4 checked" in report and "0 fully correct" in report
    assert sc.exit_code(results) == 1


def test_override_is_reported(sc, truth, tmp_path):
    folder = _run_folder(
        tmp_path, [_row("Lami", "28", "36", "7.35", "2.08", "7.4", "1.29")],
        overrides={"Lami": "mean_intervention(4.2->7.35)"})
    results = sc.score_run_folder(folder, truth)
    assert results[0]["override"] is True
    assert "override" in sc.format_report(results).lower()


def test_correct_run_exits_zero(sc, truth, tmp_path):
    # a wrong-or-right study that was NOT pooled never fails the run
    folder = _run_folder(tmp_path, [
        _row("Ang", "15", "13", "-20.2", "23.9", "-14.9", "16.4"),
        _row("Lami", "28", "36", "7.35", "2.08", "7.4", "1.29"),
        _row("Jensen", "19", "15", "45.6", "20.1", "57.8", "21.9",
             included="False", skip="needs review: runs disagree"),
    ])
    results = sc.score_run_folder(folder, truth)
    assert sc.exit_code(results) == 0
