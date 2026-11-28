"""Session 52 (cont. 4): the step-2 image prompt asks for one line per result.

The 2024 CBC scan was copied with the test names on the first lines only, so names
shifted onto the wrong numbers (PR #121 repairs that by position). The prompt now
asks, as its one exception to 'do not add anything', for each result on its own line
starting with the test name, with '(absolute)' on the absolute-count line.
Values below are synthetic.
"""
from pipelines.samd import cli, report

NAMES = ["Neutrophils", "Neutrophils (absolute)", "Lymphocytes", "Lymphocytes (absolute)",
         "Monocytes", "Monocytes (absolute)", "Eosinophils", "Eosinophils (absolute)",
         "Basophils", "Basophils (absolute)"]
VALUES = ["70", "4.2", "15", "0.9", "10", "0.6", "4", "0.2", "1", "0.1"]

PLAIN = """WBC Count 6.0 x10e9/L 3.7 - 9.2
Neutrophils 70 % 40 - 75
Neutrophils (absolute) 4.2 x10e9/L 1.8 - 6.2
Lymphocytes 15 % 10 - 50
Lymphocytes (absolute) 0.9 x10e9/L 1.0 - 3.2
Monocytes 10 % 2 - 12
Monocytes (absolute) 0.6 x10e9/L 0.1 - 0.8
Eosinophils 4 % 1 - 6
Eosinophils (absolute) 0.2 x10e9/L 0.0 - 0.4
Basophils 1 % 0 - 2
Basophils (absolute) 0.1 x10e9/L 0.0 - 0.2
"""

CHINESE = """WBC Count 白血球 6.0 x10e9/L 3.7 - 9.2
Differential Count 分類計數
Neutrophils 中性粒細胞 70 % 40 - 75
Neutrophils (absolute) 中性粒細胞 4.2 x10e9/L 1.8 - 6.2
Lymphocytes 淋巴細胞 15 % 10 - 50
Lymphocytes (absolute) 淋巴細胞 0.9 x10e9/L 1.0 - 3.2
Monocytes 單核細胞 10 % 2 - 12
Monocytes (absolute) 單核細胞 0.6 x10e9/L 0.1 - 0.8
Eosinophils 嗜酸性粒細胞 4 % 1 - 6
Eosinophils (absolute) 嗜酸性粒細胞 0.2 x10e9/L 0.0 - 0.4
Basophils 嗜鹼性粒細胞 1 % 0 - 2
Basophils (absolute) 嗜鹼性粒細胞 0.1 x10e9/L 0.0 - 0.2
"""


def _described(text):
    return [("CBC_scan.jpg", "TEXT", text)]


def _diff_rows(text):
    out = []
    for r in report.parse_results(_described(text)):
        t = str(r.get("test", ""))
        for n in sorted(NAMES, key=len, reverse=True):
            if t == n or t.startswith(n + " "):
                low = any(str(v).upper() == "LOW" for v in r.values())
                out.append((n, str(r.get("value", "")), low))
                break
    return out


def _check_layout(text):
    got = _diff_rows(text)
    assert [g[0] for g in got] == NAMES
    assert [g[1] for g in got] == VALUES
    assert [g[0] for g in got if g[2]] == ["Lymphocytes (absolute)"]


def test_prompt_one_line_rule_reverted():
    """Session 52 (cont. 5): the PR #123 sentence was reverted (the model ignored it)."""
    assert "its own line beginning with the test name" not in cli.IMAGE_PROMPT


def test_prompt_absolute_label_reverted():
    assert "(absolute) after the name" not in cli.IMAGE_PROMPT


def test_prompt_old_copy_sentence_back():
    assert "add anything; write [illegible] for a word you cannot read" in cli.IMAGE_PROMPT


def test_prompt_keeps_exact_copy_rules():
    p = cli.IMAGE_PROMPT
    assert "transcribe all text exactly as written" in p
    assert "do not summarise, correct or add anything" in p
    assert "[illegible]" in p


def test_prompt_keeps_type_and_photo_rules():
    p = cli.IMAGE_PROMPT
    for s in ("TYPE: TEXT", "TYPE: PHOTO", "do not name a diagnosis", "not LaTeX"):
        assert s in p


def test_one_line_layout_gives_ten_named_rows():
    _check_layout(PLAIN)


def test_one_line_layout_with_chinese_labels():
    _check_layout(CHINESE)


def test_one_line_layout_no_differential_warning():
    assert report.differential_problems(_described(PLAIN)) == []
    assert report.differential_problems(_described(CHINESE)) == []
