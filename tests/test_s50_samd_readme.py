"""Session 50: Readme/readme_SaMD_pipeline.txt stays in step with the SaMD code:
function names, statuses, the colour rule, exception words, the urine section
limit and the worked example are checked against report.py / cli.py."""
import ast
import re
from pathlib import Path

from pipelines.samd import report

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "Readme" / "readme_SaMD_pipeline.txt"
SAMD = ROOT / "SOURCE_CODE" / "pipelines" / "samd"
KEY = "out-of-range result normal"


def _text():
    return README.read_bytes().decode("utf-8")


def _flat():
    """Readme text with line breaks and runs of spaces as one space."""
    return " ".join(_text().split())


def test_readme_is_utf8_lf_without_bom():
    raw = README.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf")
    assert b"\r\n" not in raw
    assert raw.endswith(b"\n")


def test_function_names_exist_in_code():
    names = set(re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\(\)", _text()))
    defined = set()
    for p in SAMD.glob("*.py"):
        tree = ast.parse(p.read_text(encoding="utf-8"))
        defined |= {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
    assert names, "the readme names no function"
    assert names <= defined, sorted(names - defined)


def test_every_status_is_described():
    text = _flat()
    for s in report.STATUS_ORDER:
        assert s in text, s


def test_colour_rule_matches_code():
    assert report._DESC_ABNORMAL == {"RED", "BROWN", "TURBID"}
    assert "RED, BROWN and TURBID" in _flat()


def test_exception_words_match_code():
    text = _flat()
    for w in ("apart from", "aside from", "other than", "besides", "save for",
              "with the exception of", "except (for)"):
        assert w in text, w
        assert report._EXCEPT_CLAUSE.search(w.replace(" (for)", " for")), w


def test_urine_section_limit_matches_code():
    assert report._URINE_MAX == 60
    assert "60 lines" in _flat()


def test_worked_example_matches_code():
    text = _text()
    lines = [l[6:] for l in text.splitlines() if l.startswith("    > ")]
    rows = report.parse_results([("example", "transcription", "\n".join(lines))])
    assert {r["test"]: r["status"] for r in rows} == {
        "Colour - Urine 順色": "ABNORMAL", "Blood - Urine 潛血": "HIGH",
        "Protein - Urine 蛋白質": "HIGH"}
    for sentence, n in (("Urine protein is normal.", 1),
                        ("Urinalysis normal apart from protein 1+.", 0),
                        ("Apart from protein 1+, urine blood is normal.", 1)):
        assert '"' + sentence + '"' in text, sentence
        w = [x for x in report.check_answer(rows, sentence, case="") if KEY in x]
        assert len(w) == n, (sentence, w)
