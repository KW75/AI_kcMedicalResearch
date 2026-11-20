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
STATUS_ORDER = {"HIGH": 0, "LOW": 0, "unclear": 1, "normal": 2, "no range": 3}


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


def parse_line(line: str):
    """One result row (dict) or None if the line is not a lab result."""
    m = _LINE.match(line.strip().translate(_SYMBOLS))
    if not m:
        return None
    g = m.groupdict()
    # Session 49: a reference-note line ("... 5.7 - 6.4 6.1 - 6.9 (IFG)") is
    # not a result: unit in brackets, or a range or dash left in the name.
    name = g["name"].strip()
    if (g["unit"].startswith("(") or name.endswith("-")
            or re.search(_NUM + r"\s*-\s*" + _NUM, name)):
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


def parse_results(described) -> list[dict]:
    """Rows from every transcription / text layer (photos are skipped)."""
    rows = []
    for name, kind, body in described:
        if kind == "photo description":
            continue
        for line in (body or "").splitlines():
            row = parse_line(line)
            if row:
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


def check_answer(rows, answer: str, case: str) -> list[str]:
    """Warnings: an in-range result called abnormal; numbers with a unit in
    the answer that appear nowhere in the case (sources + doctor's notes)."""
    warnings = []
    sentences = _sentences(answer)
    for r in rows:
        if r["status"] != "normal":
            continue
        for s in sentences:
            if (_has_number(s, r["value"]) and _ABNORMAL.search(s)
                    and not _NORMAL.search(s)):
                short = s if len(s) <= 200 else s[:197] + "..."
                warnings.append(
                    f"The answer may call an in-range result abnormal: "
                    f"{r['test']} {r['value']} {r['unit']} (range {r['ref']}): "
                    f"\"{short}\"")
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
            st = f"**{r['status']}**" if r["status"] in ("HIGH", "LOW") else r["status"]
            md.append("| " + " | ".join(_cell(c) for c in (
                r["test"], r["value"], r["unit"], r["ref"] or "-",
                r["flag"] or "-", st, r["source"])) + " |")
        md += ["", "Status is computed from the reference range printed on "
               "the report, not by the AI. Results without a printed range "
               "show 'no range'."]
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
