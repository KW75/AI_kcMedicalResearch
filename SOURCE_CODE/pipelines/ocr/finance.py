"""OCR -> Finance (launcher menu 8, option 3; Session 50).

Several invoices in input/ocr/ -> one finance table: date, particulars (the
invoice header), category, currency, amount, exchange rate, amount in the
local currency, a subtotal per category and the total, written as
<header>_FINANCE.csv, .html, .docx and .pdf in output/ocr/.

The AI reads each invoice (the OCR step, as in Synopsis; .eml receipts are
read as text) and returns its fields as JSON; it does no arithmetic.
Session 50 cont. 11: exchange rates come only from
reference/ocr_finance/Reference_exchange_rates.txt. After all invoices are
read, the rates of only the currencies they use are listed and can be
changed before anything is written; changes are saved back with the day's
date. Rates are never guessed or looked up online. The program converts and
adds up with Decimal, rounded half up to 2 places. A row whose amount is not
found in the invoice text, or that has no amount, currency or rate, is shown
but kept out of the totals.
"""
from __future__ import annotations

import csv
import html
import json
import re
from datetime import date as _date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

from . import engine, output, reader

RATES_REL = Path("reference") / "ocr_finance" / "Reference_exchange_rates.txt"
RATES_FILE = RATES_REL.name
OLD_RATES_FILE = "finance_rates.csv"  # first version, in input/ocr; copied once
DEFAULT_LOCAL = "HKD"
CATEGORIES = ("Travel", "Accommodation", "Meals", "Conference/registration",
              "Equipment", "Software/subscriptions", "Publication fees", "Other")
CENT = Decimal("0.01")
MAX_PDF_PAGES = 500
RATES_TEMPLATE = (
    "# Exchange rates for OCR -> Finance (launcher menu 8, option 3).\n"
    "# local = the currency the totals are shown in.\n"
    "# Other lines: code,rate,date - rate = local currency for 1 unit, date =\n"
    "# when it was set (optional), e.g. USD,7.80,2026-11-26 means 1 USD = 7.80 HKD.\n"
    "# Lines starting with # are ignored. Rates changed at the Finance prompt\n"
    "# are saved here with the day's date.\n"
    "local,HKD\n"
)
FINANCE_PROMPT = (
    "Below is the text of one invoice or receipt. Reply with ONE JSON object "
    "and nothing else, with these keys:\n"
    '"date": the invoice date as YYYY-MM-DD ("" if none is printed);\n'
    '"particulars": the invoice header - issuer name and invoice number - '
    "and a few words on what was bought;\n"
    '"currency": the 3-letter ISO code of the amount (e.g. HKD, USD, EUR, '
    "CNY, GBP, JPY);\n"
    '"amount": the total amount payable, exactly as printed (e.g. "1,234.50");\n'
    '"category": one of: ' + "; ".join(CATEGORIES) + ".\n"
    "Use only what the text shows. Do not convert currencies, add up or "
    "guess anything."
)
_KEEP_OUT = ("not read", "AI reply", "no amount", "amount not found",
             "currency not clear", "no exchange rate")
