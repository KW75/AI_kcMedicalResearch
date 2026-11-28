"""Session 52 (cont. 2): white-cell differential re-paired by position.
Values are shaped like real reports but are not patient values."""
import re

from pipelines.samd import report

WBC = "WBC 白血球 4.0 x10e9/L 3.7 - 9.3"
# names on the first five lines only (run shape 20261128_084253)
A = [WBC, "", "Differential",
     "Neutrophils 嗜中性細胞 72 % 38 - 76",
     "Lymphocytes 淋巴細胞 2.9 x10e9/L 1.8 - 6.2",
     "Monocytes 單核細胞 20 % 16 - 49",
     "Eosinophils 嗜酸性白細胞 0.8 x10e9/L 1.0 - 3.2",
     "Basophils 嗜鹼性白細胞 5 % 3 - 11",
     "0.2 x10e9/L 0.1 - 0.8",
     "2 < 7",
     "0.08 x10e9/L 0.02 - 0.50",
     "1 % < 2",
     "0.1 x10e9/L 0.0 - 0.2", ""]
# names on the % lines, absolute lines nameless (run shape 20261127_200428)
B = [WBC, "", "Differential",
     "Neutrophils 嗜中性細胞 72 % 38 - 76", "2.9 x10e9/L 1.8 - 6.2",
     "Lymphocytes 淋巴細胞 20 % 16 - 49", "0.8 x10e9/L 1.0 - 3.2",
     "Monocytes 單核細胞 5 % 3 - 11", "0.2 x10e9/L 0.1 - 0.8",
     "Eosinophils 嗜酸性白細胞 2 % < 7", "0.08 x10e9/L 0.02 - 0.50",
     "Basophils 嗜鹼性白細胞 1 % < 2", "0.1 x10e9/L 0.0 - 0.2", ""]
# absolute numbers lost (run shape 20261128_065727)
C = [WBC, "", "Differential",
     "Neutrophils 嗜中性細胞 72 % 38 - 76", "x10e9/L 1.8 - 6.2",
     "Lymphocytes 淋巴細胞 20 % 16 - 49", "x10e9/L 1.0 - 3.2",
     "Monocytes 單核細胞 5 % 3 - 11", "x10e9/L 0.1 - 0.8",
     "Eosinophils 嗜酸性白細胞 2 % < 7", "x10e9/L 0.02 - 0.50",
     "Basophils 嗜鹼性白細胞 1 % < 2", "x10e9/L 0.0 - 0.2", ""]
D = A[:8] + [""]          # first five values only (run shape 20261127_102001)
E = [s.replace("0.8 x10e9/L 1.0 - 3.2", "2.5 x10e9/L 1.0 - 3.2") for s in A]   # check fails
F = ["WBC 白血球數量 4.7 x 10^9/L 4.0 - 11.0",
     "Neutrophil 嗜中性白血球 60.0 % 40.0 - 75.0", "Lymphocyte 淋巴性白血球 28.0 % 20.0 - 45.0",
     "Monocyte 單核白血球 8.0 % 2.0 - 12.0", "Eosinophil 嗜酸性白血球 3.5 % 0.0 - 6.0",
     "Basophil 嗜鹼性白血球 0.5 % 0.0 - 2.0", ""]
CELL = re.compile(r"(?i)^(neutro|lympho|mono|eosino|baso)")


def _described(lines):
    return [("lab_2024.pdf", "transcription", "\n".join(lines))]


def _diff(lines):
    return [r for r in report.parse_results(_described(lines)) if CELL.match(r["test"])]


def _names(rows):
    return [re.sub(r"[^\x20-\x7e]+", "", r["test"]).strip() for r in rows]


def _abs_lymph(rows):
    return [r for r in rows if r["test"].startswith("Lymphocytes (absolute)")]


ORDER = ["Neutrophils", "Neutrophils (absolute)", "Lymphocytes", "Lymphocytes (absolute)",
         "Monocytes", "Monocytes (absolute)", "Eosinophils", "Eosinophils (absolute)",
         "Basophils", "Basophils (absolute)"]


def test_repair_names_on_first_lines():
    rows = _abs_lymph(_diff(A))
    assert len(rows) == 1 and rows[0]["value"] == "0.8" and rows[0]["status"] == "LOW"


def test_repair_nameless_absolute_lines():
    rows = _abs_lymph(_diff(B))
    assert len(rows) == 1 and rows[0]["value"] == "0.8" and rows[0]["status"] == "LOW"


def test_repair_gives_ten_rows_in_order():
    assert _names(_diff(A)) == ORDER


def test_repair_keeps_chinese_label():
    assert "淋巴細胞" in _abs_lymph(_diff(A))[0]["test"]


def test_partial_block_repairs_full_pairs():
    assert _names(_diff(D)) == ORDER[:5]
    w = report.differential_problems(_described(D))
    assert len(w) == 1 and "5 of 10" in w[0]


def test_missing_absolute_values_warn():
    w = report.differential_problems(_described(C))
    assert len(w) == 1 and "missing" in w[0]


def test_failed_check_keeps_rows_and_warns():
    assert report.parse_results(_described(E)) == report._parse_results_before_s52c2(_described(E))
    w = report.differential_problems(_described(E))
    assert len(w) == 1 and "mislabelled" in w[0]


def test_clean_block_no_warning():
    assert report.differential_problems(_described(B)) == []


def test_absolute_word_alone_does_not_name():
    row = {"test": "Lymphocytes (absolute) 淋巴細胞", "value": "0.8", "unit": "x10e9/L",
           "ref": "1.0 - 3.2", "flag": "", "status": "LOW"}
    w = report.unmentioned_abnormal([row], "The absolute neutrophil count is normal.")
    assert w and "Lymphocytes (absolute)" in w[0]


def test_lymphocytes_word_names_absolute_row():
    row = {"test": "Lymphocytes (absolute) 淋巴細胞", "value": "0.8", "unit": "x10e9/L",
           "ref": "1.0 - 3.2", "flag": "", "status": "LOW"}
    assert report.unmentioned_abnormal([row], "Lymphocytes are low at 0.8 x10e9/L.") == []


def test_percent_only_block_unchanged():
    assert _names(_diff(F)) == ["Neutrophil", "Lymphocyte", "Monocyte", "Eosinophil", "Basophil"]


def test_no_wbc_no_repair():
    assert not any("(absolute)" in n for n in _names(_diff(A[1:])))


def test_missing_layout_rows_unchanged():
    assert _names(_diff(C)) == ["Neutrophils", "Lymphocytes", "Monocytes", "Eosinophils", "Basophils"]


BASO1 = {"test": "Basophils", "value": "1", "unit": "%", "ref": "<2", "flag": "", "status": "normal"}


def _in_range(rows, s):
    return [w for w in report.check_answer(rows, s, s) if "in-range result abnormal" in w]


def test_dipstick_grade_is_not_a_value():
    # sentence shape from run 20261127_173019
    s = ("The most likely diagnosis is CKD, based on the persistent elevation of serum urea "
         "(9.0 mmol/L), elevated creatinine (104 umol/L) and mild proteinuria (1+ protein in urine).")
    assert _in_range([BASO1], s) == []


def test_real_one_percent_claim_still_warns():
    assert _in_range([BASO1], "Basophils are elevated at 1 %.")
