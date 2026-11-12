"""Truth fixture and reference overrides must agree on N (Session 39).

sr_truth.yaml had Jensen N 25/18 (randomised) while the reference override
had 19/15 (completed treatment, the N behind posttreatment Table 3). The
scorer then marked a correct override WRONG. Rule: N = N analysed at the
reported timepoint. For every hand-checked study in both files, any N field
present in both must match.
"""
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
TRUTH = ROOT / "tests" / "fixtures" / "sr_truth.yaml"
OVERRIDES = ROOT / "reference" / "sr_cbt_fibromyalgia" / "study_overrides.yaml"
N_FIELDS = ("n_intervention", "n_control")


def _load(path):
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _override_entries():
    data = _load(OVERRIDES)
    return [v for v in data.values() if isinstance(v, dict) and v.get("first_author")]


def test_files_exist():
    assert TRUTH.is_file() and OVERRIDES.is_file()


def test_truth_n_matches_override_n_for_checked_studies():
    studies = _load(TRUTH)["studies"]
    compared = 0
    mismatches = []
    for entry in _override_entries():
        author = entry["first_author"]
        truth = studies.get(author)
        if not truth or not truth.get("checked"):
            continue
        if entry.get("year") is not None and truth.get("year") != entry.get("year"):
            continue
        for field in N_FIELDS:
            if field in entry and field in truth:
                compared += 1
                if int(truth[field]) != int(entry[field]):
                    mismatches.append(
                        f"{author} {field}: truth {truth[field]} vs override {entry[field]}"
                    )
    # Print the denominator so "clean" cannot mean "nothing compared".
    print(f"N fields compared: {compared}")
    assert compared > 0, "no N field compared; check file paths and keys"
    assert not mismatches, "; ".join(mismatches)