_NUMBER = re.compile(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?")
_ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
_EMAIL_DATE = re.compile(r"^Email date: (\d{4}-\d{2}-\d{2})", re.M)
_CSS = ("body{font-family:Arial,sans-serif;font-size:9pt}"
        "table{border-collapse:collapse;margin-bottom:12px}"
        "td,th{border:1px solid #888;padding:2px 4px;vertical-align:top}"
        "th{background:#eee}")


def default_rates_path(folder) -> Path:
    """reference/ocr_finance/Reference_exchange_rates.txt of the project whose
    input/ocr folder is `folder`."""
    return Path(folder).resolve().parents[1] / RATES_REL


def _parse_rate_line(line):
    """None (blank/comment), "bad", ("LOCAL", code, None) or (code, rate, date).
    Accepts 'USD,7.80,2026-11-26', 'USD 7.80', 'USD = 7.80', '1 USD = 7.80 HKD'."""
    s = line.split("#", 1)[0].strip().lstrip("*-\u2022 \t").strip()
    if not s:
        return None
    s = re.sub(r"(?i)^local\s+currency\b", "local", s)
    toks = [t for t in re.split(r"[,\s=:\u2248~]+", s) if t]
    if toks and toks[0] == "1":
        toks = toks[1:]
    if len(toks) < 2:
        return "bad"
    key = toks[0].upper()
    if key == "LOCAL":
        if re.fullmatch(r"[A-Za-z]{3}", toks[1]):
            return ("LOCAL", toks[1].upper(), None)
        return "bad"
    if not re.fullmatch(r"[A-Z]{3}", key):
        return "bad"
    try:
        rate = Decimal(toks[1])
    except InvalidOperation:
        return "bad"
    if not rate.is_finite() or rate <= 0:
        return "bad"
    when = next((t for t in toks[2:] if _ISO_DATE.fullmatch(t)), "")
    return (key, rate, when)


def load_rates(path, log=print, legacy=None) -> dict:
    """{"local", "rates", "dates"} from the rates file. A missing file is
    copied from an old input/ocr/finance_rates.csv (legacy) or gets the
    template. The local currency always has rate 1."""
    path = Path(path)
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        if legacy is not None and Path(legacy).exists():
            text = Path(legacy).read_bytes().decode("utf-8-sig", errors="replace")
            path.write_bytes(text.encode("utf-8"))
            log(f"Exchange rates copied from {legacy} to {path} "
                f"(the old file is no longer read).")
        else:
            path.write_bytes(RATES_TEMPLATE.encode("utf-8"))
            log(f"No exchange-rate file: template written to {path}. Type "
                f"rates at the prompt or add them to the file.")
    local, rates, dates = DEFAULT_LOCAL, {}, {}
    text = path.read_bytes().decode("utf-8-sig", errors="replace")
    for n, line in enumerate(text.splitlines(), 1):
        p = _parse_rate_line(line)
        if p is None:
            continue
        if p == "bad":
            log(f"    WARNING: {path.name} line {n} skipped: {line.strip()}")
            continue
        key, value, when = p
        if key == "LOCAL":
            local = value
            continue
        rates[key], dates[key] = value, when
    rates[local] = Decimal("1")
    dates.pop(local, None)
    return {"local": local, "rates": rates, "dates": dates}


def read_rates(path, log=print, legacy=None):
    """(local currency, {code: rate}) from the rates file."""
    book = load_rates(path, log, legacy)
    return book["local"], book["rates"]


def save_rates(path, changes, today) -> None:
    """Write changed rates back as code,rate,date; other lines are kept."""
    path = Path(path)
    if path.exists():
        lines = path.read_bytes().decode("utf-8-sig", errors="replace").splitlines()
    else:
        lines = RATES_TEMPLATE.splitlines()
    done = set()
    for i, line in enumerate(lines):
        p = _parse_rate_line(line)
        if isinstance(p, tuple) and p[0] in changes:
            lines[i] = f"{p[0]},{_rate(changes[p[0]])},{today}"
            done.add(p[0])
    for code in sorted(changes):
        if code not in done:
            lines.append(f"{code},{_rate(changes[code])},{today}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(("\n".join(lines) + "\n").encode("utf-8"))


def _rate_line(code, rate, when):
    if rate is None:
        return f"  {code}  no rate"
    return f"  {code}  {_rate(rate)}  " + (f"set {when}" if when else "(no date)")


def ask_rates(used, book, input_fn, log, path):
    """List the rates of only the currencies used; CODE RATE changes one.
    Returns {code: rate} changes, or None when cancelled (Ctrl+C)."""
    local = book["local"]
    if not used:
        log(f"All amounts are in {local}: no exchange rate needed.")
        return {}
    log(f"Exchange rates ({local} for 1 unit) of the currencies in these "
        f"invoices, from {path}:")
    for code in used:
        log(_rate_line(code, book["rates"].get(code), book["dates"].get(code, "")))
    if input_fn is None:
        log("  (no prompt: rates used as listed)")
        return {}
    changes = {}
    while True:
        try:
            answer = input_fn("Change a rate as CODE RATE (e.g. USD 7.82); "
                              "Enter = use these rates: ").strip()
        except EOFError:
            log("No keyboard: rates used as listed.")
            return changes
        except KeyboardInterrupt:
            log("Cancelled.")
            return None
        if not answer:
            return changes
        toks = answer.replace(",", " ").replace("=", " ").split()
        rate = None
        if len(toks) == 2 and toks[0].upper() in used:
            try:
                rate = Decimal(toks[1])
            except InvalidOperation:
                rate = None
            if rate is not None and (not rate.is_finite() or rate <= 0):
                rate = None
        if rate is None:
            log(f"  Not understood: {answer!r} - type CODE RATE for a currency "
                f"listed above, e.g. USD 7.82")
            continue
        code = toks[0].upper()
        changes[code] = rate
        log(f"  {code} = {_rate(rate)} {local} (will be saved)")


def convert(amount, rate):
    """amount x rate, rounded half up to 2 places."""
    return (amount * rate).quantize(CENT, rounding=ROUND_HALF_UP)


def parse_amount(value):
    """Decimal from an amount as printed ('HK$1,234.50' -> 1234.50), or None."""
    s = re.sub(r"[^\d.\-]", "", str(value or ""))
    if not re.fullmatch(r"-?\d+(?:\.\d+)?", s):
        return None
    return Decimal(s)


def amount_in_text(amount, text):
    """True if the amount is printed in text (1,234.50 and 1234.5 both count)."""
    target = abs(amount)
    return any(Decimal(n.replace(",", "")) == target for n in _NUMBER.findall(text))


def parse_reply(reply):
    """The first JSON object in the AI reply, or None."""
    m = re.search(r"\{.*\}", reply or "", re.S)
    if not m:
        return None
    try:
        data = json.loads(m.group(0))
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


def read_text(path, call, log=print):
    """OCR text of one invoice: text layer as it is, broken symbols filled,
    image pages read by the vision model (the Synopsis routes)."""
    parts = []
    for page in reader.read_input(path):
        if page["text"] is not None:
            text = page["text"]
        elif page.get("hint"):
            log(f"    page {page['page']}: lost symbols, AI filling [?]...")
            text, _, _ = engine.fill_lines(
                page["hint"], lambda p, png=page["png"]: call(p, images=[png]),
                codes=page.get("codes"))
        else:
            log(f"    page {page['page']}: AI reading...")
            text = call(engine.TRANSCRIBE_PROMPT, images=[page["png"]]).strip()
        parts.append(f"[Page {page['page']}]\n{text}")
    return "\n\n".join(parts)


def _empty_row(name):
    return {"file": name, "date": "", "particulars": "", "category": "Other",
            "currency": "", "amount": None, "rate": None, "local": None,
            "flags": [], "reply": "", "included": False}


def _real_date(s):
    try:
        _date.fromisoformat(s)
    except ValueError:
        return False
    return True


def extract_row(name, text, call, rates=None):
    """One table row from the invoice text: AI fields and checks; converted
    too when rates are given (else apply_rate later)."""
    row = _empty_row(name)
    budget = engine._budget_chars()
    if len(text) > budget:
        text = text[:budget]
        row["flags"].append("invoice text cut to fit the model")
    reply = call(FINANCE_PROMPT + "\n\n" + text).strip()
    row["reply"] = reply
    data = parse_reply(reply)
    if data is None:
        row["flags"].append("AI reply was not a JSON object")
        return row
    row["date"] = str(data.get("date") or "").strip()
    if row["date"] and not _ISO_DATE.fullmatch(row["date"]):
        row["flags"].append("date not in YYYY-MM-DD form")
    elif row["date"] and not _real_date(row["date"]):
        note = f"date {row['date']} is not a real calendar date - check the invoice"
        m = _EMAIL_DATE.search(text)
        if m:
            note += f" (email sent {m.group(1)})"
        row["flags"].append(note)
    row["particulars"] = " ".join(str(data.get("particulars") or "").split())
    cat = str(data.get("category") or "").strip()
    match = next((c for c in CATEGORIES if c.lower() == cat.lower()), None)
    if match is None:
        row["flags"].append(f"category {cat!r} not in the list - set to Other")
        match = "Other"
    row["category"] = match
    cur = str(data.get("currency") or "").strip().upper()
    if re.fullmatch(r"[A-Z]{3}", cur):
        row["currency"] = cur
    else:
        row["flags"].append("currency not clear")
    amount = parse_amount(data.get("amount"))
    if amount is None:
        row["flags"].append("no amount")
    else:
        row["amount"] = amount
        if not amount_in_text(amount, text):
            row["flags"].append("amount not found in the invoice text")
    if rates is not None:
        apply_rate(row, rates)
    return row


def apply_rate(row, rates):
    """Rate and amount in the local currency (or the no-rate flag)."""
    row["rate"] = row["local"] = None
    row["flags"] = [f for f in row["flags"] if not f.startswith("no exchange rate")]
    if row["currency"]:
        rate = rates.get(row["currency"])
        if rate is None:
            row["flags"].append(f"no exchange rate for {row['currency']}")
        else:
            row["rate"] = rate
    if row["amount"] is not None and row["rate"] is not None:
        row["local"] = convert(row["amount"], row["rate"])


def included(row):
    """In the totals: converted, and no flag that puts the amount in doubt."""
    return row["local"] is not None and not any(
        f.startswith(k) for f in row["flags"] for k in _KEEP_OUT)


def totals(rows, local, rates_used=None):
    sub = {}
    for r in rows:
        if r["included"]:
            sub[r["category"]] = sub.get(r["category"], Decimal("0.00")) + r["local"]
    ordered = {c: sub[c] for c in CATEGORIES if c in sub}
    return {"local": local, "subtotals": ordered,
            "total": sum(ordered.values(), Decimal("0.00")),
            "excluded": [r["file"] for r in rows if not r["included"]],
            "rates": list(rates_used or [])}


def _fmt(d):
    return "" if d is None else f"{d:,.2f}"


def _plain(d):
    return "" if d is None else f"{d:.2f}"


def _rate(d):
    return "" if d is None else format(d.normalize(), "f")


def columns(local):
    return ("No", "Date", "Particulars", "Category", "Currency", "Amount",
            "Exchange rate", f"Amount ({local})", "File", "Check")


def table_rows(rows, plain=False):
    money = _plain if plain else _fmt
    out = []
    for i, r in enumerate(rows, 1):
        check = "; ".join(r["flags"] + ([] if r["included"] else ["not in total"]))
        out.append([str(i), r["date"], r["particulars"], r["category"], r["currency"],
                    money(r["amount"]), _rate(r["rate"]), money(r["local"]),
                    r["file"], check])
    return out


def summary_rows(tot, plain=False):
    money = _plain if plain else _fmt
    return ([[c, money(v)] for c, v in tot["subtotals"].items()]
            + [["Total", money(tot["total"])]])


def rate_rows(tot):
    """Rates used, only for the currencies in the invoices."""
    return [[r["code"], _rate(r["rate"]) or "no rate", r["date"] or ""]
            for r in tot.get("rates", [])]


def _note(tot, model):
    text = (output.ai_note(model) + " Dates, particulars, currencies, amounts and "
            "categories were read by AI; exchange rates come from "
            + RATES_REL.as_posix() + " (shown for checking before this file was "
            "written); every sum was computed by the program. Rows marked 'not in "
            "total' need checking against the invoice.")
    if tot["excluded"]:
        text += " Not in total: " + ", ".join(tot["excluded"]) + "."
    return text


def write_csv(path, header, rows, tot, model, page):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(columns(tot["local"]))
        w.writerows(table_rows(rows, plain=True))
        w.writerow([])
        w.writerow(["Subtotal by category", f"Amount ({tot['local']})"])
        w.writerows(summary_rows(tot, plain=True))
        w.writerow([])
        w.writerow(["Exchange rates used", f"{tot['local']} for 1 unit", "Set on"])
        w.writerows(rate_rows(tot))


def build_html(header, rows, tot, model):
    e = html.escape
    local = tot["local"]
    head = "".join(f"<th>{e(c)}</th>" for c in columns(local))
    body = "".join("<tr>" + "".join(f"<td>{e(c)}</td>" for c in r) + "</tr>"
                   for r in table_rows(rows))
    sub = "".join(f"<tr><td>{e(c)}</td><td>{e(v)}</td></tr>"
                  for c, v in summary_rows(tot))
    rr = rate_rows(tot)
    if rr:
        rates = (f"<h2>Exchange rates used ({e(local)} for 1 unit)</h2><table>"
                 "<tr><th>Currency</th><th>Rate</th><th>Set on</th></tr>"
                 + "".join("<tr>" + "".join(f"<td>{e(c)}</td>" for c in r) + "</tr>"
                           for r in rr) + "</table>")
    else:
        rates = f"<p>All amounts in {e(local)}: no exchange rate needed.</p>"
    return ("<!DOCTYPE html><html><head><meta charset='utf-8'><title>"
            + e(header) + " Finance</title><style>" + _CSS + "</style></head><body>"
            + f"<h1>{e(header)} - Finance</h1>"
            + f"<p>Total ({e(local)}): {e(_fmt(tot['total']))}</p>"
            + f"<table><tr>{head}</tr>{body}</table>"
            + f"<h2>Subtotal by category ({e(local)})</h2><table>{sub}</table>"
            + rates
            + f"<p>{e(_note(tot, model))}</p></body></html>\n")


def write_docx(path, header, rows, tot, model, page):
    import docx  # lazy: python-docx
    clean = lambda s: output._clean(s) or ""
    d = docx.Document()
    d.add_heading(clean(f"{header} - Finance"), level=0)
    d.add_paragraph(f"Total ({tot['local']}): {_fmt(tot['total'])}")
    cols = columns(tot["local"])
    t = d.add_table(rows=1, cols=len(cols))
    t.style = "Table Grid"
    for cell, text in zip(t.rows[0].cells, cols):
        cell.text = text
    for r in table_rows(rows):
        for cell, text in zip(t.add_row().cells, r):
            cell.text = clean(text)
    d.add_heading(f"Subtotal by category ({tot['local']})", level=1)
    s = d.add_table(rows=0, cols=2)
    s.style = "Table Grid"
    for cat, v in summary_rows(tot):
        cells = s.add_row().cells
        cells[0].text, cells[1].text = cat, v
    d.add_heading(f"Exchange rates used ({tot['local']} for 1 unit)", level=1)
    rr = rate_rows(tot)
    if rr:
        x = d.add_table(rows=1, cols=3)
        x.style = "Table Grid"
        for cell, text in zip(x.rows[0].cells, ("Currency", "Rate", "Set on")):
            cell.text = text
        for r in rr:
            for cell, text in zip(x.add_row().cells, r):
                cell.text = text
    else:
        d.add_paragraph(f"All amounts in {tot['local']}: no exchange rate needed.")
    d.add_paragraph(clean(_note(tot, model)))
    d.save(str(path))


def write_pdf(path, header, rows, tot, model, page):
    import fitz  # lazy: PyMuPDF (Story turns the HTML page into PDF pages)
    story = fitz.Story(html=page)
    writer = fitz.DocumentWriter(str(path))
    box = fitz.paper_rect("a4-l")
    where = box + (36, 36, -36, -36)
    for _ in range(MAX_PDF_PAGES):
        dev = writer.begin_page(box)
        more, _filled = story.place(where)
        story.draw(dev)
        writer.end_page()
        if not more:
            break
    writer.close()


def write_outputs(out_dir, header, rows, tot, model, log=print):
    """<header>_FINANCE .csv .html .docx .pdf; a .docx/.pdf error keeps the rest."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    page = build_html(header, rows, tot, model)
    paths = {}
    for kind, fn in (("csv", write_csv), ("html", None), ("docx", write_docx),
                     ("pdf", write_pdf)):
        p = out / f"{header}_FINANCE.{kind}"
        try:
            if fn is None:
                p.write_text(page, encoding="utf-8")
            else:
                fn(p, header, rows, tot, model, page)
            paths[kind] = p
        except Exception as exc:
            log(f"    WARNING: {kind} not written: {exc}")
            paths[kind] = None
    return paths


def run_finance(folder, out_dir, name, model, call=None, now=None, log=print,
                records_root=None, rates_path=None, input_fn=None,
                today=None) -> dict:
    """Option 3: every invoice in folder -> one finance table (4 files).
    Reads every invoice first, then shows the rates of the currencies used
    (input_fn may change them), then converts, adds up and writes."""
    folder = Path(folder)
    files = [f for f in reader.list_inputs(folder) if f.name.lower() != OLD_RATES_FILE]
    if not files:
        raise ValueError(f"No invoices in {folder}")
    call = call or engine.ollama_call(model)
    rates_path = Path(rates_path) if rates_path else default_rates_path(folder)
    today = today or _date.today().isoformat()
    book = load_rates(rates_path, log, legacy=folder / OLD_RATES_FILE)
    local = book["local"]
    header = engine.unique_header(name, out_dir, records_root, now)
    rec_dir = engine._rec_dir(records_root, header) or Path(out_dir) / "records" / header
    rec_dir.mkdir(parents=True, exist_ok=True)
    result = {"header": header, "records": [], "failed": [], "summary": None,
              "rows": [], "totals": None, "paths": {}, "rates_file": rates_path}
    for i, path in enumerate(files, start=1):
        log(f"[{i}/{len(files)}] {path.name}")
        try:
            text = read_text(path, call, log)
            row = extract_row(path.name, text, call)
            (rec_dir / f"{path.stem}_OCR.txt").write_text(
                text + "\n\n--- AI reply ---\n" + row["reply"] + "\n", encoding="utf-8")
            result["records"].append(path.name)
        except Exception as exc:
            log(f"    FAILED: {exc}")
            result["failed"].append((path.name, str(exc)))
            row = _empty_row(path.name)
            row["flags"].append(f"not read: {exc}")
        result["rows"].append(row)
    used = sorted({r["currency"] for r in result["rows"]
                   if r["currency"] and r["currency"] != local})
    changes = ask_rates(used, book, input_fn, log, rates_path)
    if changes is None:
        log(f"Cancelled: no finance table written. OCR text and AI replies: {rec_dir}")
        result["cancelled"] = True
        return result
    if changes:
        book["rates"].update(changes)
        book["dates"].update({c: today for c in changes})
        save_rates(rates_path, changes, today)
        log(f"Saved {len(changes)} rate(s) to {rates_path}")
    for row in result["rows"]:
        apply_rate(row, book["rates"])
        row["included"] = included(row)
        notes = row["flags"] + ([] if row["included"] else ["not in total"])
        if notes:
            log(f"  {row['file']}")
            for f in notes:
                log(f"    CHECK: {f}")
    used_rates = [{"code": c, "rate": book["rates"].get(c),
                   "date": book["dates"].get(c, "")} for c in used]
    tot = totals(result["rows"], local, used_rates)
    result["totals"] = tot
    result["paths"] = write_outputs(out_dir, header, result["rows"], tot, model, log)
    log(f"Total ({local}): {_fmt(tot['total'])}; not in total: {len(tot['excluded'])} "
        f"of {len(result['rows'])} invoice(s). OCR text and AI replies: {rec_dir}")
    return result
