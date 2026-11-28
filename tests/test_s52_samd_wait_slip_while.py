"""Session 52 (cont. 5): wait messages, slipped differential ranges, 'while' clauses.

Run 20261128_114340 copied all 10 differential values in order, but from Eosinophils on each
reference range slipped down one line (a % line without its range, a lone range line at the
end). Values below are synthetic.
"""
import inspect
import re

from pipelines.samd import cli, report

CJK = re.compile(r"[\u3400-\u9fff\uf900-\ufaff]+")
DIFF = re.compile(r"(?i)^(neutrophils?|lymphocytes?|monocytes?|eosinophils?|basophils?)\b")
NAMES = ["Neutrophils", "Neutrophils (absolute)", "Lymphocytes", "Lymphocytes (absolute)",
         "Monocytes", "Monocytes (absolute)", "Eosinophils", "Eosinophils (absolute)",
         "Basophils", "Basophils (absolute)"]
VALUES = ["70", "4.2", "15", "0.9", "10", "0.6", "4", "0.2", "1", "0.1"]

SLIP = """WBC 白血球 6.0 x10e9/L 3.7 - 9.3
Platelet Count 血小板計數 250 x10e9/L 160 - 420
Differential
Neutrophils 嗜中性細胞 70 % 38 - 76
Lymphocytes 淋巴細胞 4.2 x10e9/L 1.8 - 6.2
15 % 10 - 50
Monocytes 單核細胞 0.9 x10e9/L 1.0 - 3.2
10 %
Eosinophils 嗜酸性白細胞 0.6 x10e9/L 0.2 - 0.7
4 %
Basophils 嗜鹼性白細胞 0.2 x10e9/L < 7
1 % 0.04 - 0.4
0.1 x10e9/L < 2
0.0 - 0.1

The total percentage of WBC differential count may not be 100 due to round up effect.
"""

BAD_CHECK = SLIP.replace("Basophils 嗜鹼性白細胞 0.2 x10e9/L < 7", "Basophils 嗜鹼性白細胞 0.9 x10e9/L < 7")

FULL_LONE = """WBC 6.0 x10e9/L 3.7 - 9.3
Differential
Neutrophils 70 % 38 - 76
Lymphocytes 4.2 x10e9/L 1.8 - 6.2
15 % 10 - 50
Monocytes 0.9 x10e9/L 1.0 - 3.2
10 % 2 - 12
Eosinophils 0.6 x10e9/L 0.2 - 0.7
4 % < 7
Basophils 0.2 x10e9/L 0.04 - 0.4
1 % < 2
0.1 x10e9/L 0.0 - 0.1
0.0 - 0.1
"""

CLEAN = FULL_LONE.replace("0.1 x10e9/L 0.0 - 0.1\n0.0 - 0.1\n", "0.1 x10e9/L 0.0 - 0.1\n")

PSA_ROW = {"test": "PSA Total 前列腺特殊抗原", "value": "1.013", "unit": "ng/ml",
           "ref": "0.00 - 4.00", "flag": "", "status": "normal", "source": "x.pdf"}


def _described(text):
    return [("CBC_scan.jpg", "TEXT", text)]


def _diff(text):
    out = []
    for r in report.parse_results(_described(text)):
        t = CJK.sub("", str(r.get("test", ""))).strip()
        if DIFF.match(t) and " - Urine" not in t:
            out.append((t, str(r.get("value", "")), str(r.get("ref") or ""), str(r.get("status", ""))))
    return out


def _ollama(monkeypatch, model=None, pick="m"):
    from pipelines.ocr import engine
    monkeypatch.setattr(engine, "ollama_call", lambda name: (lambda *a, **k: "ok"))
    logs = []
    call = cli.choose_call("ollama", model, log=logs.append, input_fn=lambda *a: "",
                           models_fn=lambda: [{"name": "m", "size_gb": 1.0, "params_b": 1.0}],
                           caps_fn=lambda host, name: ["vision"],
                           pick_fn=lambda models, **k: pick)
    return call, logs


def test_wait_messages_defined():
    for m in (cli._WAIT_READING, cli._WAIT_CHECKING, cli._WAIT_LOADING):
        assert m.endswith("please wait...")
    assert "Ollama" in cli._WAIT_CHECKING


def test_reading_message_before_read_sources():
    src = inspect.getsource(cli.run)
    assert "say(_WAIT_READING)" in src
    assert src.index("say(_WAIT_READING)") < src.index("read_sources(folder")


def test_ollama_list_checking_then_loading(monkeypatch):
    call, logs = _ollama(monkeypatch)
    assert call is not None
    i = logs.index(cli._WAIT_CHECKING)
    j = logs.index("AI: Ollama m (local).")
    k = logs.index(cli._WAIT_LOADING)
    assert i < j < k


def test_ollama_named_model_loading(monkeypatch):
    call, logs = _ollama(monkeypatch, model="m")
    assert call is not None
    assert logs.index("AI: Ollama m (local).") < logs.index(cli._WAIT_LOADING)


def test_cloud_provider_has_no_local_wait_messages(monkeypatch):
    from pipelines.ocr import cli as ocr_cli, engine
    prov = next(iter(ocr_cli.CLOUD_KEYS))
    monkeypatch.setattr(ocr_cli, "_cloud_model", lambda p, m: "x")
    monkeypatch.setattr(engine, "cloud_call", lambda p, n: (lambda *a, **k: "ok"))
    logs = []
    call = cli.choose_call(prov, None, log=logs.append)
    assert call is not None
    assert not any("please wait" in str(l) for l in logs)


def test_no_model_chosen_no_loading_message(monkeypatch):
    call, logs = _ollama(monkeypatch, pick=None)
    assert call is None
    assert not any("Loading the local AI model" in str(l) for l in logs)


def test_slipped_ranges_repaired_by_position():
    got = _diff(SLIP)
    assert [g[0] for g in got] == NAMES
    assert [g[1] for g in got] == VALUES
    assert all(g[2] for g in got[:4])
    assert all(g[2] == "" and g[3] == "no range" for g in got[4:])
    assert [g[0] for g in got if g[3] == "LOW"] == ["Lymphocytes (absolute)"]


def test_slipped_ranges_warning():
    w = report.differential_problems(_described(SLIP))
    assert len(w) == 1
    assert "did not line up" in w[0] and "last 6 rows" in w[0]


def test_slip_with_failed_wbc_check_keeps_rows():
    w = report.differential_problems(_described(BAD_CHECK))
    assert len(w) == 1 and "mislabelled" in w[0]
    assert not any("(absolute)" in g[0] for g in _diff(BAD_CHECK))


def test_lone_range_without_missing_range_still_fails():
    w = report.differential_problems(_described(FULL_LONE))
    assert len(w) == 1 and "mislabelled" in w[0]


def test_clean_block_unchanged():
    assert report.differential_problems(_described(CLEAN)) == []
    got = _diff(CLEAN)
    assert [g[0] for g in got] == NAMES
    assert [g[0] for g in got if g[3] == "LOW"] == ["Lymphocytes (absolute)"]


def test_while_splits_clause():
    s = ("- **Elevated PSA (1.013 ng/mL)**: While within normal limits for age, it is near the "
         "upper limit and requires monitoring if there are urinary symptoms.")
    w = [x for x in report.check_answer([dict(PSA_ROW)], s, "") if "in-range" in x]
    assert len(w) == 1


def test_while_normal_clause_quiet():
    s = "While the PSA (1.013 ng/ml) remains within the normal range, it should be rechecked in a year."
    w = [x for x in report.check_answer([dict(PSA_ROW)], s, "") if "in-range" in x]
    assert w == []
