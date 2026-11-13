# Session 39 (item 8, F8): the N extracted for an arm must appear in that
# arm's source quote when the quote carries candidate Ns. Real case: Ang 2010,
# quote "Week 6 change 15 13 ..." but run 20261112_222233 extracted N 17/15
# with no source_quote_warning.
from pipelines.sr.src.extraction.data_extractor import DataExtractor

ANG_Q = "Week 6 change\u2021     15      13      -20.2 \u00b1 23.9    -14.9 \u00b1 16.4"


def _check(primary, participants=None, **top):
    r = {"filename": "t.pdf", "primary_outcome": primary, **top}
    if participants is not None:
        r["participants"] = participants
    DataExtractor.__new__(DataExtractor)._flag_suspect_source_quotes(r)
    return r.get("source_quote_warning") or ""


def _ang():
    return {"mean_intervention": -20.2, "sd_intervention": 23.9,
            "mean_control": -14.9, "sd_control": 16.4,
            "source_quote_intervention": ANG_Q, "source_quote_control": ANG_Q}


def test_ang_wrong_n_warns():
    w = _check(_ang(), {"n_intervention": 17, "n_control": 15})
    assert "intervention N (17) does not appear" in w
    assert "quote has 13, 15" in w
    assert "control N" not in w          # 15 is in the quote


def test_ang_right_n_no_n_warning():
    w = _check(_ang(), {"n_intervention": 15, "n_control": 13})
    assert "N (" not in w


def test_n_read_from_top_level_when_no_participants():
    p = {"mean_intervention": 3.88, "sd_intervention": 1.05,
         "mean_control": 3.67, "sd_control": 0.75,
         "source_quote_intervention": "CBT (n = 24): 3.88 (1.05)",
         "source_quote_control": "Wait-list (n = 24): 3.67 (0.75)"}
    w = _check(p, None, n_intervention=30, n_control=24)
    assert "intervention N (30) does not appear" in w
    assert "control N" not in w


def test_scale_range_is_not_an_n():          # Jensen-style quote
    p = {"mean_intervention": 60.5, "sd_intervention": 4.0,
         "mean_control": 65.0, "sd_control": 2.7,
         "source_quote_intervention": "Average weekly FM pain (0\u2013100 VAS)  60.5 \u00b1 4.0",
         "source_quote_control": "Average weekly FM pain (0\u2013100 VAS)  65.0 \u00b1 2.7"}
    assert "N (" not in _check(p, {"n_intervention": 19, "n_control": 15})


def test_integer_mean_sd_cells_are_not_ns():  # Jensen Table 3 prints 49 (19)
    p = {"mean_intervention": 49, "sd_intervention": 19,
         "mean_control": 59, "sd_control": 26,
         "source_quote_intervention": "CBT 49 (19)",
         "source_quote_control": "Waiting list 59 (26)"}
    assert "N (" not in _check(p, {"n_intervention": 25, "n_control": 18})


def test_quote_without_ns_gives_no_n_warning():  # Lami-style quote
    p = {"mean_intervention": 4.2, "sd_intervention": 2.1,
         "mean_control": 5.1, "sd_control": 2.3,
         "source_quote_intervention": "CBT-IP group: mean = 4.2 (SD = 2.1) at post-treatment",
         "source_quote_control": "UMC group: mean = 5.1 (SD = 2.3) at post-treatment"}
    assert "N (" not in _check(p, {"n_intervention": 28, "n_control": 36})
