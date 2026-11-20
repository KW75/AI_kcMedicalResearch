"""SaMD report (Session 49 PR F).

Lab results table computed by the program (never by the AI) from the
reference range printed on the lab report; checks on the AI answer; the
report in output/samd/<run_id>/ as report.md, report.html (opened in the
browser) and report.docx. Stdlib only; python-docx is imported lazily.
"""
from __future__ import annotations

import html
import re
from pathlib import Path

_NUM = r"\d+(?:\.\d+)?"
_LINE = re.compile(
    r"^(?P<name>[A-Za-z][^<>]*?)\s+"
    r"(?P<value>[<>]=?\s?" + _NUM + r"|" + _NUM + r")"
    r"(?:\s+(?P<flag>HH|LL|H|L|\*))?"
    r"\s+(?P<unit>(?=\S*[A-Za-z%])[^\s\d]\S*)"
    r"(?:\s+(?P<ref>" + _NUM + r"\s*-\s*" + _NUM + r"|[<>]=?\s?" + _NUM + r"))?"
    r"\s*$"
)
# Session 49: report symbols mapped to ASCII before matching, so rows with
# <= / >= signs, full-width < > or en/em dash ranges are not dropped.
_SYMBOLS = str.maketrans({
    "\u2264": "<=", "\u2266": "<=", "\u2265": ">=", "\u2267": ">=",
    "\uff1c": "<", "\uff1e": ">", "\u2013": "-", "\u2014": "-",
})
# Session 49: report notes that look like rows (accreditation number,
# percentile notes, "Smoker: Upto 6.5 ug/L") are not results.
_NOT_RESULT = re.compile(r"\bup\s?to\b|\bpercentile\b|^HO?KLAS$", re.I)
STATUS_ORDER = {"HIGH": 0, "LOW": 0, "ABNORMAL": 0, "unclear": 1, "see bands": 1, "normal": 2, "no range": 3}


def _num(s: str) -> float:
    return float(re.search(_NUM, s).group(0))


def status(value: str, ref: str) -> str:
    """HIGH, LOW, normal, unclear (a '<x'/'>x' value that may be either
    side) or 'no range'. Ranges 'a - b' are inclusive."""
    if not ref:
        return "no range"
    v, r = value.replace(" ", ""), ref.replace(" ", "")
    q = re.match(r"[<>]=?", v)
    q = q.group(0) if q else ""
    x = _num(v)
    m = re.fullmatch("(" + _NUM + ")-(" + _NUM + ")", r)
    if m:
        lo, hi = float(m.group(1)), float(m.group(2))
        if not q:
            return "LOW" if x < lo else "HIGH" if x > hi else "normal"
        if q.startswith("<"):
            return "LOW" if x <= lo else "unclear"
        return "HIGH" if x >= hi else "unclear"
    m = re.fullmatch("([<>]=?)(" + _NUM + ")", r)
    if not m:
        return "no range"
    rq, b = m.group(1), float(m.group(2))
    if rq.startswith("<"):            # upper limit only
        if not q:
            high = x >= b if rq == "<" else x > b
            return "HIGH" if high else "normal"
        if q.startswith("<"):
            return "normal" if x <= b else "unclear"
        return "HIGH" if x >= b else "unclear"
    if not q:                         # lower limit only
        low = x <= b if rq == ">" else x < b
        return "LOW" if low else "normal"
    if q.startswith("<"):
        return "LOW" if x <= b else "unclear"
    return "normal" if x >= b else "unclear"


_TEXT_VALUES = r"NEGATIVE|POSITIVE|TRACE|NIL|NOT\s+SEEN|[1-4]\+"
_RANGE = _NUM + r"\s*-\s*" + _NUM
_OTHER = re.compile(
    r"^(?P<name>[A-Za-z][^<>]*?)\s+"
    r"(?P<value>" + _TEXT_VALUES + r"|" + _RANGE + r"|[<>]=?\s?" + _NUM
    + r"|" + _NUM + r")"
    r"(?:\s+(?P<flag>H|L))?"
    r"(?:\s+(?!(?:NEGATIVE|UP\s?TO)\b)(?P<unit>(?=\S*[A-Za-z%])[^\s\d]\S*))?"
    r"(?:\s+(?P<ref>NEGATIVE|UP\s?TO\s+TRACE|UP\s?TO\s+" + _NUM
    + r"|[<>]=?\s?" + _NUM + r"|" + _RANGE + r"))?"
    r"\s*$", re.I)


