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
    # Session 38: Karlsson hand-checked (Table 2 p6, MPI-1 Pain severity).
    checked = sorted(a for a, s in truth["studies"].items() if s["checked"])
    assert checked == ["Jensen", "Karlsson", "Lami", "McCrae"] 


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
    # Session 38 (7k): Ang is unchecked now (NFR row, excluded by the reviewer);
    # mark a copy checked so the "wrong N, matching means" path stays covered.
    import copy
    t = copy.deepcopy(truth)
    t["studies"]["Ang"]["checked"] = True
    r = sc.score_row(_row("Ang", "17", "15", "-20.2", "23.9", "-14.9", "16.4"), t)
    assert r["fields"]["n_intervention"] == "WRONG"
    assert r["fields"]["n_control"] == "WRONG"
    assert r["fields"]["mean_intervention"] == "MATCH"
    assert r["fields"]["sd_control"] == "MATCH"


def test_empty_cell_is_missing(sc, truth):
    r = sc.score_row(_row("Jensen", "19", "15", "", "", "", ""), truth)
    assert r["fields"]["mean_intervention"] == "MISSING"
    assert r["fields"]["n_intervention"] == "WRONG"


def test_unchecked_and_unknown_studies_are_not_scored(sc, truth):
    # Session 38: Karlsson is now hand-checked, so mark a copy unchecked;
    # the not_checked path stays covered whatever the reviewer has checked.
    import copy
    t = copy.deepcopy(truth)
    t["studies"]["Karlsson"]["checked"] = False
    k = sc.score_row(_row("Karlsson", "24", "24", "3.88", "1.05", "3.67", "0.75"), t)
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
    # Session 38: Karlsson hand-checked (values match); Ang unchecked (7k, NFR row).
    assert "4 checked" in report and "1 fully correct" in report
    offenders = report.split("differ from the hand-checked truth:")[-1]
    assert "Karlsson" not in offenders and "Ang" not in offenders
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



# Session 38: the score is also saved as <run folder>/score.txt (it used to
# only print to the screen). Same text as the screen, replaced on every
# rerun, nothing written when the folder is not a run.

def _score(sc, folder, capsys):
    code = sc.main([str(folder), "--truth", str(TRUTH)])
    return code, capsys.readouterr().out


def test_score_is_saved_as_score_txt_in_run_folder(sc, tmp_path, capsys):
    folder = _run_folder(tmp_path, [_row("Lami", "28", "36", "7.35", "2.08", "7.4", "1.29")])
    _, out = _score(sc, folder, capsys)
    path = folder / "score.txt"
    assert path.exists(), "score.txt not written to the run folder"
    saved = path.read_text(encoding="utf-8")
    assert not path.read_bytes().startswith(b"\xef\xbb\xbf"), "score.txt has a BOM"
    assert saved.startswith("[SCORE] ")
    assert "Lami" in saved
    assert out == saved + f"[SCORE] saved {path}\n"


def test_rescore_replaces_score_txt(sc, tmp_path, capsys):
    folder = _run_folder(tmp_path, [_row("Lami", "28", "36", "7.35", "2.08", "7.4", "1.29")])
    _score(sc, folder, capsys)
    first = (folder / "score.txt").read_text(encoding="utf-8")
    _score(sc, folder, capsys)
    second = (folder / "score.txt").read_text(encoding="utf-8")
    assert second == first
    assert second.count("[SCORE] ") == 1, "rerun appended instead of replacing"


def test_not_a_run_folder_writes_no_score_txt(sc, tmp_path, capsys):
    code, out = _score(sc, tmp_path, capsys)   # empty folder, no data/results csv
    assert code == 2
    assert out.startswith("[SCORE] ")
    assert not (tmp_path / "score.txt").exists()



# Session 38 (7f): an override hides what the AI extracted. The AI's own value
# survives in extracted_data.csv override_fields as "field(old->new)"; the
# scorer shows it as separate "AI alone" lines and a separate count. The
# pooled result and the exit code do not change.

LAMI_ROW = ("Lami", "28", "36", "7.35", "2.08", "7.4", "1.29")
LAMI_OVR = ("n_intervention(38->28); n_control(41->36); mean_intervention(3.8->7.35); "
            "sd_intervention(2.1->2.08); mean_control(5.2->7.4); sd_control(2.3->1.29)")


def _report(sc, truth, folder):
    results = sc.score_run_folder(folder, truth)
    return results, sc.format_report(results)


def test_override_shows_ai_values_scored_against_truth(sc, truth, tmp_path):
    folder = _run_folder(tmp_path, [_row(*LAMI_ROW)], overrides={"Lami": LAMI_OVR})
    _, text = _report(sc, truth, folder)
    assert "Lami       POOLED     ALL MATCH" in text          # review result unchanged
    assert "AI alone: n_intervention WRONG (AI 38, truth 28)" in text
    assert "AI alone: mean_control WRONG (AI 5.2, truth 7.4)" in text


def test_absent_ai_value_is_missing_and_untouched_fields_count_as_ai(sc, truth, tmp_path):
    folder = _run_folder(tmp_path, [_row(*LAMI_ROW)],
                         overrides={"Lami": "first_author; year; sd_intervention(absent->2.08)"})
    _, text = _report(sc, truth, folder)
    assert "AI alone: sd_intervention MISSING (AI empty, truth 2.08)" in text
    assert "AI alone: n_intervention" not in text             # not overridden = AI's own value


def test_summary_counts_ai_alone_and_exit_code_unchanged(sc, truth, tmp_path):
    folder = _run_folder(tmp_path, [_row(*LAMI_ROW)], overrides={"Lami": LAMI_OVR})
    results, text = _report(sc, truth, folder)
    assert "SUMMARY: 1 checked, 1 fully correct, 0 wrong or missing AND POOLED." in text
    assert "AI alone: 1 checked, 0 fully correct" in text
    assert sc.exit_code(results) == 0


def test_ai_values_that_match_show_all_match(sc, truth, tmp_path):
    folder = _run_folder(tmp_path, [_row(*LAMI_ROW)],
                         overrides={"Lami": "n_intervention(28.0->28)"})
    _, text = _report(sc, truth, folder)
    assert "AI alone: ALL MATCH" in text
    assert "AI alone: 1 checked, 1 fully correct" in text


def test_no_override_prints_no_ai_lines(sc, truth, tmp_path):
    folder = _run_folder(tmp_path, [_row(*LAMI_ROW)])
    _, text = _report(sc, truth, folder)
    assert "AI alone" not in text
