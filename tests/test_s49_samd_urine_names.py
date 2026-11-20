"""Session 49: urine microscopy rows (unit /HPF or /LPF) are named '- Urine',
so they differ from the blood counts in the same file."""
from pipelines.samd import report

# reports/samd/20261120_170939/step2_02_labs_2022-11.pdf.txt lines 27-28, 424-440
BLOCK = "\n".join([
    "WBC                     白血球             4.9            x10e9/L          3.7 - 9.3",
    "RBC Count               紅血球計數         4.42           x10e12/L         4.40 - 5.80",
    "pH - Urine 酸鹼度 5.5 5.0 - 8.0",
    "Microscopic 顯微鏡檢測",
    "WBC 白血球 NIL cell/HPF ≤5",
    "RBC 紅血球 1-3 cell/HPF ≤5",
    "Urine Crystal 晶體類 NOT SEEN",
    "Epithelial Cell 上皮細胞 3-5 cell/LPF",
])


def _rows(body=BLOCK):
    return report.parse_results([("labs.pdf", "transcription", body)])


def _name(rows, value, unit):
    hits = [r["test"] for r in rows if r["value"] == value and r["unit"] == unit]
    assert len(hits) == 1, (value, unit, hits)
    return hits[0]


def test_urine_counts_named_urine():
    rows = _rows()
    assert _name(rows, "NIL", "cell/HPF") == "WBC - Urine 白血球"
    assert _name(rows, "1-3", "cell/HPF") == "RBC - Urine 紅血球"
    assert _name(rows, "3-5", "cell/LPF") == "Epithelial Cell - Urine 上皮細胞"


def test_blood_counts_and_urine_names_unchanged():
    rows = _rows()
    assert _name(rows, "4.9", "x10e9/L") == "WBC 白血球"
    assert _name(rows, "4.42", "x10e12/L") == "RBC Count 紅血球計數"
    assert _name(rows, "5.5", "") == "pH - Urine 酸鹼度"
    assert "Urine Crystal 晶體類" in [r["test"] for r in rows]


def test_wbc_names_unique():
    names = [r["test"] for r in _rows() if r["test"].startswith("WBC")]
    assert len(names) == 2 and len(set(names)) == 2


def test_ascii_name_gets_urine():
    rows = _rows("RBC 1-3 cell/HPF ≤5")
    assert [r["test"] for r in rows] == ["RBC - Urine"]


def test_table_shows_urine_name():
    md = report.build_markdown(run_id="r", intended_use="u", doctor_text="",
                               rows=_rows(), warnings=[], answer="", sources=[])
    assert "| WBC - Urine 白血球 | NIL |" in md
    assert "| WBC 白血球 | 4.9 |" in md


def test_status_unchanged():
    rows = _rows()
    st = {r["test"]: r["status"] for r in rows}
    assert st["WBC 白血球"] == "normal"
    assert st["RBC Count 紅血球計數"] == "normal"