def _text_status(value: str, ref: str) -> str:
    """NEGATIVE/NIL/NOT SEEN are normal against any printed reference; TRACE
    is normal against 'up to trace' and HIGH against 'negative'; 1+ to 4+
    and POSITIVE are HIGH against either. Anything else: unclear."""
    r = ref.lower()
    if not r:
        return "no range"
    if value in ("NEGATIVE", "NIL", "NOT SEEN"):
        return "normal"
    if value == "TRACE":
        return "normal" if "trace" in r else "HIGH" if r == "negative" else "unclear"
    if r == "negative" or "trace" in r:
        return "HIGH"
    return "unclear"


def _parse_other(line: str):
    """Session 49: rows the main pattern skips - text results (NEGATIVE,
    TRACE, NIL, NOT SEEN, 1+ to 4+, POSITIVE), count ranges (1-3 cell/HPF),
    numbers without a unit but with a printed range (pH 5.5 5.0 - 8.0) and
    'up to N' references. An up/down arrow is the report's H/L flag."""
    text = line.strip().translate(_SYMBOLS)
    text = re.sub(r"\s*\u2191\s*", " H ", text)
    text = re.sub(r"\s*\u2193\s*", " L ", text).strip()
    m = _OTHER.match(text)
    if not m:
        return None
    g = m.groupdict()
    name = re.sub(r"\s+", " ", g["name"]).strip()
    unit = g["unit"] or ""
    if (name.endswith("-") or _NOT_RESULT.search(name)
            or re.search(r"(?<![\w.])\d", name)
            or unit.startswith("(") or unit.lower().rstrip(".") in _TIME_WORDS):
        return None
    value = re.sub(r"\s+", " ", g["value"]).strip().upper()
    ref = re.sub(r"\s+", " ", g["ref"] or "").strip()
    is_text = re.fullmatch(_TEXT_VALUES, value) is not None
    rng = re.fullmatch("(" + _NUM + r")\s*-\s*(" + _NUM + ")", value)
    if is_text:
        pass
    elif rng:
        if not unit:
            return None
        value = f"{rng.group(1)}-{rng.group(2)}"
    elif not unit:
        if not re.fullmatch(_NUM, value) or not re.fullmatch(_RANGE, ref):
            return None
    elif not ref.lower().startswith("up"):
        return None
    if not is_text:
        value = value.replace(" ", "")
    up = re.fullmatch(r"up\s?to\s+(" + _NUM + ")", ref, re.I)
    rr = re.fullmatch("(" + _NUM + r")\s*-\s*(" + _NUM + ")", ref)
    if up:
        ref = "<=" + up.group(1)
    elif rr:
        ref = f"{rr.group(1)} - {rr.group(2)}"
    elif ref[:1] in ("<", ">"):
        ref = ref.replace(" ", "")
    elif ref:
        ref = ref[0].upper() + ref[1:].lower()
    if is_text:
        st = _text_status(value, ref)
    elif rng:
        a, b = status(rng.group(1), ref), status(rng.group(2), ref)
        st = a if a == b else "no range" if "no range" in (a, b) else "unclear"
    else:
        st = status(value, ref)
    return {"test": name, "value": value, "unit": unit, "ref": ref,
            "flag": (g["flag"] or "").upper(), "status": st}


_DESC_NAME = r"(?:Colou?r|COLOU?R|Clarity|CLARITY|Appearance|APPEARANCE)"
_DESC_WORDS = (r"PALE\s+YELLOW|DARK\s+YELLOW|YELLOW|STRAW|AMBER|ORANGE|RED|"
               r"BROWN|COLOU?RLESS|SLIGHTLY\s+TURBID|TURBID|CLEAR|CLOUDY|HAZY")
_DESCRIPTIVE = re.compile(
    r"^(?P<name>" + _DESC_NAME + r"(?:\s+[^\x00-\x7f]+)?)\s+"
    r"(?P<value>" + _DESC_WORDS + r")(?:\s+-)?\s*$")


_DESC_ABNORMAL = {"RED", "BROWN", "TURBID"}  # user decision, Session 49


