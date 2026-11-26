"""Session 50 (cont. 11): OCR Finance follow-up. The rates file is
reference/ocr_finance/Reference_exchange_rates.txt; the rates of only the
currencies the invoices use are shown and can be changed before anything is
written; .eml receipts (and .txt files that are emails) are read.
Made-up invoices and emails only.
"""
import csv
import json
import re
from decimal import Decimal
from email.message import EmailMessage
from pathlib import Path

import pytest

from pipelines.ocr import finance as fin
from pipelines.ocr import reader

ROOT = Path(__file__).resolve().parents[1]
RATES = "local,HKD\nUSD,7.80,2026-11-20\nEUR,8.50\nGBP,9.90\n"
ZETA = "ATTACHED INVOICE ZETA TOTAL HKD 88.00"
REPLIES = {
    "HOTEL ALPHA": {"date": "2026-10-01", "particulars": "Hotel Alpha, invoice A1",
                    "currency": "USD", "amount": "1,234.50", "category": "Accommodation"},
    "CAFE BETA": {"date": "2026-10-02", "particulars": "Cafe Beta, receipt B2",
                  "currency": "HKD", "amount": "300.00", "category": "Meals"},
    "SUSHI GAMMA": {"date": "2026-10-03", "particulars": "Sushi Gamma, receipt C3",
                    "currency": "JPY", "amount": "5,000", "category": "Meals"},
    "SHOP OMEGA": {"date": "2026-37-10", "particulars": "Shop Omega, order O7",
                   "currency": "HKD", "amount": "2.00",
                   "category": "Software/subscriptions"},
}
BASE = {"a.txt": "HOTEL ALPHA  Invoice A1\nTotal due USD 1,234.50\n",
        "b.txt": "CAFE BETA  Receipt B2\nTotal HKD 300.00\n"}
SUSHI = {"c.txt": "SUSHI GAMMA Receipt C3\nTotal JPY 5,000\n"}
EML = (
    "From: Shop Omega <receipts@example.com>\r\n"
    "To: someone@example.com\r\n"
    "Subject: =?UTF-8?Q?=E6=94=B6=E6=93=9A_Shop_Omega?=\r\n"
    "Date: Sat, 10 Oct 2026 12:41:25 +0000\r\n"
    "MIME-Version: 1.0\r\n"
    "Content-Type: text/html; charset=UTF-8\r\n"
    "Content-Transfer-Encoding: quoted-printable\r\n"
    "\r\n"
    "<html><head><title>x</title><style>td {color:red}</style></head><body>\r\n"
    "<table><tr><td>SHOP OMEGA =E6=94=B6=E6=93=9A</td></tr>\r\n"
    "<tr><td>=E6=97=A5=E6=9C=9F</td><td>2026=E5=B9=B437=E6=9C=8810=E6=97=A5</td></tr>\r\n"
    "<tr><td>Order O7</td><td>HK$=C2=A02.00</td></tr></table></body></html>\r\n"
).encode("ascii")


@pytest.fixture(autouse=True)
def _no_env_model(monkeypatch):
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)


def fake_call(prompt, images=None):
    for key, reply in REPLIES.items():
        if key in prompt:
            return json.dumps(reply)
    return "{}"


def _go(tmp_path, files, answers=None, rates=RATES):
    inp = tmp_path / "input" / "ocr"
    inp.mkdir(parents=True)
    for name, body in files.items():
        data = body if isinstance(body, bytes) else body.encode("utf-8")
        (inp / name).write_bytes(data)
    rp = tmp_path / "reference" / "ocr_finance" / "Reference_exchange_rates.txt"
    rp.parent.mkdir(parents=True)
    rp.write_bytes(rates.encode("utf-8"))
    logs = []
    fn = None
    if answers is not None:
        it = iter(answers)

        def fn(prompt=""):
            a = next(it)
            if isinstance(a, BaseException):
                raise a
            return a
    res = fin.run_finance(inp, tmp_path / "output" / "ocr", "Trip", "fake-model",
                          call=fake_call, log=logs.append,
                          records_root=tmp_path / "reports" / "ocr",
                          rates_path=rp, input_fn=fn, today="2026-11-26")
    return res, logs, rp


