"""Session 52 (cont. 3): finding words checked against the table.
Values are shaped like real reports but are not patient values."""
from pipelines.samd import report


def _r(test, value, unit, ref, status):
    return {"test": test, "value": value, "unit": unit, "ref": ref, "flag": "", "status": status}


LYM = _r("Lymphocytes (absolute) 淋巴細胞", "0.8", "x10e9/L", "1.0 - 3.2", "LOW")
WBC = _r("WBC 白血球", "5.0", "x10e9/L", "3.7 - 9.3", "normal")
HB1 = _r("Hemoglobin 血紅蛋白", "14.0", "g/dL", "13.5 - 17.3", "normal")
HB2 = _r("Haemoglobin 血紅素", "14.1", "g/dl", "13.5 - 18.0", "normal")
CA = _r("Calcium 鈣, 血清", "2.40", "mmol/L", "2.08 - 2.65", "normal")
PLT = _r("Platelet Count 血小板計數", "118", "x10e9/L", "160 - 420", "LOW")
GLU = _r("Glucose Fasting 血葡萄糖,空腹", "6.5", "mmol/L", "3.9 - 6.0", "HIGH")
ALB_L = _r("Albumin", "38", "g/L", "40 - 49", "LOW")
ALB_N = _r("Albumin 白蛋白", "44", "g/L", "32 - 50", "normal")
UGLU = _r("Glucose - Urine 糖", "NEGATIVE", "", "Negative", "normal")


def test_denied_lymphopenia_warns():
    # sentence shape from run 20261128_084253
    w = report.denied_blood_findings([LYM, WBC], "There is no significant leukocytosis or lymphopenia in the CBC.")
    assert len(w) == 1 and "Lymphocytes (absolute)" in w[0] and "WBC" not in w[0]


def test_denied_after_term_warns():
    assert len(report.denied_blood_findings([PLT], "Thrombocytopenia is absent.")) == 1


def test_no_symptoms_of_is_not_denial():
    assert report.denied_blood_findings([GLU], "The patient has no symptoms of hyperglycemia.") == []


def test_denied_normal_finding_quiet():
    assert report.denied_blood_findings([HB1], "There is no evidence of anemia.") == []


def test_no_mention_of_is_not_denial():
    assert report.denied_blood_findings([PLT], "There is no mention of thrombocytopenia in the notes.") == []


def test_but_breaks_denial():
    s = "No anaemia, but thrombocytopenia is present."
    assert report.denied_blood_findings([PLT, HB1], s) == []
    assert report.unsupported_findings([PLT, HB1], s) == []


def test_unsupported_hypercalcaemia_warns():
    # sentence shape from run 20261128_084253
    w = report.unsupported_findings([CA], "Parathyroid hormone level - if hypercalcemia persists.")
    assert len(w) == 1 and "hypercalcaemia" in w[0]


def test_unsupported_anaemia_warns():
    w = report.unsupported_findings([HB1, HB2], "The patient also has mild anaemia.")
    assert len(w) == 1 and "anaemia" in w[0]


def test_supported_finding_quiet():
    assert report.unsupported_findings([PLT], "Thrombocytopenia (platelets 118 x10^9/L) is present.") == []


def test_one_abnormal_date_supports():
    assert report.unsupported_findings([ALB_L, ALB_N], "Possible hypoalbuminaemia.") == []


def test_rule_out_is_not_a_claim():
    assert report.unsupported_findings([HB1], "Repeat CBC to rule out anaemia.") == []


def test_negated_is_not_a_claim():
    assert report.unsupported_findings([HB1], "There is no evidence of anemia.") == []


def test_no_rows_no_warning():
    assert report.unsupported_findings([], "Hyperkalaemia is present.") == []
    assert report.denied_blood_findings([], "No hyperkalaemia.") == []


def test_urine_rows_ignored():
    assert report.unsupported_findings([UGLU], "Hyperglycaemia is present.") == []


def test_unlikely_is_not_a_claim():
    assert report.unsupported_findings([HB1], "Anaemia is unlikely because haemoglobin is normal.") == []


def test_not_indicated_is_denial_not_claim():
    # sentence shape from run 20261120_182309
    glu = _r("Glucose Fasting", "5.6", "mmol/L", "3.9 - 6.0", "normal")
    s = "Hypoglycemia is not indicated by the results; fasting glucose is normal."
    assert report.unsupported_findings([glu], s) == []
    assert report.denied_blood_findings([glu], s) == []


def test_would_be_considered_if_is_not_a_claim():
    # sentence shape from run 20261120_170939
    s = "Iron deficiency anaemia \u2013 This would be considered if haemoglobin were low, but it is not."
    assert report.unsupported_findings([HB1], s) == []


def test_typical_description_is_not_a_claim():
    # sentence shape from run 20261120_170939
    s = ("Chronic disease anaemia \u2013 This typically presents with normocytic or microcytic "
         "anaemia and low serum iron with normal ferritin.")
    assert report.unsupported_findings([HB1], s) == []


def test_differential_label_is_not_a_claim():
    # sentence shape from run 20261120_170939
    s = "Haemolytic anaemia \u2013 This would show elevated LDH, indirect bilirubin and reticulocytosis."
    assert report.unsupported_findings([HB1], s) == []
    ca = _r("Calcium", "2.40", "mmol/L", "2.08 - 2.65", "normal")
    assert len(report.unsupported_findings([ca], "PTH level \u2013 If hypercalcemia persists.")) == 1