def _parse_descriptive(line: str):
    """Session 49: urinalysis Colour / Clarity / Appearance rows
    ("Colour 順色 YELLOW -"). Only these names and a fixed list of upper-case
    words. The report prints no reference: RED, BROWN and TURBID are
    ABNORMAL (user decision, Session 49); every other word is 'no range'."""
    m = _DESCRIPTIVE.match(line.strip().translate(_SYMBOLS))
    if not m:
        return None
    value = re.sub(r"\s+", " ", m.group("value")).strip()
    return {"test": re.sub(r"\s+", " ", m.group("name")).strip(),
            "value": value, "unit": "", "ref": "", "flag": "",
            "status": "ABNORMAL" if value in _DESC_ABNORMAL else "no range"}


def parse_line(line: str):
    """One result row (dict) or None if the line is not a lab result."""
    m = _LINE.match(line.strip().translate(_SYMBOLS))
    if not m:
        return _parse_other(line) or _parse_descriptive(line)
    g = m.groupdict()
    # Session 49: a reference-note line ("... 5.7 - 6.4 6.1 - 6.9 (IFG)") is
    # not a result: unit in brackets, or a range or dash left in the name.
    name = g["name"].strip()
    if (g["unit"].startswith("(") or name.endswith("-")
            or re.search(_NUM + r"\s*-\s*" + _NUM, name)):
        return None
    if _NOT_RESULT.search(name):
        return None
    value = re.sub(r"\s+", "", g["value"])
    ref = (g["ref"] or "").strip()
    if ref and ref[0].isdigit():
        lo, hi = [p.strip() for p in ref.split("-", 1)]
        ref = f"{lo} - {hi}"
    else:
        ref = ref.replace(" ", "")
    return {"test": re.sub(r"\s+", " ", g["name"]).strip(), "value": value,
            "unit": g["unit"], "ref": ref, "flag": g["flag"] or "",
            "status": status(value, ref)}


_CRIT = re.compile(r"[<>]=?\s?" + _NUM + r"|" + _NUM + r"\s*-\s*" + _NUM)


def _add_bands(row: dict, following: list[str]) -> None:
    """Session 49: a result printed without a range (HbA1c 6.1 %) but with a
    band table below it ("Interpretation  HbA1c (%)  FBS", then one band per
    line) gets the printed bands of its own column as the reference, and the
    value is marked in every band it falls in. Bands may overlap, so the
    program does not pick one: status 'see bands'."""
    key = row["test"].split()[0].lower()
    if len(key) < 3:
        return
    for h, head in enumerate(following[:2]):
        cols = re.split(r"\s{2,}", head.strip())
        hits = [n for n, c in enumerate(cols[1:]) if key in c.lower()]
        if hits:
            break
    else:
        return
    col, bands = hits[0], []
    for line in following[h + 1:]:
        text = line.strip().translate(_SYMBOLS)
        if not text:
            break
        crits = _CRIT.findall(text)
        if not crits:
            if not bands or not text[0].islower():
                break
            bands[-1][0] += " " + text
            continue
        label = re.sub(r"\s+", " ", text[:_CRIT.search(text).start()]).strip()
        if label and col < len(crits):
            bands.append([label, re.sub(r"\s+", " ", crits[col])])
    if not bands:
        return
    row["ref"] = "; ".join(
        f"{label} {crit}"
        + (" (value in band)" if status(row["value"], crit) == "normal" else "")
        for label, crit in bands)
    row["status"] = "see bands"


_VALUE_FIRST = re.compile(r"(?:[<>]=?\s?)?" + _NUM + r"\s")
_HEADER = re.compile(r"^(?:tests?|interpretation)\b|\bref\.?\s*range\b", re.I)


def _name_above(lines: list[str], i: int) -> str:
    """Session 49: name for a value row printed without one ("6.9 U <9.0"):
    the nearest line above with ASCII letters, at most 2 lines up (a
    Chinese-only name line is skipped). A blank line, a header, a report
    note or a line that is itself a result gives no name. A trailing '#'
    (not HOKLAS-accredited) is dropped."""
    for line in reversed(lines[max(0, i - 2):i]):
        text = line.strip().translate(_SYMBOLS)
        if not text:
            return ""
        if not re.search(r"[A-Za-z]", text):
            continue
        name = re.sub(r"\s+", " ", text).rstrip("#").strip()
        if (not name or _HEADER.search(name) or _NOT_RESULT.search(name)
                or parse_line(text) or _VALUE_FIRST.match(text + " ")):
            return ""
        return name
    return ""