def _row(res, name):
    return next(r for r in res["rows"] if r["file"] == name)


def _listed(logs):
    found = (re.match(r"  ([A-Z]{3}) ", line) for line in logs)
    return {m.group(1) for m in found if m}


def test_rates_file_lives_in_reference(tmp_path):
    assert fin.RATES_REL.as_posix() == "reference/ocr_finance/Reference_exchange_rates.txt"
    inp = tmp_path / "input" / "ocr"
    inp.mkdir(parents=True)
    assert fin.default_rates_path(inp) == tmp_path.resolve() / fin.RATES_REL


def test_rates_file_lenient_forms(tmp_path):
    p = tmp_path / "r.txt"
    p.write_bytes(b"local,HKD\nUSD,7.80,2026-11-20\nEUR = 8.5\nJPY 0.052 2026-11-01\n"
                  b"1 GBP = 9.9 HKD\n# note\nbad line\n")
    book = fin.load_rates(p, log=lambda *a: None)
    assert book["local"] == "HKD"
    assert book["rates"] == {"USD": Decimal("7.80"), "EUR": Decimal("8.5"),
                             "JPY": Decimal("0.052"), "GBP": Decimal("9.9"),
                             "HKD": Decimal("1")}
    assert book["dates"]["USD"] == "2026-11-20" and book["dates"]["JPY"] == "2026-11-01"


def test_rates_file_written_as_prose(tmp_path):
    p = tmp_path / "r.txt"
    p.write_bytes("\ufeffLocal Currency: HKD\n* 1 USD \u2248 7.84 HKD\n"
                  "* 1 GBP \u2248 10.22 HKD\n".encode("utf-8"))
    book = fin.load_rates(p, log=lambda *a: None)
    assert book["local"] == "HKD"
    assert book["rates"] == {"USD": Decimal("7.84"), "GBP": Decimal("10.22"),
                             "HKD": Decimal("1")}


def test_old_rates_file_copied_once(tmp_path):
    old = tmp_path / "input" / "ocr" / "finance_rates.csv"
    old.parent.mkdir(parents=True)
    old.write_bytes(b"local,HKD\nUSD,7.80\n")
    new = tmp_path / "reference" / "ocr_finance" / "Reference_exchange_rates.txt"
    local, rates = fin.read_rates(new, log=lambda *a: None, legacy=old)
    assert new.exists() and "USD,7.80" in new.read_text(encoding="utf-8")
    assert rates["USD"] == Decimal("7.80") and old.exists()


def test_prompt_lists_only_currencies_used(tmp_path):
    res, logs, _ = _go(tmp_path, BASE, answers=[""])
    assert _listed(logs) == {"USD"}


def test_changed_rate_used_and_saved(tmp_path):
    res, logs, rp = _go(tmp_path, BASE, answers=["USD 8", ""])
    assert _row(res, "a.txt")["local"] == Decimal("9876.00")
    assert res["totals"]["total"] == Decimal("10176.00")
    text = rp.read_text(encoding="utf-8")
    assert "USD,8,2026-11-26" in text and "USD,7.80" not in text
    assert "EUR,8.50" in text and "GBP,9.90" in text


def test_missing_rate_typed_at_prompt(tmp_path):
    res, logs, rp = _go(tmp_path, {**BASE, **SUSHI}, answers=["JPY 0.05", ""])
    row = _row(res, "c.txt")
    assert row["included"] and row["local"] == Decimal("250.00")
    assert res["totals"]["total"] == Decimal("10179.10")
    assert "JPY,0.05,2026-11-26" in rp.read_text(encoding="utf-8")


def test_bad_answers_ask_again(tmp_path):
    res, logs, _ = _go(tmp_path, BASE, answers=["XYZ 1", "USD abc", "HKD 2", ""])
    assert sum(line.startswith("  Not understood") for line in logs) == 3
    assert res["totals"]["total"] == Decimal("9929.10")


