"""Session 51 (cont. 19): 'in-range result called abnormal' is judged per clause
(split at ';', but, however, although, though, whereas). For a row whose value is 10,
the '10' of a power-of-ten unit is not that value; 'low' for a '<X' range is not an
abnormal claim."""
from pipelines.samd import report


def _row(test, value, unit, ref, status, flag=""):
    return {"test": test, "value": value, "unit": unit, "ref": ref, "flag": flag,
            "status": status,
            "source": "CKW_Blood test_2024.02.19_TFT,CPK,VitD,Tumour markers.jpg"}


AFP = _row("AFP 甲種胎兒球蛋白", "2.24", "ng/ml", "<15.0", "normal")
SCC = _row("SCC 鱗狀細胞癌瘤抗原", "2.94", "ng/ml", "<=2.5", "HIGH", "H")
CRP = _row("CRP", "0.8", "mg/L", "<5.0", "normal")
GGT = _row("GGT", "10", "U/L", "10 - 71", "normal")
WBC = _row("WBC", "4.9", "x10e9/L", "3.7 - 9.3", "normal")
REAL = ("**Early-stage malignancy**: Supported by elevated SCC (2.94 ng/ml) and mild "
        "elevation in AFP (2.24 ng/ml), but all tumour markers remain within "
        "non-cancerous ranges.")


def _inrange(rows, answer, name):
    return [w for w in report.check_answer(rows, answer, answer)
            if "in-range result abnormal" in w and name in w]


def _afp(answer):
    return _inrange([AFP, SCC], answer, "AFP")


def test_real_afp_sentence_warns():
    out = _afp(REAL)
    assert len(out) == 1 and "within non-cancerous" in out[0]


def test_elevated_but_within_warns():
    assert len(_afp("AFP 2.24 ng/ml is elevated, but within the normal range.")) == 1


def test_semicolon_clause_warns():
    assert len(_afp("AFP 2.24 ng/ml is raised; other tumour markers are normal.")) == 1


def test_abnormal_word_in_other_clause_no_warning():
    assert _afp("AFP 2.24 ng/ml was measured, but SCC is elevated.") == []


def test_normal_clause_still_quiet():
    assert _afp("AFP 2.24 ng/ml is within normal range, but SCC is elevated.") == []


def test_plain_elevated_still_warns():
    assert len(_afp("Elevated AFP (2.24 ng/ml).")) == 1


def test_negated_still_quiet():
    assert _afp("AFP 2.24 ng/ml is not elevated, but SCC is.") == []


def test_low_for_upper_limit_range_is_not_abnormal():
    answer = ("- There are no signs of infection or inflammation: WBC count is normal at "
              "4.9 x10\u2079/L; CRP is low at 0.8 mg/L (<5.0); and the differential shows "
              "no abnormality.")
    assert _inrange([CRP], answer, "CRP") == []


def test_power_of_ten_is_not_a_value():
    answer = ("- The patient has mild anemia of chronic disease: hemoglobin is normal at "
              "13.8 g/dL but RBC count is slightly low (4.45 \u00d7 10\u00b9\u00b2/L), with a "
              "borderline ESR of 69 mm/hr, which may reflect ongoing inflammation.")
    assert _inrange([GGT], answer, "GGT") == []


def test_power_of_ten_unit_still_names_its_value():
    assert len(_inrange([WBC], "WBC 4.9 x10e9/L is low.", "WBC")) == 1