def _parse_nameless(lines: list[str], i: int):
    """Session 49: parse a value-first line under a placeholder name, so the
    value, unit, ref and status rules stay those of parse_line."""
    text = lines[i].strip().translate(_SYMBOLS)
    if not _VALUE_FIRST.match(text + " "):
        return None
    name = _name_above(lines, i)
    if not name:
        return None
    row = parse_line("Result " + text)
    if row:
        row["test"] = name
    return row


_PER_FIELD = re.compile(r"/\s*[HL]PF\b", re.I)


def _mark_urine(row: dict) -> None:
    """Session 49: a urine microscopy row (unit per field, /HPF or /LPF) gets
    ' - Urine' after its English name, so 'WBC 白血球' NIL cell/HPF differs from
    the blood 'WBC 白血球' 4.9 x10e9/L in the same file. The Chinese part is kept
    (lab style 'pH - Urine 酸鹼度'); names already saying Urine are left alone."""
    if not _PER_FIELD.search(row["unit"]) or re.search(r"\burine\b", row["test"], re.I):
        return
    m = re.match(r"([\x00-\x7f]+?)\s*([^\x00-\x7f].*)?$", row["test"])
    if not m or not m.group(1).strip():
        return
    rest = (m.group(2) or "").strip()
    row["test"] = f"{m.group(1).strip()} - Urine" + (f" {rest}" if rest else "")


def parse_results(described) -> list[dict]:
    """Rows from every transcription / text layer (photos are skipped)."""
    rows = []
    for name, kind, body in described:
        if kind == "photo description":
            continue
        lines = (body or "").splitlines()
        for i, line in enumerate(lines):
            row = parse_line(line) or _parse_nameless(lines, i)
            if row:
                _mark_urine(row)
                if not row["ref"] and re.fullmatch(r"(?:[<>]=?)?" + _NUM, row["value"]):
                    _add_bands(row, lines[i + 1:])
                row["source"] = name
                rows.append(row)
    return rows


# --- checks on the AI answer -------------------------------------------------

_ABNORMAL = re.compile(r"\b(elevated|raised|high|increased|low|decreased|"
                       r"reduced|abnormal|borderline)\b|ana?emi", re.I)
_NORMAL = re.compile(r"\b(normal|within)\b", re.I)
_CITED = re.compile(r"(?<![\w.])(" + _NUM + r")\s?(%|[A-Za-z][A-Za-z/^0-9.]*)")
_TIME_WORDS = {"year", "years", "month", "months", "week", "weeks", "day",
               "days", "hour", "hours", "hr", "hrs", "minute", "minutes",
               "min", "mins", "times", "x"}


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text) if s.strip()]


def _has_number(text: str, num: str) -> bool:
    return re.search(r"(?<![\d.])" + re.escape(num) + r"(?!\d)", text) is not None


def _value_cited(text: str, num: str) -> bool:
    """num appears in text as a value: not the end of a range ("3-6"), not
    a time span ("6 months") and not part of a longer number ("6.5").
    Session 49: "Repeat CBC in 3-6 months" was matched to Monocytes 6 %."""
    for m in re.finditer(r"(?<![\d.])" + re.escape(num) + r"(?!\.?\d)", text):
        if re.search(r"\d\s*[-\u2013\u2014]\s*$", text[:m.start()]):
            continue
        w = re.match(r"\s*([A-Za-z]+)\b", text[m.end():])
        if w and w.group(1).lower() in _TIME_WORDS:
            continue
        return True
    return False


_NOT_NORMAL = re.compile(r"\b(?:not|no longer)\s+(?:normal|within)\b", re.I)


def _row_named(s: str, r: dict) -> bool:
    """Session 49: sentence s names row r - a number value cited as a value,
    or (text values such as RED, 1+, TRACE) the first word of the test name
    and the value both in the sentence."""
    value = r["value"]
    if re.fullmatch(r"(?:[<>]=?)?" + _NUM, value):
        return _value_cited(s, value.lstrip("<>="))
    words = r["test"].split()
    key = re.sub(r"[^a-z]", "", words[0].lower()) if words else ""
    if len(key) < 3:
        return False
    key_pat = r"colou?r" if key in ("colour", "color") else re.escape(key)
    return (re.search(r"\b" + key_pat + r"\b", s, re.I) is not None
            and re.search(r"(?<!\w)" + re.escape(value) + r"(?!\w)", s, re.I) is not None)


