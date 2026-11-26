"""Session 50: OCR menu 8 -> 3 Finance (several invoices -> one finance table).

The AI reads the fields; the program converts with rates from
finance_rates.csv (Decimal, half up), adds subtotals per category and the
total, and keeps doubtful rows out of the totals. Outputs: CSV, HTML, DOCX, PDF.
"""
import csv
import json
from decimal import Decimal
from pathlib import Path

import pytest

from pipelines.ocr import cli

PULLED = [{"name": "gemma4:e4b", "size_gb": 6.6, "params_b": 7.5}]
ROOT = Path(__file__).resolve().parents[1]

REPLIES = {
    "HOTEL ALPHA": {"date": "2026-10-01", "particulars": "Hotel Alpha, invoice A1",
                    "currency": "USD", "amount": "1,234.50", "category": "Accommodation"},
    "CAFE BETA": {"date": "2026-10-02", "particulars": "Cafe Beta, receipt B2",
                  "currency": "HKD", "amount": "300.00", "category": "Meals"},
    "SUSHI GAMMA": {"date": "2026-10-03", "particulars": "Sushi Gamma, receipt C3",
                    "currency": "JPY", "amount": "5,000", "category": "Meals"},
    "SHOP DELTA": {"date": "2026-10-04", "particulars": "Shop Delta, bill D4",
                   "currency": "HKD", "amount": "99.99", "category": "Equipment"},
    "BOOK EPSILON": {"date": "2026-10-05", "particulars": "Book Epsilon, inv E5",
                     "currency": "HKD", "amount": "120.00", "category": "Books"},
    "WEIRD STORE": "Sorry, I cannot read this.",
    "A&B <LTD>": {"date": "2026-10-06", "particulars": "A&B <Ltd> invoice F6",
                  "currency": "HKD", "amount": "1.00", "category": "Other"},
}
TEXTS = {
    "c.txt": "SUSHI GAMMA Receipt C3\nTotal JPY 5,000\n",
    "d.txt": "SHOP DELTA Bill D4\nTotal HKD 55.00\n",
    "e.txt": "BOOK EPSILON Inv E5\nTotal HKD 120.00\n",
    "w.txt": "WEIRD STORE\nTotal HKD 10.00\n",
    "f.txt": "A&B <LTD> Inv F6\nTotal HKD 1.00\n",
}


@pytest.fixture(autouse=True)
def _no_env_model(monkeypatch):
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)


def _fin():
    from pipelines.ocr import finance
    return finance


def fake_call(prompt, images=None):
    for key, reply in REPLIES.items():
        if key in prompt:
            return reply if isinstance(reply, str) else json.dumps(reply)
    return "{}"


def _run(tmp_path, *extra):
    inp = tmp_path / "input" / "ocr"
    inp.mkdir(parents=True)
    (inp / "a.txt").write_text("HOTEL ALPHA  Invoice A1\nTotal due USD 1,234.50\n",
                               encoding="utf-8")
    (inp / "b.txt").write_text("CAFE BETA  Receipt B2\nTotal HKD 300.00\n",
                               encoding="utf-8")
    for name in extra:
        (inp / name).write_text(TEXTS[name], encoding="utf-8")
    (inp / "finance_rates.csv").write_text("local,HKD\nUSD,7.80\n", encoding="utf-8")
    logs = []
    res = _fin().run_finance(inp, tmp_path / "output" / "ocr", "Trip", "fake-model",
                             call=fake_call, log=logs.append,
                             records_root=tmp_path / "reports" / "ocr")
    return res, logs


def _row(res, name):
    return next(r for r in res["rows"] if r["file"] == name)


def _cli(tmp_path, *answers):
    inp = tmp_path / "input" / "ocr"
    inp.mkdir(parents=True)
    for f in ("a.pdf", "b.png"):
        (inp / f).write_bytes(b"x")
    calls, asked, logs = [], [], []
    it = iter(answers)

    def _input(prompt=""):
        asked.append(prompt)
        return next(it)

    def fake_finance(folder, out_dir, name, model, log=print, records_root=None,
                     **kw):
        calls.append(("finance", name))
        return {"header": name, "records": [], "failed": [], "summary": None, "paths": {}}

    def other(*a, **k):
        calls.append(("other",))
        return {"header": "H", "records": [], "failed": [], "summary": None}

    cli.run(tmp_path, input_fn=_input, list_fn=lambda host=None: [dict(m) for m in PULLED],
            caps_fn=lambda host, name: {"completion", "vision"}, run_single=other,
            run_set=other, run_finance=fake_finance, log=logs.append, kind="ask")
    return calls, asked, logs


def test_menu_lists_finance_option(tmp_path):
    calls, asked, logs = _cli(tmp_path, "3", "Trip", "")
    assert any(line.startswith("3. Finance") for line in logs)