def test_no_keyboard_uses_file_unchanged(tmp_path):
    res, logs, rp = _go(tmp_path, BASE, answers=[EOFError()])
    assert res["totals"]["total"] == Decimal("9929.10")
    assert rp.read_bytes() == RATES.encode("utf-8")


def test_outputs_list_rates_used_only(tmp_path):
    res, _, _ = _go(tmp_path, BASE)
    page = Path(res["paths"]["html"]).read_text(encoding="utf-8")
    assert "Exchange rates used" in page and "2026-11-20" in page
    assert "EUR" not in page and "GBP" not in page
    with open(res["paths"]["csv"], encoding="utf-8", newline="") as fh:
        rows = list(csv.reader(fh))
    assert ["USD", "7.8", "2026-11-20"] in rows


def test_eml_html_receipt_read_as_text(tmp_path):
    p = tmp_path / "o.eml"
    p.write_bytes(EML)
    pages = reader.read_input(p)
    text = pages[0]["text"]
    assert len(pages) == 1
    assert "Email date: 2026-10-10" in text
    assert "HK$ 2.00" in text and "\u6536\u64da" in text
    assert "2026\u5e7437\u670810\u65e5" in text
    assert "=C2" not in text and "<td" not in text and "color:red" not in text


def test_eml_is_a_supported_input(tmp_path):
    assert ".eml" in reader.SUPPORTED_EXTS
    (tmp_path / "o.eml").write_bytes(EML)
    (tmp_path / "x.xyz").write_bytes(b"x")
    assert [f.name for f in reader.list_inputs(tmp_path)] == ["o.eml"]


def test_txt_that_is_an_email_read_as_email(tmp_path):
    p = tmp_path / "o.eml.txt"
    p.write_bytes(EML)
    text = reader.read_input(p)[0]["text"]
    assert "HK$ 2.00" in text and "=C2=A0" not in text


def test_plain_txt_unchanged(tmp_path):
    p = tmp_path / "b.txt"
    p.write_bytes(b"CAFE BETA\nTotal HKD 300.00\n")
    assert reader.read_input(p)[0]["text"] == "CAFE BETA\nTotal HKD 300.00"


def test_eml_pdf_attachment_becomes_a_page(tmp_path):
    import fitz
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), ZETA)
    pdf = doc.tobytes()
    doc.close()
    msg = EmailMessage()
    msg["From"] = "Shop Zeta <a@example.com>"
    msg["Subject"] = "Invoice"
    msg["Date"] = "Mon, 12 Oct 2026 08:00:00 +0000"
    msg.set_content("See the attached invoice.")
    msg.add_attachment(pdf, maintype="application", subtype="pdf", filename="z.pdf")
    p = tmp_path / "z.eml"
    p.write_bytes(bytes(msg))
    pages = reader.read_input(p)
    assert len(pages) == 2 and "ZETA" in pages[1]["text"]


def test_impossible_date_flagged_row_kept(tmp_path):
    res, logs, _ = _go(tmp_path, {**BASE, "o.eml": EML})
    row = _row(res, "o.eml")
    assert any("not a real calendar date" in f and "2026-10-10" in f for f in row["flags"])
    assert row["included"]
    assert res["totals"]["total"] == Decimal("9931.10")


def test_cancel_at_rates_writes_nothing(tmp_path):
    res, logs, _ = _go(tmp_path, BASE, answers=[KeyboardInterrupt()])
    assert res.get("cancelled") and not res["paths"]
    assert not list((tmp_path / "output" / "ocr").glob("*_FINANCE.*"))


def test_readme_describes_rates_and_eml():
    text = " ".join((ROOT / "Readme" / "readme_ocr_pipeline.txt")
                    .read_text(encoding="utf-8").split())
    for phrase in ("reference/ocr_finance/Reference_exchange_rates.txt",
                   "Enter = use these rates", ".eml", "not a real calendar date"):
        assert phrase in text, phrase


def test_rates_folder_ignored_by_git():
    lines = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert "reference/ocr_finance/" in [line.strip() for line in lines]