def check_answer(rows, answer: str, case: str) -> list[str]:
    """Warnings: an in-range result called abnormal; an out-of-range result
    (HIGH, LOW, ABNORMAL) called normal; numbers with a unit in
    the answer that appear nowhere in the case (sources + doctor's notes)."""
    warnings = []
    sentences = _sentences(answer)
    for r in rows:
        if (r["status"] != "normal"
                or not re.fullmatch(r"(?:[<>]=?)?" + _NUM, r["value"])):
            continue
        for s in sentences:
            if (_value_cited(s, r["value"]) and _ABNORMAL.search(s)
                    and not _NORMAL.search(s)):
                short = s if len(s) <= 200 else s[:197] + "..."
                warnings.append(
                    f"The answer may call an in-range result abnormal: "
                    f"{r['test']} {r['value']} {r['unit']} (range {r['ref']}): "
                    f"\"{short}\"")
                break
    for r in rows:
        if r["status"] not in ("HIGH", "LOW", "ABNORMAL"):
            continue
        for s in sentences:
            if (_row_named(s, r) and _NORMAL.search(s)
                    and not _ABNORMAL.search(s) and not _NOT_NORMAL.search(s)):
                short = s if len(s) <= 200 else s[:197] + "..."
                what = " ".join(x for x in (r["test"], r["value"], r["unit"]) if x)
                ref = f", range {r['ref']}" if r["ref"] else ""
                warnings.append(
                    f"The answer may call an out-of-range result normal: "
                    f"{what} ({r['status']}{ref}): \"{short}\"")
                break
    missing = []
    for m in _CITED.finditer(answer):
        num, unit = m.group(1), m.group(2)
        if unit.lower().rstrip(".") in _TIME_WORDS or _has_number(case, num):
            continue
        item = f"{num} {unit}"
        if item not in missing:
            missing.append(item)
    if missing:
        warnings.append("Numbers in the answer not found in the sources: "
                        + ", ".join(missing))
    return warnings


# --- report ------------------------------------------------------------------

def _cell(text: str) -> str:
    return str(text).replace("|", "/").replace("\n", " ")


def build_markdown(*, run_id, intended_use, doctor_text, rows, warnings,
                   answer, sources, ai_line="") -> str:
    md = [f"# SaMD report {run_id}", "", f"**{intended_use}**", "",
          "## Checks by the program", ""]
    md += [f"- WARNING: {w}" for w in warnings] or ["- No warnings."]
    md += ["", "## Lab results (status computed by the program)", ""]
    if rows:
        md += ["| Test | Result | Unit | Reference range | Report flag | Status | Source |",
               "|---|---|---|---|---|---|---|"]
        for r in sorted(rows, key=lambda r: STATUS_ORDER.get(r["status"], 9)):
            st = f"**{r['status']}**" if r["status"] in ("HIGH", "LOW", "ABNORMAL") else r["status"]
            md.append("| " + " | ".join(_cell(c) for c in (
                r["test"], r["value"], r["unit"] or "-", r["ref"] or "-",
                r["flag"] or "-", st, r["source"])) + " |")
        md += ["", "Status is computed from the reference range printed on "
               "the report, not by the AI. Results without a printed range "
               "show 'no range'; 'see bands' means bands are printed below "
               "the result and the value is marked in each band it falls in."]
    else:
        md.append("No lab result with a value and unit was found in the sources.")
    md += ["", "## Doctor's notes", "", doctor_text or "(none typed)", "",
           "## AI answer", "", re.sub(r"(?m)^(#{1,5}) ", r"#\1 ", answer), "",
           "## Sources", ""]
    md += [f"- {n} ({k})" for n, k in sources] or ["- (typed text only)"]
    if ai_line:
        md += ["", ai_line]
    return "\n".join(md) + "\n"


_SEP = re.compile(r"^\|[\s:|-]+\|$")
_CSS = ("body{font-family:'Segoe UI',Arial,sans-serif;max-width:62em;"
        "margin:2em auto;padding:0 1em;line-height:1.45;color:#222}"
        "h2{border-bottom:1px solid #ccc;padding-bottom:.2em}"
        "table{border-collapse:collapse;margin:.5em 0}"
        "th,td{border:1px solid #999;padding:.25em .6em;text-align:left}"
        "th{background:#eee}td strong{color:#b00000}")