def test_prompt_names_finance(tmp_path):
    calls, asked, logs = _cli(tmp_path, "3", "Trip", "")
    assert any("Finance" in p for p in asked)


def test_answer_3_runs_finance_only(tmp_path):
    calls, asked, logs = _cli(tmp_path, "3", "Trip", "")
    assert calls == [("finance", "Trip")]


def test_read_rates_local_and_rates(tmp_path):
    p = tmp_path / "finance_rates.csv"
    p.write_text("local,HKD\nUSD,7.80\n# note\nbad\nEUR,abc\n", encoding="utf-8")
    local, rates = _fin().read_rates(p, log=lambda *a: None)
    assert local == "HKD"
    assert rates == {"USD": Decimal("7.80"), "HKD": Decimal("1")}


def test_missing_rates_file_writes_template(tmp_path):
    p = tmp_path / "input" / "ocr" / "finance_rates.csv"
    local, rates = _fin().read_rates(p, log=lambda *a: None)
    assert p.exists() and "local,HKD" in p.read_text(encoding="utf-8")
    assert (local, rates) == ("HKD", {"HKD": Decimal("1")})


def test_amount_in_text_with_thousands_separator():
    f = _fin()
    assert f.amount_in_text(Decimal("1234.5"), "Total USD 1,234.50")
    assert not f.amount_in_text(Decimal("1234.6"), "Total USD 1,234.50")
    assert not f.amount_in_text(Decimal("2345"), "Total 12,345")


def test_convert_rounds_half_up():
    f = _fin()
    assert f.convert(Decimal("10.005"), Decimal("1")) == Decimal("10.01")
    assert f.convert(Decimal("1234.50"), Decimal("7.80")) == Decimal("9629.10")


def test_subtotals_and_total(tmp_path):
    res, _ = _run(tmp_path)
    tot = res["totals"]
    assert tot["subtotals"] == {"Accommodation": Decimal("9629.10"),
                                "Meals": Decimal("300.00")}
    assert tot["total"] == Decimal("9929.10")


def test_rates_file_is_not_an_invoice(tmp_path):
    res, _ = _run(tmp_path)
    assert res["records"] == ["a.txt", "b.txt"]


def test_amount_not_in_text_kept_out(tmp_path):
    res, _ = _run(tmp_path, "d.txt")
    row = _row(res, "d.txt")
    assert "amount not found in the invoice text" in row["flags"]
    assert not row["included"]
    assert res["totals"]["total"] == Decimal("9929.10")


def test_missing_rate_kept_out(tmp_path):
    res, _ = _run(tmp_path, "c.txt")
    row = _row(res, "c.txt")
    assert "no exchange rate for JPY" in row["flags"]
    assert "c.txt" in res["totals"]["excluded"]
    assert res["totals"]["total"] == Decimal("9929.10")


def test_unknown_category_becomes_other(tmp_path):
    res, _ = _run(tmp_path, "e.txt")
    row = _row(res, "e.txt")
    assert row["category"] == "Other" and row["included"]
    assert any("set to Other" in f for f in row["flags"])
    assert res["totals"]["subtotals"]["Other"] == Decimal("120.00")


def test_bad_reply_flagged_not_crash(tmp_path):
    res, _ = _run(tmp_path, "w.txt")
    row = _row(res, "w.txt")
    assert "AI reply was not a JSON object" in row["flags"]
    assert not row["included"]


def test_writes_csv_html_docx_pdf(tmp_path):
    res, _ = _run(tmp_path)
    paths = res["paths"]
    assert all(paths[k] and Path(paths[k]).exists() for k in ("csv", "html", "docx", "pdf"))
    with open(paths["csv"], encoding="utf-8", newline="") as fh:
        rows = list(csv.reader(fh))
    assert ["Total", "9929.10"] in rows
    import docx
    d = docx.Document(str(paths["docx"]))
    assert any("9,929.10" in p.text for p in d.paragraphs)
    import fitz
    with fitz.open(str(paths["pdf"])) as pdf:
        assert "9,929.10" in "".join(page.get_text() for page in pdf)


def test_html_escapes_text(tmp_path):
    res, _ = _run(tmp_path, "f.txt")
    page = Path(res["paths"]["html"]).read_text(encoding="utf-8")
    assert "A&amp;B &lt;Ltd&gt;" in page
    assert "<Ltd>" not in page


def test_readme_describes_finance():
    text = " ".join((ROOT / "Readme" / "readme_ocr_pipeline.txt")
                    .read_text(encoding="utf-8").split())
    for phrase in ("8. Finance", "Reference_exchange_rates.txt", "rounded half up",
                   "not in total"):
        assert phrase in text, phrase
