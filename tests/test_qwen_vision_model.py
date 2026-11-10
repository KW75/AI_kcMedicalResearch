"""
Session 37: SR vision model comes from one rule, not hard-coded names.

DataExtractor, HybridTableExtractor and scripts/nondet_probe.py had
"qwen-vl-plus" hard-coded as their default model. That model returns 404 on
the current key. The real SR run was not affected (sr/main.py always passes
model=args.model), but the probe, and any extractor built without model=,
were. The defaults now come from providers.sr_default_model(provider),
the same rule main._sr_default_model uses.

The docs-match-code tests read the default from providers.py SOURCE, not
from providers.QWEN_VISION_MODEL, so a local .env cannot change the result.
"""
import ast
import io
import re
import tokenize
from pathlib import Path

import pytest

import providers

ROOT = Path(__file__).resolve().parent.parent
SR = ROOT / "SOURCE_CODE" / "pipelines" / "sr"
HARD_CODED = "qwen-vl-plus"
FILES_WITHOUT_HARD_CODED_MODEL = [
    SR / "src" / "extraction" / "data_extractor.py",
    SR / "src" / "extraction" / "table_extractor.py",
    SR / "scripts" / "nondet_probe.py",
]
PROBE = SR / "scripts" / "nondet_probe.py"


# ---------------------------------------------------------------------------
# Extractor defaults follow the shared rule
# ---------------------------------------------------------------------------

def test_data_extractor_without_model_uses_qwen_vision_model(monkeypatch):
    monkeypatch.setattr(providers, "QWEN_VISION_MODEL", "dummy-vl")
    from pipelines.sr.src.extraction.data_extractor import DataExtractor
    ex = DataExtractor(pico_criteria={"outcome": "pain"}, provider="qwen",
                       api_key="dummy-not-a-real-key")
    assert ex.model == "dummy-vl"


def test_data_extractor_explicit_model_wins(monkeypatch):
    monkeypatch.setattr(providers, "QWEN_VISION_MODEL", "dummy-vl")
    from pipelines.sr.src.extraction.data_extractor import DataExtractor
    ex = DataExtractor(pico_criteria={"outcome": "pain"}, provider="qwen",
                       model="explicit-model", api_key="dummy-not-a-real-key")
    assert ex.model == "explicit-model"


def test_hybrid_table_extractor_without_model_uses_qwen_vision_model(monkeypatch):
    monkeypatch.setattr(providers, "QWEN_VISION_MODEL", "dummy-vl")
    from pipelines.sr.src.extraction.table_extractor import HybridTableExtractor
    ex = HybridTableExtractor(pico_criteria={"outcome": "pain"}, provider="qwen",
                              call_llm_fn=lambda *a, **k: "")
    assert ex.model == "dummy-vl"


# ---------------------------------------------------------------------------
# No hard-coded model name left in code or docstrings (comments may keep
# history, e.g. the S26 probe note in data_extractor.py)
# ---------------------------------------------------------------------------

def _string_tokens(path: Path):
    kinds = {tokenize.STRING}
    if hasattr(tokenize, "FSTRING_MIDDLE"):   # Python 3.12+
        kinds.add(tokenize.FSTRING_MIDDLE)
    src = path.read_text(encoding="utf-8")
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type in kinds:
            yield tok.start[0], tok.string


@pytest.mark.parametrize("path", FILES_WITHOUT_HARD_CODED_MODEL,
                         ids=lambda p: p.name)
def test_no_hard_coded_qwen_vl_plus_in_strings(path):
    hits = [line for line, s in _string_tokens(path) if HARD_CODED in s]
    assert hits == [], f"{path.name}: '{HARD_CODED}' in a string on line(s) {hits}"


# ---------------------------------------------------------------------------
# Probe: --model defaults to None (the extractor then applies the rule)
# ---------------------------------------------------------------------------

def test_probe_model_flag_defaults_to_none():
    tree = ast.parse(PROBE.read_text(encoding="utf-8"))
    found = False
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call)
                and getattr(node.func, "attr", None) == "add_argument"
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and node.args[0].value == "--model"):
            found = True
            kw = {k.arg: k.value for k in node.keywords}
            if "default" in kw:
                d = kw["default"]
                assert isinstance(d, ast.Constant) and d.value is None, (
                    f"--model default is {ast.unparse(d)}, expected None")
    assert found, "no add_argument('--model', ...) in nondet_probe.py"


# ---------------------------------------------------------------------------
# Docs match code
# ---------------------------------------------------------------------------

def _code_default() -> str:
    src = (ROOT / "SOURCE_CODE" / "providers.py").read_text(encoding="utf-8")
    m = re.search(r'QWEN_VISION_MODEL\s*=\s*os\.getenv\(\s*"QWEN_VISION_MODEL"'
                  r'\s*,\s*"([^"]+)"', src)
    assert m, "QWEN_VISION_MODEL = os.getenv(...) line not found in providers.py"
    return m.group(1)


def test_env_example_qwen_vision_model_matches_code():
    text = (ROOT / ".env.example").read_text(encoding="utf-8")
    values = re.findall(r"^\s*#?\s*QWEN_VISION_MODEL=(\S+)", text, re.M)
    assert values, "no QWEN_VISION_MODEL= line in .env.example"
    assert set(values) == {_code_default()}, values


def test_readme_qwen_vision_model_matches_code():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    values = re.findall(r"QWEN_VISION_MODEL=(\S+)", text)
    values += re.findall(r"QWEN_VISION_MODEL`\s*\(default `([^`]+)`\)", text)
    assert values, "README names no QWEN_VISION_MODEL value"
    assert set(values) == {_code_default()}, values
