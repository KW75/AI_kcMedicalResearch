"""Session 51 (cont. 20): band-name check - the answer names a band the value
is not in ('35.9 ng/ml ... in the "insufficient" range' with 35.9 in Enough 30-100)."""
from pathlib import Path

from pipelines.samd import report

CLI = Path(__file__).resolve().parents[1] / "SOURCE_CODE" / "pipelines" / "samd" / "cli.py"


def _cli_text():
    return CLI.read_text(encoding="utf-8")


def _row(test, value, unit, ref, flag=""):
    return {"test": test, "value": value, "unit": unit, "ref": ref, "flag": flag,
            "status": "see bands",
            "source": "CKW_Blood test_2024.02.19_TFT,CPK,VitD,Tumour markers.jpg"}


VITD = _row("Vitamin D, 25-Hydroxy維他命D", "35.9", "ng/ml",
            "Lack of Vit-D <10; Insufficiency 10-30; Enough 30-100 (value in band); "
            "Toxicosis >100")
VITD_LOW = _row("Vitamin D, 25-Hydroxy維他命D", "20.1", "ng/ml",
                "Lack of Vit-D <10; Insufficiency 10-30 (value in band); Enough 30-100; "
                "Toxicosis >100")
CPK = _row("CPK 肌酸磷酸酶", "248", "IU/l", "Female 29-168; Male 30-200", "H")
CEA = _row("CEA 癌胚抗原", "2.28", "ng/ml",
           "Non-smoker < 5.0 (value in band); Smoker < 10.0 (value in band)")
REAL = ('5. **Vitamin D insufficiency**: Supported by vitamin D level of 35.9 ng/ml '
        '(in the "insufficient" range per source, which defines <10 as deficiency, '
        '10\u201330 as insufficient, and >30 as sufficient).')


def test_real_sentence_warns():
    out = report.band_name_mismatch([VITD], REAL)
    assert len(out) == 1 and '"Enough"' in out[0] and "insufficien" in out[0]


def test_definitions_only_no_warning():
    answer = ("Vitamin D 35.9 ng/ml (source defines <10 as deficiency, 10\u201330 as "
              "insufficient, >30 as sufficient).")
    assert report.band_name_mismatch([VITD], answer) == []


def test_correct_band_no_warning():
    assert report.band_name_mismatch([VITD], "Vitamin D 35.9 ng/ml is sufficient.") == []


def test_negated_no_warning():
    assert report.band_name_mismatch([VITD], "Vitamin D 35.9 ng/ml is not insufficient.") == []


def test_deficiency_word_warns():
    out = report.band_name_mismatch([VITD], "Vitamin D 35.9 ng/ml indicates deficiency.")
    assert len(out) == 1 and "deficiency" in out[0]


def test_insufficient_value_named_insufficient_no_warning():
    assert report.band_name_mismatch([VITD_LOW], "Vitamin D 20.1 ng/ml is insufficient.") == []


def test_insufficient_value_called_sufficient_warns():
    out = report.band_name_mismatch([VITD_LOW], "Vitamin D 20.1 ng/ml is sufficient.")
    assert len(out) == 1 and '"Insufficiency"' in out[0]


def test_sex_and_smoker_bands_skipped():
    answer = "CPK 248 IU/l suggests toxicity; CEA 2.28 ng/ml is insufficient."
    assert report.band_name_mismatch([CPK, CEA], answer) == []


def test_value_not_cited_no_warning():
    assert report.band_name_mismatch([VITD], "Vitamin D insufficiency is common.") == []


def test_cli_shows_the_warning():
    t = _cli_text()
    assert "report.band_name_mismatch(rows, answer)" in t
    assert t.index("report.band_name_mismatch(") > t.index("report.denied_urine_findings(")
