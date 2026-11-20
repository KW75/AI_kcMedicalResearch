"""Session 49: every row inside the URINALYSIS ... Released By section is named
'- Urine', so urine Casts, Mucous, Colour, Clarity and Specific Gravity are told
apart from other results. Lines from reports/samd/20261120_170939
step2_02_labs_2022-11.pdf.txt (27, 416-443)."""
import pytest

from pipelines.samd import report

BLOOD = "WBC                     白血球             4.9            x10e9/L          3.7 - 9.3"
SECTION = [
    "URINALYSIS 尿液常規檢驗",
    "Specimen Type: Mid-Stream Urine",
    "Tests Results Unit Ref. Range",
    "Macrosopic 表觀檢測",
    "Colour 順色 YELLOW -",
    "Clarity 清晰度 CLEAR -",
    "pH - Urine 酸鹼度 5.5 5.0 - 8.0",
    "Specific Gravity 比重 1.025 1.005 - 1.030",
    "Protein - Urine 蛋白質 1+ ↑ Up to trace",
    "Microscopic 顯微鏡檢測",
    "WBC 白血球 NIL cell/HPF ≤5",
    "Casts 圓柱類 NOT SEEN",
    "Urine Crystal 晶體類 NOT SEEN",
    "Mucous 粘液絲 TRACE",
    "Urine Released By: Lai Wai Hung on 14/NOV/2022 13:07",
]
AFTER = "Glucose 5.2 mmol/L 3.9 - 6.1"


def _rows(lines):
    return report.parse_results([("labs.pdf", "transcription", "\n".join(lines))])


def _names(lines):
    return [r["test"] for r in _rows(lines)]


@pytest.mark.parametrize("name", [
    "Colour - Urine 順色",
    "Clarity - Urine 清晰度",
    "Specific Gravity - Urine 比重",
    "Casts - Urine 圓柱類",
    "Mucous - Urine 粘液絲",
])
def test_section_row_named_urine(name):
    assert name in _names([BLOOD] + SECTION + [AFTER])


def test_rows_already_urine_unchanged():
    names = _names([BLOOD] + SECTION + [AFTER])
    for n in ("pH - Urine 酸鹼度", "Protein - Urine 蛋白質", "Urine Crystal 晶體類",
              "WBC - Urine 白血球"):
        assert names.count(n) == 1, n


def test_blood_before_section_unchanged():
    assert _names([BLOOD] + SECTION)[0] == "WBC 白血球"


def test_row_after_released_by_unchanged():
    assert _names(SECTION + [AFTER])[-1] == "Glucose"


def test_mixed_case_urinalysis_starts_no_section():
    assert _names(["Urinalysis CLAB-MBB011", "Casts 圓柱類 NOT SEEN"]) == ["Casts 圓柱類"]


def test_guard_ends_section_after_60_lines():
    lines = ["URINALYSIS 尿液常規檢驗"] + ["note"] * 61 + ["Casts 圓柱類 NOT SEEN"]
    assert _names(lines) == ["Casts 圓柱類"]