def _cells(row: str) -> list[str]:
    return [c.strip() for c in row.strip().strip("|").split("|")]


def _inline(s: str) -> str:
    s = html.escape(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    return re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", s)


def md_to_html(md: str, title: str) -> str:
    """Small Markdown subset (headings, lists, tables, bold, italic) to a
    self-contained HTML page; all text is escaped."""
    out, table = [], []
    state = {"list": None}

    def close_list():
        if state["list"]:
            out.append(f"</{state['list']}>")
            state["list"] = None

    def flush_table():
        rows = [r for r in table if not _SEP.match(r)]
        if rows:
            out.append("<table>")
            for i, r in enumerate(rows):
                tag = "th" if i == 0 else "td"
                out.append("<tr>" + "".join(f"<{tag}>{_inline(c)}</{tag}>"
                                            for c in _cells(r)) + "</tr>")
            out.append("</table>")
        table.clear()

    for raw in md.splitlines():
        s = raw.strip()
        if s.startswith("|"):
            close_list()
            table.append(s)
            continue
        flush_table()
        m = re.match(r"(#{1,6})\s+(.*)", s)
        if m:
            close_list()
            n = len(m.group(1))
            out.append(f"<h{n}>{_inline(m.group(2))}</h{n}>")
            continue
        m = re.match(r"([-*]|\d+\.)\s+(.*)", s)
        if m:
            kind = "ol" if m.group(1)[0].isdigit() else "ul"
            if state["list"] != kind:
                close_list()
                out.append(f"<{kind}>")
                state["list"] = kind
            out.append(f"<li>{_inline(m.group(2))}</li>")
            continue
        close_list()
        if s:
            out.append(f"<p>{_inline(s)}</p>")
    close_list()
    flush_table()
    return ("<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
            "<title>" + html.escape(title) + "</title>\n<style>" + _CSS
            + "</style>\n</head>\n<body>\n" + "\n".join(out) + "\n</body>\n</html>\n")


_CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def _runs(paragraph, text: str) -> None:
    for i, part in enumerate(re.split(r"\*\*(.+?)\*\*", text)):
        if part:
            run = paragraph.add_run(part if i % 2 else part.replace("*", ""))
            run.bold = bool(i % 2)


def write_docx(path, md: str) -> None:
    import docx  # lazy
    d = docx.Document()
    table = []

    def flush_table():
        rows = [_cells(r) for r in table if not _SEP.match(r)]
        if rows:
            cols = len(rows[0])
            t = d.add_table(rows=len(rows), cols=cols)
            t.style = "Table Grid"
            for i, r in enumerate(rows):
                for j, c in enumerate(r[:cols]):
                    _runs(t.cell(i, j).paragraphs[0], c)
        table.clear()

    for raw in _CTRL.sub("", md).splitlines():
        s = raw.strip()
        if s.startswith("|"):
            table.append(s)
            continue
        flush_table()
        if not s:
            continue
        m = re.match(r"(#{1,6})\s+(.*)", s)
        if m:
            d.add_heading(m.group(2).replace("*", ""), level=min(len(m.group(1)), 4))
            continue
        m = re.match(r"([-*]|\d+\.)\s+(.*)", s)
        if m:
            style = "List Number" if m.group(1)[0].isdigit() else "List Bullet"
            _runs(d.add_paragraph(style=style), m.group(2))
            continue
        _runs(d.add_paragraph(), s)
    flush_table()
    d.save(str(path))


def write_report(out_dir, md: str, *, title: str, log=print) -> dict:
    """report.md, report.html, report.docx in out_dir; a .docx error keeps
    the other two (paths['docx'] is then None)."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {"md": out_dir / "report.md", "html": out_dir / "report.html",
             "docx": out_dir / "report.docx"}
    paths["md"].write_text(md, encoding="utf-8", newline="\n")
    paths["html"].write_text(md_to_html(md, title), encoding="utf-8", newline="\n")
    try:
        write_docx(paths["docx"], md)
    except Exception as e:
        log(f"Could not write report.docx ({e}); report.md and report.html written.")
        paths["docx"] = None
    return paths
