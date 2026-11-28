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


def _parse_line_v1(line: str):
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



# --- Session 51: other labs' layouts -----------------------------------------
_ROW_NO = re.compile(r"^\d{1,3}\s+(?=[A-Za-z])")  # "22 SGOT/AST ..."
_ARROW = re.compile(r"\s*([\u2191\u2193])\s*")
_CJK = re.compile(r"[\u3400-\u9fff\uf900-\ufaff]")
_TRAILING_NUM = re.compile(r"(?:^|\s)" + _NUM + r"$")
_LINE_VRU = re.compile(
    r"^(?P<name>[A-Za-z][^<>]*?)\s+(?P<value>" + _NUM + r")\s+"
    r"(?P<ref>" + _NUM + r"\s*-\s*" + _NUM + r"|[<>]=?\s?" + _NUM + r")"
    r"(?:\s+\([A-Z]\))?\s+(?P<unit>(?=[^\d\s(])(?=.*[A-Za-z%]).+?)\s*$")


def _numbered_row(text: str) -> bool:
    """Session 51: "24 CPK 肌酸磷酸酶 248 IU/l ..." is a numbered result row,
    not a value printed without a name: a leading row number followed by
    Chinese text or by two or more words before the first number."""
    if not _ROW_NO.match(text):
        return False
    rest = _ROW_NO.sub("", text, count=1)
    if _CJK.search(rest):
        return True
    before = 0
    for tok in rest.split():
        if re.search(r"\d", tok):
            break
        before += 1
    return before >= 2


def _parse_vru(text: str):
    """Session 51: value - range - unit order ("Hb 13.2 13.0-17.0 (M) g/dL",
    "Total Cholesterol 4.12 < 5.20 mmol/L"). A one-letter marker such as
    (M) after the range is dropped; the unit may contain spaces."""
    m = _LINE_VRU.match(text)
    if not m:
        return None
    g = m.groupdict()
    name = re.sub(r"\s+", " ", g["name"]).strip()
    unit = re.sub(r"\s+", " ", g["unit"]).strip()
    if (name.endswith("-") or name.endswith(":")
            or re.search(_NUM + r"\s*-\s*" + _NUM, name)
            or _NOT_RESULT.search(name)
            or unit.lower().rstrip(".") in _TIME_WORDS):
        return None
    value = g["value"]
    ref = g["ref"].strip()
    if ref[0].isdigit():
        lo, hi = [p.strip() for p in ref.split("-", 1)]
        ref = f"{lo} - {hi}"
    else:
        ref = ref.replace(" ", "")
    return {"test": name, "value": value, "unit": unit, "ref": ref,
            "flag": "", "status": status(value, ref)}


# --- Session 51 (cont. 6): labelled ranges ------------------------------------
_LIMIT_WORDS = (
    (re.compile(r"\b(?:under|below|less\s+than)\s+(?=\d)", re.I), "<"),
    (re.compile(r"\b(?:over|above|more\s+than|greater\s+than)\s+(?=\d)", re.I), ">"),
)
_BAND_CRIT = r"(?:[<>]=?\s?" + _NUM + r"|" + _NUM + r"\s*-\s*" + _NUM + r")"
_BAND_UNIT = r"(?:\s+(?=\S*[A-Za-z%])[^\s\d]\S*)?"
_BAND_LABEL = r"[A-Za-z][A-Za-z\-/]*(?:\s+[A-Za-z][A-Za-z\-/]*){0,4}"
_COLON_TAIL = re.compile(r"\s*:\s*(?P<crit>" + _BAND_CRIT + r")" + _BAND_UNIT + r"\s*$")
_BAND_LINE = re.compile(r"^(?P<label>" + _BAND_LABEL + r")\s*:?\s*(?P<crit>"
                        + _BAND_CRIT + r")" + _BAND_UNIT + r"\s*$")
_BAND_LINE_COLON = re.compile(r"^(?P<label>" + _BAND_LABEL + r")\s*:\s*(?P<crit>"
                              + _BAND_CRIT + r")" + _BAND_UNIT + r"\s*$")
_BAND_MARKER = re.compile(r"\s+(?:recommended|reference|ref\.?)\s+(?:ranges?|values?)"
                          r"\s*:?\s*$", re.I)
_LABEL_WORD = re.compile(r"[A-Za-z][A-Za-z\-/]*$")


def _band_ref(value: str, bands) -> str:
    """Session 51: printed bands as the reference; the value is marked in
    every band it falls in (the _add_bands form)."""
    out = []
    for label, crit in bands:
        label = re.sub(r"\s+", " ", label).strip()
        crit = re.sub(r"\s+", " ", crit).strip()
        mark = " (value in band)" if status(value, crit) == "normal" else ""
        out.append(f"{label} {crit}{mark}")
    return "; ".join(out)


def _value_in_name(row: dict) -> bool:
    """Session 51: the test name holds '<number> <unit>' with the row's own
    unit - the value was taken from later in the line ("PSA 1.13 ng/ml
    under 4 ng/ml" read as 4)."""
    unit = row.get("unit") or ""
    return bool(unit) and re.search(r"(?<![\d.])" + _NUM + r"\s+" + re.escape(unit)
                                    + r"(?!\S)", row["test"]) is not None


def _read(t: str):
    """Session 51: the Session 49 parser, then value - range - unit order;
    readings that took the limit or a later number as the value are refused."""
    row = _parse_line_v1(t)
    if row and ((row["value"].startswith(("<", ">")) and _TRAILING_NUM.search(row["test"]))
                or _value_in_name(row)):
        row = None
    return row or _parse_vru(t)


def _normalize_limits(t: str) -> str:
    """Session 51: 'under 4 ng/ml' -> '<4', 'over 10' -> '>10'; a unit
    repeated after the limit is dropped."""
    for pat, sym in _LIMIT_WORDS:
        t = pat.sub(sym, t)
    return re.sub(r"^(.*\s(\S+)\s+[<>]=?\s?" + _NUM + r")\s+\2\s*$", r"\1", t)


def _read_with_bands(t: str):
    """Session 51: a result with one labelled band at the end of its line
    ("CPK 248 IU/l Female : 29-168"), or ending in 'Recommended Range'
    (the bands follow on the next lines; see _labelled_bands)."""
    m = _COLON_TAIL.search(t)
    if m:
        words = t[:m.start()].split()
        for k in range(1, min(5, len(words))):
            label = words[-k:]
            if not all(_LABEL_WORD.match(w) for w in label):
                break
            head = " ".join(words[:-k])
            row = _read(head) or _read(_normalize_limits(head))
            if row and not row["ref"]:
                row["ref"] = _band_ref(row["value"], [(" ".join(label), m.group("crit"))])
                row["status"] = "see bands"
                return row
        return None
    m = _BAND_MARKER.search(t)
    if m:
        row = _read(t[:m.start()])
        if row and not row["ref"]:
            return row
    return None


def _labelled_bands(row: dict, lines: list, i: int) -> set:
    """Session 51: more bands on the lines below a result: 'Male : 30-200'
    under 'CPK ... Female : 29-168', or the 'label range' lines under a
    '... Recommended Range' result (Vitamin D). A line that is itself a
    result ends the block. Bands are alternatives (sex, smoking) or
    categories, so the program does not pick one: 'see bands'. Returns the
    band lines used, so they are not read again."""
    text = lines[i].strip().translate(_SYMBOLS)
    if row["status"] == "see bands" and ";" not in row["ref"] and _COLON_TAIL.search(text):
        pat = _BAND_LINE_COLON
    elif not row["ref"] and _BAND_MARKER.search(text):
        pat = _BAND_LINE
    else:
        return set()
    bands, used = [], set()
    for j in range(i + 1, min(len(lines), i + 7)):
        m = pat.match(lines[j].strip().translate(_SYMBOLS))
        if not m or parse_line(lines[j]):
            break
        bands.append((m.group("label"), m.group("crit")))
        used.add(j)
    if bands:
        more = _band_ref(row["value"], bands)
        row["ref"] = row["ref"] + "; " + more if row["ref"] else more
        row["status"] = "see bands"
    return used



_NOTE_WORDS = re.compile(r"(?i)\b(?:normal|optimal|desirable|borderline|high|low|risk|"
                         r"factors?|target|patients?|adults?|ref|recommended|ideal|goal)\b")
_NOTE_KEEP = re.compile(r"(?i)\b(?:high|low)[\s-]+(?:density|sensitivity)\b")


def _is_note_row(row: dict) -> bool:
    """Session 51 (cont. 7): a reference-note line read as a row ("Normal :
    < 1.7 mmol/L", "Target in patients 0-1 risk factors : < 3.4 mmol/L").
    No printed range (or a range as the value), no H/L flag, and a note word
    in the test name. 'high/low density' and 'high/low sensitivity' do not
    count, so 'High Sensitivity CRP 0.8 mg/L' stays a result."""
    if row.get("flag"):
        return False
    if row.get("ref") and not re.search(r"\d\s*-\s*\d", str(row.get("value", ""))):
        return False
    return bool(_NOTE_WORDS.search(_NOTE_KEEP.sub(" ", row.get("test", ""))))


def parse_line(line: str):
    """One result row (dict) or None if the line is not a lab result.
    Session 51: the Session 49 rules run first (_parse_line_v1); then other
    labs' layouts: one up/down arrow anywhere is the H/L flag, a leading row
    number is dropped, value - range - unit order is read, and readings that
    took the reference limit or a later number as the value are refused.
    Session 51 (cont. 6): 'under/over N' limits and labelled bands."""
    text = line.strip().translate(_SYMBOLS)
    arrow = ""
    if len(_ARROW.findall(text)) == 1:
        m = _ARROW.search(text)
        arrow = "H" if m.group(1) == "\u2191" else "L"
        text = (text[:m.start()] + " " + text[m.end():]).strip()
    tries = [text]
    if _ROW_NO.match(text):
        tries.append(_ROW_NO.sub("", text, count=1))
    for t in tries:
        row = _read(t)
        if not row:
            n = _normalize_limits(t)
            row = _read(n) if n != t else None
        row = row or _read_with_bands(t)
        if row:
            if arrow and not row["flag"]:
                row["flag"] = arrow
            if _is_note_row(row):
                return None
            return row
    return None


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
    if _numbered_row(text):
        return None  # Session 51: a numbered row, not a nameless value
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
_URINE_START = re.compile(r"^\s*URINALYSIS\b")  # upper case: not "Urinalysis CLAB-..."
_URINE_END = re.compile(r"Released By", re.I)
_URINE_MAX = 60  # lines; guard when no "Released By" follows
_PAGE_BREAK = re.compile(r"^--- page \d+ \(")  # cli.py joins pages with this line



# Session 51 (cont. 9): start of the English name of a urine test. Prefixes, so
# AI misspellings ('Urobiligen') still match. Names shared with blood tests
# (Glucose, Protein, Blood, Bilirubin) cannot be told apart by name.
_URINE_NAME = re.compile(
    r"(?i)(?:ph\b|sp\b|specific\s+gravity|protein|glucose|ketone|bilirubin|urobil|"
    r"blood|nitrit|leuc|leuk|rbc|wbc|epith|ep\.?\s*cells?\b|cast|granular|hyaline|crystal|bacteria|"
    r"yeast|mucu|muco|colou?r|clarity|appearance|others?\b)")


def _mark_urine(row: dict, in_urine: bool = False) -> None:
    """Session 49: a urine row - unit per field (/HPF, /LPF), or any row inside
    the URINALYSIS ... Released By section (Casts, Colour, Specific Gravity) - gets
    ' - Urine' after its English name, so 'WBC 白血球' NIL cell/HPF differs from
    the blood 'WBC 白血球' 4.9 x10e9/L in the same file. The Chinese part is kept
    (lab style 'pH - Urine 酸鹼度'); names already saying Urine are left alone."""
    if re.search(r"\burine\b", row["test"], re.I):
        return
    m = re.match(r"([\x00-\x7f]+?)\s*([^\x00-\x7f].*)?$", row["test"])
    if not m or not m.group(1).strip():
        return
    # Session 51 (cont. 9): inside a URINALYSIS section only known urine test
    # names are marked; a /HPF or /LPF unit is marked anywhere.
    if not _PER_FIELD.search(row["unit"]) and not (
            in_urine and _URINE_NAME.match(m.group(1).strip())):
        return
    rest = (m.group(2) or "").strip()
    row["test"] = f"{m.group(1).strip()} - Urine" + (f" {rest}" if rest else "")



# Session 51 (cont. 10): urine rows printed as name - result [*] - reference
# [- unit] ("Blood 尿血 Trace * Negative", "Hyaline Cast 透明柱體 Nil Nil /HPF",
# "RBC 紅血球 1 - 2 < 5 cells/ul"). Used only inside a URINALYSIS section and
# only when parse_line found no row or a row with no reference.
_PAIR_TEXT = r"NEGATIVE|POSITIVE|TRACE|NIL|NOT\s+SEEN|[1-4]?\+"
_PAIR_NUM = r"[<>]=?\s?" + _NUM + "|" + _NUM + r"\s*-\s*" + _NUM + "|" + _NUM
_URINE_PAIR = re.compile(
    r"^(?P<name>[A-Za-z][^<>*]*?)\s+(?P<value>" + _PAIR_TEXT + "|" + _PAIR_NUM + r")"
    r"(?P<star>\s*\*)?\s+(?P<ref>" + _PAIR_TEXT + "|" + _PAIR_NUM + r")"
    r"(?:\s+(?P<unit>(?=\S*[A-Za-z%])[^\s\d]\S*))?\s*$", re.I)
_NEG_REF = ("negative", "nil", "not seen")


def _pair_text_status(value: str, ref: str) -> str:
    """Text result against a text reference: NEGATIVE/NIL/NOT SEEN normal;
    TRACE HIGH against negative/nil, normal against trace; +, 1+ to 4+ and
    POSITIVE HIGH against negative/nil/trace. Anything else: unclear."""
    r = ref.lower()
    neg = r in _NEG_REF
    if value in ("NEGATIVE", "NIL", "NOT SEEN"):
        return "normal" if neg or "trace" in r else "unclear"
    if value == "TRACE":
        return "HIGH" if neg else "normal" if "trace" in r else "unclear"
    if value == "POSITIVE" or value.endswith("+"):
        return "HIGH" if neg or "trace" in r else "unclear"
    return "unclear"


def _parse_urine_pair(line: str):
    """Session 51 (cont. 10): see _URINE_PAIR. '*' is the report's flag."""
    text = line.strip().translate(_SYMBOLS)
    m = _URINE_PAIR.match(text)
    if not m:
        return None
    name = re.sub(r"\s+", " ", m.group("name")).strip()
    if (name.endswith(("-", ":")) or _NOT_RESULT.search(name)
            or re.search(r"(?<![\w.])\d", name)):
        return None
    value = re.sub(r"\s+", " ", m.group("value")).strip()
    ref = re.sub(r"\s+", " ", m.group("ref")).strip()
    unit = m.group("unit") or ""
    v_text = re.fullmatch(_PAIR_TEXT, value, re.I) is not None
    r_text = re.fullmatch(_PAIR_TEXT, ref, re.I) is not None
    rng = None if v_text else re.fullmatch("(" + _NUM + r")\s*-\s*(" + _NUM + ")", value)
    if v_text:
        value = value.upper()
    elif rng:
        value = f"{rng.group(1)}-{rng.group(2)}"
    else:
        value = value.replace(" ", "")
    rr = None if r_text else re.fullmatch("(" + _NUM + r")\s*-\s*(" + _NUM + ")", ref)
    if r_text:
        ref = ref[0].upper() + ref[1:].lower()
    elif rr:
        ref = f"{rr.group(1)} - {rr.group(2)}"
    else:
        ref = ref.replace(" ", "")
    if v_text and r_text:
        st = _pair_text_status(value, ref)
    elif v_text or r_text:
        st = "unclear"
    elif rng:
        a, b = status(rng.group(1), ref), status(rng.group(2), ref)
        st = a if a == b else "no range" if "no range" in (a, b) else "unclear"
    else:
        st = status(value, ref)
    return {"test": name, "value": value, "unit": unit, "ref": ref,
            "flag": "*" if m.group("star") else "", "status": st}


def parse_results(described) -> list[dict]:
    """Rows from every transcription / text layer (photos are skipped)."""
    rows = []
    for name, kind, body in described:
        if kind == "photo description":
            continue
        lines = (body or "").splitlines()
        urine_from = None
        used = set()
        for i, line in enumerate(lines):
            if _URINE_START.match(line):
                urine_from = i
            elif urine_from is not None and (_URINE_END.search(line)
                                             or _PAGE_BREAK.match(line)
                                             or i - urine_from > _URINE_MAX):
                urine_from = None
            if i in used:
                continue
            row = parse_line(line)
            if urine_from is not None and (row is None or not row["ref"]):
                row = _parse_urine_pair(line) or row
            row = row or _parse_nameless(lines, i)
            if row:
                _mark_urine(row, urine_from is not None)
                if not row["ref"] and re.fullmatch(r"(?:[<>]=?)?" + _NUM, row["value"]):
                    _add_bands(row, lines[i + 1:])
                used.update(_labelled_bands(row, lines, i))
                row["source"] = name
                rows.append(row)
    return rows


# --- checks on the AI answer -------------------------------------------------

_ABNORMAL = re.compile(r"\b(elevated|elevations?|raised|high|increased|low|decreased|"
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
_EXCEPT_CLAUSE = re.compile(
    r"\b(?:apart from|aside from|other than|besides|save for|"
    r"with the exception of|except(?:\s+for)?)\b", re.I)


def _claim_part(s: str) -> str:
    """Session 50: sentence s without its exception clauses, so "Urinalysis
    normal apart from protein 1+" does not call Protein 1+ normal. A clause runs
    from 'apart from', 'aside from', 'other than', 'besides', 'save for',
    'with the exception of' or 'except (for)' to the next comma or semicolon,
    else to the end of the sentence. "Apart from protein 1+, urine blood is
    normal" keeps ", urine blood is normal"."""
    while True:
        m = _EXCEPT_CLAUSE.search(s)
        if m is None:
            return s
        end = re.search(r"[,;]", s[m.end():])
        s = s[:m.start()] + (s[m.end() + end.start():] if end else "")


def _row_named(s: str, r: dict) -> bool:
    """Session 49: sentence s names row r - a number value cited as a value,
    or (text values such as RED, 1+, TRACE) the first word of the test name
    and the value both in the sentence; for a urine row also the test word
    next to 'urine'/'urinary' ("urine protein", "protein in the urine")."""
    value = r["value"]
    if re.fullmatch(r"(?:[<>]=?)?" + _NUM, value):
        return _cites_row(s, r, value.lstrip("<>="))
    words = r["test"].split()
    key = re.sub(r"[^a-z]", "", words[0].lower()) if words else ""
    if len(key) < 3:
        return False
    key_pat = r"colou?r" if key in ("colour", "color") else re.escape(key)
    if re.search(r"\b" + key_pat + r"\b", s, re.I) is None:
        return False
    if re.search(r"(?<!\w)" + re.escape(value) + r"(?!\w)", s, re.I):
        return True
    if key == "urine" or not re.search(r"\burine\b", r["test"], re.I):
        return False
    return re.search(r"\burin(?:e|ary)\s+(?:\w+\s+)?" + key_pat + r"\b"
                     r"|\b" + key_pat + r"\s+(?:in|on)\s+(?:the\s+)?urine\b",
                     s, re.I) is not None


# --- Session 51: fewer false warnings in check_answer ------------------------
_TREND = re.compile(
    r"\bfrom\s+(?:[<>]=?\s?)?" + _NUM + r"(?:\s?[^\s\d,;()]+)?"
    r"(?:\s+to\s+|\s*(?:\u2192|->)\s*)(?:[<>]=?\s?)?" + _NUM, re.I)
_OUTSIDE_NORMAL = re.compile(
    r"\b(?:above|below|outside|beyond|exceed(?:s|ed|ing)?|higher\s+than|lower\s+than)"
    r"\s+(?:the\s+)?(?:upper\s+|lower\s+)?(?:limits?\s+of\s+)?(?:the\s+)?normal\b", re.I)
_UNIT_WORDS = {"g", "mg", "ug", "ng", "pg", "mmol", "umol", "nmol", "pmol", "u",
               "iu", "mu", "miu", "ku", "fl", "mmhg", "meq", "sec", "cells", "cell"}


def _unit_key(unit: str) -> str:
    """Session 51: unit for comparison - case, spaces, micro sign; IU = U."""
    k = re.sub(r"\s+", "", unit).lower().replace("\u00b5", "u").replace("\u03bc", "u")
    return re.sub(r"^iu(?=/|$)", "u", k.rstrip("."))


def _cites_row(s: str, r: dict, num: str, trend: bool = False) -> bool:
    """Session 51: sentence s cites num as the value of row r. As _value_cited
    (not a range end, not a time span, not part of a longer number), and also
    not glued to letters ("CA19-9"), not the start of a range ("19-9"), not
    followed by a different unit ("69 mm/hr" is not 69 g/L), and - when trend
    is set - not inside "from X to Y" / "X -> Y" (a change over time)."""
    text = _pow10(s.replace("*", ""))  # Session 52
    spans = [m.span() for m in _TREND.finditer(text)] if trend else []
    row_unit = _unit_key(_pow10(r.get("unit") or ""))  # Session 52
    for m in re.finditer(r"(?<![\dA-Za-z.])" + re.escape(num) + r"(?!\.?\d)", text):
        before, after = text[:m.start()], text[m.end():]
        if re.search(r"\d\s*[-\u2013\u2014]\s*$", before):
            continue
        if re.match(r"\s*[-\u2013\u2014]\s*\d", after):
            continue
        w = re.match(r"\s*([A-Za-z]+)\b", after)
        if w and w.group(1).lower() in _TIME_WORDS:
            continue
        if any(a <= m.start() < b for a, b in spans):
            continue
        u = re.match(r"\s?(%|[A-Za-z\u00b5\u03bc][A-Za-z0-9\u00b5\u03bc/^.]*)", after)
        if u and row_unit:
            tok = u.group(1)
            key = _unit_key(tok)
            unit_like = "/" in tok or "%" in tok or "^" in tok or key in _UNIT_WORDS
            if unit_like and key != row_unit:
                continue
        return True
    return False


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
            if any(_clause_cites(c, r) and _abnormal_for_row(c, r)
                   and not _NORMAL.search(c)
                   for c in _clauses(s)):  # Session 51 (cont. 19)
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
            c = _claim_part(s)
            if (_row_named(c, r) and _NORMAL.search(_OUTSIDE_NORMAL.sub(" ", c))
                    and not _abnormal_claim(c) and not _NOT_NORMAL.search(c)):
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


# Session 51 (cont. 12): abnormal results the answer never names. check_answer
# warns when a result is called the wrong thing; this warns when an abnormal
# result (HIGH, LOW, ABNORMAL, or 'see bands' with the lab's own flag) is left
# out. 'Named' = a distinctive English word of the test name in the answer; for
# a urine row the word must be in a sentence that says urine / urinary.
_MENTION_COMMON = {"total", "free", "serum", "count", "cell", "cells", "ratio", "test",
                   "level", "urine", "blood", "fasting", "random", "direct", "indirect",
                   "and", "the", "with"}
_URINE_SENTENCE = re.compile(r"(?i)\burin(?:e|ary|alysis)\b")


def _english_test_name(test: str) -> str:
    s = test.replace(" - Urine", " ")
    s = re.sub(r"[^\x20-\x7e]+", " ", s)
    return re.sub(r"\s+", " ", s).strip(" ,;:*#")


def _value_in_sentence(value: str, s: str) -> bool:
    """Session 51 (cont. 15): a urine result counts as named only when its value
    is in the same sentence ("urine protein 1+", "trace blood in the urine",
    "RBC 10-17"); "urine protein quantification" alone is not enough."""
    v = (value or "").strip().replace("\u2013", "-").replace("\u2014", "-")
    if not v:
        return True
    t = s.replace("\u2013", "-").replace("\u2014", "-")
    if v == "+":
        return re.search(r"(?<![\w+])\+(?![\w+])", t) is not None
    pat = re.escape(v).replace(r"\-", r"\s*-\s*")
    return re.search(r"(?<![\w.])" + pat + r"(?!\w)", t, re.I) is not None


def _is_mentioned(name: str, urine: bool, sentences, value: str = "") -> bool:
    words = [w for w in re.findall(r"[A-Za-z][A-Za-z0-9]+", name)
             if len(w) >= 3 and w.lower() not in _MENTION_COMMON]
    if not words:
        words = [w for w in re.findall(r"[A-Za-z]+", name) if len(w) >= 3] or [name]
    pats = _mention_pats(name, words)  # Session 52 (cont. 1): plurals; A/G
    for s in sentences:
        if urine and not _URINE_SENTENCE.search(s):
            continue
        if any(p.search(s) for p in pats) and (not urine or _value_in_sentence(value, s)):
            return True
    return False


def unmentioned_abnormal(rows, answer) -> list:
    """Session 51 (cont. 12): one warning listing abnormal results the answer
    never names (urine results grouped, repeated names once), or []. Known
    limit: a word used in another sense ('C-reactive protein') counts as named."""
    sentences = [_named_protein(_RATIO_PHRASE.sub(" ratio ", s))  # Session 51 (cont. 18)
                 for s in _sentences(answer or "")]
    urine_sentences = [_PLURAL_ABBR.sub(r"\1", s) for s in sentences]
    found = {False: [], True: []}
    for r in rows:
        st = r.get("status")
        if not (st in ("HIGH", "LOW", "ABNORMAL") or (st == "see bands" and r.get("flag"))):
            continue
        urine = " - Urine" in r.get("test", "") or bool(_PER_FIELD.search(r.get("unit") or ""))
        name = _english_test_name(r.get("test", ""))
        if not name or _is_mentioned(name, urine, urine_sentences if urine else sentences, r.get("value") or ""):
            continue
        if name.lower() not in [n.lower() for n in found[urine]]:
            found[urine].append(name)
    parts = []
    if found[False]:
        parts.append(", ".join(found[False]))
    if found[True]:
        parts.append("urine: " + ", ".join(found[True]))
    return ["Abnormal results not mentioned in the answer: " + "; ".join(parts)] if parts else []


# Session 51 (cont. 13): the CKD stage named in the answer against the eGFR
# (KDIGO G categories). eGFR from the table; if the table has none, from the
# answer. Only stage vs eGFR is checked, not whether CKD is the right diagnosis.
_KDIGO_G = (("G1", 90.0, float("inf")), ("G2", 60.0, 90.0), ("G3a", 45.0, 60.0),
            ("G3b", 30.0, 45.0), ("G4", 15.0, 30.0), ("G5", 0.0, 15.0))
_KDIGO_TEXT = {"G1": ">=90", "G2": "60-89", "G3a": "45-59", "G3b": "30-44",
               "G4": "15-29", "G5": "<15"}
_STAGE_SETS = {"1": {"G1"}, "2": {"G2"}, "3": {"G3a", "G3b"}, "3a": {"G3a"},
               "3b": {"G3b"}, "4": {"G4"}, "5": {"G5"}}
_EGFR_NAME = re.compile(r"(?i)\be?GFR\b|estimated\s+glomerular")
_EGFR_IN_TEXT = re.compile(r"(?i)\beGFR\b[^.\d<>]{0,40}?(?P<v>(?:[<>]=?\s?)?\d+(?:\.\d+)?)")
_CKD_STAGE = re.compile(
    r"(?i)\b(?:CKD|chronic\s+kidney\s+disease)(?:\s*\(CKD\))?[\s,:*-]*(?:stage\s*|G)"
    r"(?P<a>[1-5])(?P<x>[ab])?(?!\d|\.\d)"
    r"|\bstage\s*(?P<b>[1-5])(?P<y>[ab])?\s+(?:CKD|chronic\s+kidney\s+disease)")
_STAGE_SKIP = re.compile(r"(?i)\b(?:not|no|without|rule[sd]?\s+out|exclude[sd]?|unlikely|"
                         r"risk|progress\w*|prevent\w*|avoid\w*)\b")


def _egfr_groups(value: str) -> set:
    m = re.fullmatch(r"([<>]=?)?(\d+(?:\.\d+)?)", (value or "").replace(" ", ""))
    if not m:
        return set()
    op, n = m.group(1) or "", float(m.group(2))
    if op.startswith(">"):
        return {g for g, lo, hi in _KDIGO_G if hi > n}
    if op.startswith("<"):
        return {g for g, lo, hi in _KDIGO_G if lo < n}
    return {g for g, lo, hi in _KDIGO_G if lo <= n < hi}


def ckd_stage_mismatch(rows, answer) -> list:
    """Session 51 (cont. 13): one warning when a CKD stage named in the answer
    fits none of the eGFR values (KDIGO), or []. A stage after 'not', 'rule
    out', 'unlikely', 'risk', 'progress' ... in the same sentence is skipped."""
    text = answer or ""
    egfr = []
    for r in rows:
        if _EGFR_NAME.search(_english_test_name(r.get("test", ""))):
            g = _egfr_groups(r.get("value", ""))
            if g:
                egfr.append((r["value"].replace(" ", ""), "table", g))
    if not egfr:
        for m in _EGFR_IN_TEXT.finditer(text):
            g = _egfr_groups(m.group("v"))
            if g:
                egfr.append((m.group("v").replace(" ", ""), "answer", g))
    if not egfr:
        return []
    named = []
    for s in _sentences(text):
        for m in _CKD_STAGE.finditer(s):
            if _STAGE_SKIP.search(s[:m.start()]):
                continue
            st = (m.group("a") or m.group("b")) + (m.group("x") or m.group("y") or "").lower()
            if st not in named:
                named.append(st)
    bad = [st for st in named if all(not (_STAGE_SETS[st] & g) for _, _, g in egfr)]
    if not bad:
        return []
    vals = []
    for v, src, g in egfr:
        gs = sorted(g)
        item = (f"eGFR {v} ({src}) = {', '.join(gs)} "
                f"({', '.join(_KDIGO_TEXT[x] for x in gs)})")
        if item not in vals:
            vals.append(item)
    return ["CKD stage in the answer does not match the eGFR (KDIGO): stage "
            + ", ".join(bad) + " named; " + "; ".join(vals)]


# Session 51 (cont. 14): an eGFR row printed as name + value only
# ("e-GFR <Chinese>, <Chinese> 68"); the unit and the reference are in notes
# below the table ("eGFR unit: ml/min/1.73m2", "eGFR >90 is normal unless ...").
# Read only when the other readers find no row, and only for eGFR. The value is
# kept as printed; no unit or reference is taken from the notes, so the status
# is 'no range'. Note lines that start with a number ("2. eGFR >90 ...") are not read.
_EGFR_ONLY = re.compile(
    r"^\s*(e-?GFR\b[^\d<>=\u2264\u2265]*?)\s*([<>]=?|\u2264|\u2265)?\s*(\d+(?:\.\d+)?)\s*$",
    re.I)
_parse_line_before_egfr = parse_line


def _parse_egfr_only(line: str):
    m = _EGFR_ONLY.match(line)
    if not m:
        return None
    sign = m.group(2) or ""
    sign = {"\u2264": "<=", "\u2265": ">="}.get(sign, sign)
    return {"test": m.group(1).strip(" ,:"), "value": sign + m.group(3),
            "unit": "", "ref": "", "flag": "", "status": "no range"}


def parse_line(line: str):
    """Session 51 (cont. 14): parse_line as before, then the eGFR value-only row."""
    row = _parse_line_before_egfr(line)
    return row if row is not None else _parse_egfr_only(line)


# Session 51 (cont. 17): a negated abnormal word ("no evidence of anaemia",
# "not elevated") is not an abnormal claim. Used where _ABNORMAL.search was used.
_NEG_BEFORE = re.compile(
    r"(?i)\b(?:no|not|without|absence\s+of|negative\s+for)\b(?:\s+[\w-]+){0,3}\s*$")


def _abnormal_claim(s: str):
    t = (s or "").replace("*", "")
    for m in _ABNORMAL.finditer(t):
        before = re.split(r"[,;:()]", t[:m.start()])[-1]
        if not _NEG_BEFORE.search(before):
            return m
    return None


# Session 51 (cont. 17): "no proteinuria", "no haematuria confirmed" against an
# abnormal urine result. Known limits: "proteinuria is absent" (negation after
# the term) is not read; "no data on proteinuria" may warn.
_DENIED_TERMS = (
    (r"proteinuria|albuminuria", ("protein", "albumin")),
    (r"ha?ematuria", ("blood", "rbc")),
    (r"pyuria|leu[ck]ocyturia", ("wbc", "leuk", "leucocyte", "leukocyte")),
    (r"glu[ck]osuria|glycosuria", ("glucose",)),
    (r"ketonuria", ("ketone",)),
)
_DENY_RE = [(re.compile(r"(?i)\b(?:no|not|without|absence\s+of|negative\s+for|nil)\b"
                        r"(?:,?\s+(?!(?:but|however|although|though|yet|whereas|except|data|information|results?|records?|mention|tests?|tested|testing|measured|assessed|checked|exclude[sd]?|rule[sd]?)\b)[\w-]+){0,3}?,?\s+(?:" + t + r")\b"), keys)
            for t, keys in _DENIED_TERMS]


def denied_urine_findings(rows, answer) -> list:
    """Session 51 (cont. 17): warnings for sentences that deny an abnormal urine
    result by its medical term ("No proteinuria" with urine Protein 1+)."""
    urine = []
    for r in rows:
        if r.get("status") not in ("HIGH", "ABNORMAL"):
            continue
        if " - Urine" not in r.get("test", "") and not _PER_FIELD.search(r.get("unit") or ""):
            continue
        words = r.get("test", "").split()
        key = re.sub(r"[^a-z]", "", words[0].lower()) if words else ""
        if key:
            urine.append((key, r))
    out = []
    for s in _sentences(answer or ""):
        t = s.replace("*", "")
        hit = []
        for pat, keys in _DENY_RE:
            if pat.search(t):
                for key, r in urine:
                    if key.startswith(keys) and r not in hit:
                        hit.append(r)
        if hit:
            q = s.strip()
            q = q if len(q) <= 200 else q[:197] + "..."
            names = "; ".join(f"{r['test']} {r['value']} (range {r.get('ref') or '-'})"
                              for r in hit)
            out.append(f'The answer may deny an abnormal urine result: {names}: "{q}"')
    return out

# Session 51 (cont. 18): text read by the not-mentioned check (unmentioned_abnormal).
# A urine albumin/protein-to-creatinine ratio does not name serum Albumin, Protein or
# Creatinine. 'RBCs' -> 'RBC' only for urine rows: urine 'RBCs/ul' is not blood RBC.
_RATIO_PHRASE = re.compile(
    r"(?i)\b(?:albumin|protein)(?:\s*[-:/]\s*|\s+)(?:to(?:\s*-\s*|\s+))?creatinine\s+ratio\b")
_PLURAL_ABBR = re.compile(r"\b([A-Z]{2,6})s\b")

# Session 51 (cont. 19): check_answer judges 'in-range result called abnormal' per
# clause ('... mild elevation in AFP (2.24 ng/ml), but ... within ...'). For a row
# whose value is 10, the '10' of a power-of-ten unit ('x 10^12', 'x10e9') is not that
# value ('GGT 10' vs '4.45 x 10(sup)12/L'); other rows read the clause unchanged so
# 'WBC 4.9 x10e9/L' still matches its unit. For a one-sided range 'low' (range '<X')
# or 'high' (range '>X') is not an abnormal claim ('CRP is low at 0.8 mg/L (<5.0)').
_CONTRAST = re.compile(r"\s*;\s*|,?\s*\b(?:but|however|although|though|whereas)\b", re.I)
_EXP_TEN = re.compile(r"([\u00d7xX]\s?)10(?=\s?\^\s?[-\u2212]?\d"
                      r"|\s?[\u207b\u2070\u00b9\u00b2\u00b3\u2074-\u2079]|[eE]\d)")
_LOW_WORDS = {"low", "decreased", "reduced"}
_HIGH_WORDS = {"elevated", "elevation", "elevations", "raised", "high", "increased"}


def _clauses(s: str) -> list:
    """Session 51 (cont. 19): sentence s split at contrast words and semicolons."""
    return [c for c in _CONTRAST.split(s) if c.strip()] or [s]


def _clause_cites(c: str, r: dict) -> bool:
    """Session 51 (cont. 19): clause c cites row r; for a row whose value is 10 the
    '10' of a power-of-ten unit is not read as that value."""
    try:
        ten = float(r["value"].lstrip("<>=")) == 10
    except ValueError:
        ten = False
    if ten:
        c = _EXP_TEN.sub(r"\1TEN", c)
    return _cites_row(c, r, r["value"], trend=True)


def _abnormal_for_row(c: str, r: dict):
    """Session 51 (cont. 19): like _abnormal_claim, but for a range with only an upper
    limit ('<5.0') 'low' words, and with only a lower limit ('>1.03') 'high' words,
    are not an abnormal claim."""
    t = (c or "").replace("*", "")
    ref = (r.get("ref") or "").strip()
    for m in _ABNORMAL.finditer(t):
        before = re.split(r"[,;:()]", t[:m.start()])[-1]
        if _NEG_BEFORE.search(before):
            continue
        w = m.group(0).lower()
        if (ref.startswith("<") and w in _LOW_WORDS) or (ref.startswith(">") and w in _HIGH_WORDS):
            continue
        return m
    return None

# Session 51 (cont. 20): band-name check (word list approved by the user). A 'see
# bands' row whose band labels are all in the list warns when a clause gives the
# row's value and names a band the value is not in. A band word right after a range
# and 'as' ('10-30 as insufficient') is a definition; negated words do not count.
_BAND_WORDS = (
    ("insufficient", re.compile(r"(?i)\binsufficien(?:t|cy)\b")),
    ("deficient", re.compile(r"(?i)\bdeficien(?:t|cy)\b")),
    ("sufficient", re.compile(r"(?i)\b(?:sufficien(?:t|cy)|adequate|enough)\b")),
    ("toxic", re.compile(r"(?i)\b(?:toxic(?:ity|osis)?|excess(?:ive)?)\b")),
)
_DEF_BEFORE = re.compile(r"(?:[<>]=?\s?|\d\s*[-\u2013\u2014]\s*)" + _NUM
                         + r"(?:\s*[A-Za-z/]+)?\s+as\s+$", re.I)


def _band_kind(label: str):
    t = label.lower()
    if "insufficien" in t:
        return "insufficient"
    if "deficien" in t or "lack" in t:
        return "deficient"
    if "sufficien" in t or "enough" in t or "adequate" in t:
        return "sufficient"
    if "toxic" in t:
        return "toxic"
    return None


def _bands_of(r: dict):
    """Session 51 (cont. 20): [(label, kind, value_in_band)] for a 'see bands' row,
    or None when a band label is not in the word list (sex / smoker bands)."""
    out = []
    for part in (r.get("ref") or "").split(";"):
        part = part.strip()
        if not part:
            continue
        m = _CRIT.search(part)
        label = (part[:m.start()] if m else part).strip()
        kind = _band_kind(label)
        if kind is None:
            return None
        out.append((label, kind, "(value in band)" in part))
    return out or None


def band_name_mismatch(rows, answer) -> list:
    """Session 51 (cont. 20): warnings for a band name in the answer that does not
    match the band the value is in ('35.9 ng/ml ... insufficient' with 35.9 in
    'Enough 30-100')."""
    out = []
    sentences = _sentences(answer or "")
    for r in rows:
        if r.get("status") != "see bands":
            continue
        bands = _bands_of(r)
        if not bands:
            continue
        inside = {k for _, k, hit in bands if hit}
        kinds = {k for _, k, _ in bands}
        if not inside:
            continue
        found = None
        for s in sentences:
            for c in _clauses(s):
                if not _clause_cites(c, r):
                    continue
                t = c.replace("*", "")
                for kind, pat in _BAND_WORDS:
                    if kind in inside or kind not in kinds:
                        continue
                    for m in pat.finditer(t):
                        before = t[:m.start()]
                        if _DEF_BEFORE.search(before):
                            continue
                        if _NEG_BEFORE.search(re.split(r"[,;:()]", before)[-1]):
                            continue
                        found = (m.group(0), s)
                        break
                    if found:
                        break
                if found:
                    break
            if found:
                break
        if found:
            word, s = found
            q = s.strip()
            q = q if len(q) <= 200 else q[:197] + "..."
            label = "; ".join(lb for lb, _, hit in bands if hit)
            what = " ".join(x for x in (r.get("test"), r.get("value"), r.get("unit")) if x)
            out.append(f'The answer may name the wrong band: {what} is in "{label}"; '
                       f'the answer says "{word}": "{q}"')
    return out

# Session 52: power-of-ten units are written one way before a row is matched
# ('x 10^12', 'x10e12', 'x 10(sup)12' -> 'x10^12'), in the answer and in the row unit.
# After this the 'x' is not read as 'times', and the '10' is not read as a value.
_POW10 = re.compile(r"(?<![A-Za-z])[\u00d7xX]\s?10\s?(?:\^\s?|[eE])([-\u2212]?\d+)"
                    r"|(?<![A-Za-z])[\u00d7xX]\s?10\s?(\u207b?[\u2070\u00b9\u00b2\u00b3"
                    r"\u2074-\u2079]+)")
_SUP_DIGITS = str.maketrans("\u2070\u00b9\u00b2\u00b3\u2074\u2075\u2076\u2077\u2078\u2079"
                            "\u207b", "0123456789-")


def _pow10(s: str) -> str:
    """Session 52: one written form for power-of-ten units ('x10^12/L')."""
    def rep(m):
        e = m.group(1) if m.group(1) is not None else m.group(2).translate(_SUP_DIGITS)
        return "x10^" + e.replace("\u2212", "-")
    return re.sub(r"(x10\^-?\d+)\s+/", r"\1/", _POW10.sub(rep, s or ""))


# Session 52: 'C-reactive protein' / 'Bence Jones protein' do not name Protein(Total)
# in the not-mentioned check.
_NAMED_PROTEIN = re.compile(r"(?i)\b(c[-\s]?reactive|bence[-\s]+jones)\s+proteins?\b")


def _named_protein(s: str) -> str:
    return _NAMED_PROTEIN.sub(
        lambda m: m.group(1) + (" CRP" if "reactive" in m.group(1).lower() else " BJP"), s)


# Session 52: a denial after the term ('Proteinuria is absent', 'was not seen');
# the words between stop at contrast words.
_DENY_RE = _DENY_RE + [
    (re.compile(r"(?i)\b(?:" + t + r")\b(?:\s+(?!(?:but|however|although|though|yet|"
                r"whereas|except)\b)[\w-]+){0,2}?\s+(?:absent|not\s+(?:seen|detected|"
                r"present|found)|negative|nil)\b"), keys)
    for t, keys in _DENIED_TERMS]

# Session 52: Colour / Appearance with a reference word ('Colour 顏色 Yellow Yellow',
# any case) and Crystals rows ('Crystals (1) 結晶 Nil'). A colour equal to its
# reference is normal; RED, BROWN, TURBID stay ABNORMAL; any other differing word is
# unclear. Crystals without a reference are 'no range'.
_DESC_PAIR = re.compile(r"(?i)^(?P<name>" + _DESC_NAME + r"(?:\s+[^\x00-\x7f]+)?)\s+"
                        r"(?P<value>" + _DESC_WORDS + r")(?:\s+(?P<ref>" + _DESC_WORDS
                        + r"))?(?:\s+-)?\s*$")
_CRYSTALS = re.compile(r"(?i)^(?P<name>Crystals?(?:\s*\(\d+\))?(?:\s+[^\x00-\x7f]+)?)\s+"
                       r"(?P<value>NIL|NEGATIVE|NOT\s+SEEN|PRESENT|FEW|[1-4]?\+)"
                       r"(?:\s+(?P<ref>NIL|NEGATIVE|NOT\s+SEEN))?\s*$")


def _parse_s52_extra(line: str):
    text = line.strip().translate(_SYMBOLS)
    m = _DESC_PAIR.match(text)
    if m:
        value = re.sub(r"\s+", " ", m.group("value")).upper()
        ref = re.sub(r"\s+", " ", m.group("ref") or "").upper()
        st = ("ABNORMAL" if value in _DESC_ABNORMAL else "normal" if ref and ref == value
              else "unclear" if ref else "no range")
        return {"test": re.sub(r"\s+", " ", m.group("name")).strip(), "value": value,
                "unit": "", "ref": ref.title(), "flag": "", "status": st}
    m = _CRYSTALS.match(text)
    if m:
        value = re.sub(r"\s+", " ", m.group("value")).upper()
        ref = re.sub(r"\s+", " ", m.group("ref") or "").capitalize()
        return {"test": re.sub(r"\s+", " ", m.group("name")).strip(), "value": value,
                "unit": "", "ref": ref, "flag": "",
                "status": _text_status(value, ref) if ref else "no range"}
    return None


_parse_line_before_s52 = parse_line


def parse_line(line: str):
    """Session 52: parse_line as before, then Colour-with-reference and Crystals rows."""
    row = _parse_line_before_s52(line)
    return row if row is not None else _parse_s52_extra(line)


# Session 52 (cont. 1): plural test names; A/G Ratio named only as A/G; lone '-' unit column.
_AG_NAME = re.compile(r"(?i)^\s*A\s*/\s*G\b")
_AG_WORDS = re.compile(r"(?i)(?<![A-Za-z])A\s*/\s*G(?![A-Za-z])"
                       r"|\balbumin\s*(?:/|:|-?\s*to\s*-?)\s*globulin\b")


def _plural_pat(w: str) -> str:
    """Session 52 (cont. 1): an ordinary test word also matches with a plural 's'
    ('Platelet' names 'platelets'); short capital forms (RBC, WBC, ESR) stay exact,
    so urine 'RBCs' never names a blood RBC row."""
    if w.isupper() or len(w) < 4:
        return re.escape(w)
    lw = w.lower()
    stem = w[:-1] if lw.endswith("s") and not lw.endswith(("ss", "us")) else w
    return re.escape(stem) + "s?"


def _mention_pats(name: str, words) -> list:
    """Session 52 (cont. 1): patterns that name a row. A/G Ratio is named only by
    'A/G' or 'albumin/globulin', not by any word 'ratio'."""
    if _AG_NAME.match(name):
        return [_AG_WORDS]
    return [re.compile(r"(?i)(?<![A-Za-z])" + _plural_pat(w) + r"(?![A-Za-z])") for w in words]


_DASH_UNIT = re.compile(
    r"^(?P<name>[A-Za-z][A-Za-z0-9 /().,#%+'-]*?)\s+(?P<value>\d+(?:\.\d+)?)\s*"
    r"(?P<arrow>[\u2191\u2193])?\s+-\s+(?P<low>\d+(?:\.\d+)?)\s*-\s*(?P<high>\d+(?:\.\d+)?)\s*$")

_parse_line_before_s52c1 = parse_line


def _parse_dash_unit(line: str):
    """Session 52 (cont. 1): a row whose unit column is a lone '-'
    ('A/G Ratio 2.2 (up arrow) - 0.8 - 2.0'): the dash is dropped and the line is
    read again by the usual rules; refused unless low <= high and the value is kept."""
    m = _DASH_UNIT.match(line.strip().translate(_SYMBOLS))
    if not m or float(m.group("low")) > float(m.group("high")):
        return None
    text = " ".join(x for x in (m.group("name").strip(), m.group("value"), m.group("arrow"),
                                m.group("low") + " - " + m.group("high")) if x)
    row = _parse_line_before_s52c1(text)
    if not row or row.get("value") != m.group("value"):
        return None
    return row


def parse_line(line: str):
    """Session 52 (cont. 1): parse_line as before, then rows with a lone '-' unit."""
    row = _parse_line_before_s52c1(line)
    return row if row is not None else _parse_dash_unit(line)


# Session 52 (cont. 2): white-cell differential re-paired by position (WBC x % check).
_MENTION_COMMON = set(_MENTION_COMMON) | {"absolute"}
_DIFF_CELLS = ("Neutrophils", "Lymphocytes", "Monocytes", "Eosinophils", "Basophils")
_DIFF_NAME = re.compile(r"(?i)^(neutrophils?|lymphocytes?|monocytes?|eosinophils?|basophils?)\b")
_DIFF_ABS_UNIT = r"x\s*10\s*(?:\^|e)?\s*9\s*/\s*L"
_DIFF_ITEM = re.compile(r"(?i)^(?P<value>\d+(?:\.\d+)?)\s*(?P<unit>%|" + _DIFF_ABS_UNIT + r")?\s*(?P<ref>.*)$")
_DIFF_NOVALUE = re.compile(r"(?i)^" + _DIFF_ABS_UNIT + r"(?![A-Za-z])")
_DIFF_CJK = re.compile(r"^[\s\u3400-\u9fff\uf900-\ufaff()\uff08\uff09,]*")


def _diff_stem(s: str) -> str:
    return s.lower().rstrip("s")


def _diff_items(lines):
    """Session 52 (cont. 2): value lines of the differential block in order, named or not."""
    start = next((i for i, s in enumerate(lines) if s.strip().lower() == "differential"), None)
    if start is None:
        start = next((i for i, s in enumerate(lines) if _DIFF_NAME.match(s.strip())), None)
    if start is None:
        return []
    items, began = [], False
    for s in lines[start:]:
        t = s.strip()
        if t.lower() == "differential":
            continue
        if not t:
            if began:
                break
            continue
        name, cn = "", ""
        m = _DIFF_NAME.match(t)
        if m:
            name = m.group(1)
            rest = t[m.end():]
            c = _DIFF_CJK.match(rest)
            cn = re.sub(r"[^\u3400-\u9fff\uf900-\ufaff]", "", c.group(0))
            t = rest[c.end():]
        if _DIFF_NOVALUE.match(t):
            items.append({"name": name, "cn": cn, "value": None, "kind": "none", "unit": "", "ref": ""})
            began = True
            continue
        m = _DIFF_ITEM.match(t)
        if not m:
            break
        unit = m.group("unit") or ""
        items.append({"name": name, "cn": cn, "value": m.group("value"),
                      "kind": "abs" if unit and unit != "%" else "pct",
                      "unit": unit, "ref": m.group("ref").strip()})
        began = True
    return items


def _diff_wbc(lines):
    for s in lines:
        if re.match(r"(?i)^\s*WBC\b", s) and not re.search(r"(?i)urine|cells?\s*/\s*ul", s):
            r = parse_line(s)
            if r and re.search(r"(?i)10\s*(?:\^|e)?\s*9", r.get("unit") or ""):
                try:
                    return float(r["value"])
                except (TypeError, ValueError):
                    pass
    return None


def _diff_plan(lines) -> dict:
    """Session 52 (cont. 2): 'ok' (10 values, % / absolute alternating), 'partial'
    (leading full pairs only), 'missing' (absolute lines without a number), 'fail'
    (names out of order, odd layout or WBC x % check failed) or 'none'."""
    items = _diff_items(lines)
    if not items:
        return {"status": "none"}
    if any(it["kind"] == "none" for it in items):
        return {"status": "missing"}
    has_abs = any(it["kind"] == "abs" for it in items)
    stems = [_diff_stem(c) for c in _DIFF_CELLS]
    named = [_diff_stem(it["name"]) for it in items if it["name"]]
    if named != stems[:len(named)]:
        return {"status": "fail" if has_abs else "none"}
    n, pairs = len(items), 0
    while (pairs < 5 and 2 * pairs + 1 < n and items[2 * pairs]["kind"] == "pct"
           and items[2 * pairs + 1]["kind"] == "abs"):
        pairs += 1
    full = n == 10 and pairs == 5
    partial = (1 <= pairs < 5 and n in (2 * pairs, 2 * pairs + 1)
               and items[-1]["kind"] == ("abs" if n == 2 * pairs else "pct"))
    if not (full or partial):
        return {"status": "fail" if has_abs else "none"}
    wbc = _diff_wbc(lines)
    if wbc is None:
        return {"status": "none"}
    for k in range(pairs):
        exp = wbc * float(items[2 * k]["value"]) / 100
        if abs(float(items[2 * k + 1]["value"]) - exp) > max(0.15, 0.15 * exp):
            return {"status": "fail"}
    cn = {_diff_stem(it["name"]): it["cn"] for it in items if it["name"] and it["cn"]}
    specs = [(_DIFF_CELLS[j // 2], it, j % 2 == 1, cn.get(_diff_stem(_DIFF_CELLS[j // 2]), ""))
             for j, it in enumerate(items)]
    return {"status": "ok" if full else "partial", "specs": specs, "n": n}


def _diff_rows(plan, name):
    out = []
    for cell, it, is_abs, cn in plan["specs"]:
        if is_abs:
            text = f"{cell} (absolute) {it['value']} {it['unit']} {it['ref']}"
        else:
            text = f"{cell} {it['value']} % {it['ref']}"
        row = parse_line(text.strip())
        if not row or row.get("value") != it["value"]:
            return None
        row["test"] = cell + (" (absolute)" if is_abs else "") + (" " + cn if cn else "")
        _mark_urine(row, False)
        row["source"] = name
        out.append(row)
    return out


_parse_results_before_s52c2 = parse_results


def parse_results(described) -> list:
    """Session 52 (cont. 2): parse_results as before; then a white-cell differential whose
    names the AI placed on the wrong lines is re-paired by position (report order, % then
    absolute), only when every pair passes WBC x % = absolute (15%, at least 0.15)."""
    rows = _parse_results_before_s52c2(described)
    for name, kind, body in described:
        if kind == "photo description":
            continue
        plan = _diff_plan((body or "").splitlines())
        if plan["status"] not in ("ok", "partial"):
            continue
        new = _diff_rows(plan, name)
        if not new:
            continue
        src_idx = [i for i, r in enumerate(rows) if r.get("source") == name]
        idx = [i for i in src_idx if " - Urine" not in rows[i].get("test", "")
               and _DIFF_NAME.match(rows[i].get("test", ""))]
        at = idx[0] if idx else (src_idx[-1] + 1 if src_idx else len(rows))
        for i in reversed(idx):
            del rows[i]
        rows[at:at] = new
    return rows


def differential_problems(described) -> list:
    """Session 52 (cont. 2): warnings about the white-cell differential transcription."""
    out = []
    for name, kind, body in described:
        if kind == "photo description":
            continue
        plan = _diff_plan((body or "").splitlines())
        st = plan["status"]
        if st == "missing":
            out.append(f"White-cell differential: absolute counts are missing from the "
                       f"transcription of {name} (unit and range only); only percentages are in the table.")
        elif st == "partial":
            out.append(f"White-cell differential: only {plan['n']} of 10 values were read from "
                       f"{name}; the rest are missing from the transcription.")
        elif st == "fail":
            out.append(f"White-cell differential rows of {name} may be mislabelled (WBC x % does "
                       f"not match the absolute count, or names out of order); check them against the report.")
    return out


# Session 52 (cont. 2): a dipstick grade ('1+', '2+') is not a value.
_DIPSTICK = re.compile(r"(?<![\dA-Za-z.])\d+\+(?!\d)")
_cites_row_before_s52c2 = _cites_row


def _cites_row(s: str, r: dict, num: str, trend: bool = False) -> bool:
    """Session 52 (cont. 2): as before, but a dipstick grade ('1+ protein') is not read
    as the value 1 (false in-range warning for a Basophils 1 % row, run 20261127_173019)."""
    return _cites_row_before_s52c2(_DIPSTICK.sub(" ", s), r, num, trend)


# Session 52 (cont. 3): finding words (lymphopenia, anaemia, hypercalcaemia ...) checked
# against the table: denied while the table shows them, or claimed while it does not.
_FINDINGS = [
    ("anaemia", r"an(?:a)?emi(?:a|c)", r"^(?:ha?emoglobin|hb)\b", "LOW"),
    ("thrombocytopenia", r"thrombocytopeni(?:a|c)", r"^platelets?\b", "LOW"),
    ("thrombocytosis", r"thrombocytosis", r"^platelets?\b", "HIGH"),
    ("leukopenia", r"leu[ck]openi(?:a|c)", r"^wbc\b", "LOW"),
    ("leukocytosis", r"leu[ck]ocytosis", r"^wbc\b", "HIGH"),
    ("neutropenia", r"neutropeni(?:a|c)", r"^neutrophils?\s+\(absolute\)", "LOW"),
    ("neutrophilia", r"neutrophilia", r"^neutrophils?\s+\(absolute\)", "HIGH"),
    ("lymphopenia", r"lympho(?:cyto)?peni(?:a|c)", r"^lymphocytes?\s+\(absolute\)", "LOW"),
    ("lymphocytosis", r"lymphocytosis", r"^lymphocytes?\s+\(absolute\)", "HIGH"),
    ("hypoalbuminaemia", r"hypoalbumin(?:a)?emi(?:a|c)", r"^albumin\b", "LOW"),
    ("hyperglycaemia", r"hyperglyc(?:a)?emi(?:a|c)", r"^glucose\b", "HIGH"),
    ("hypoglycaemia", r"hypoglyc(?:a)?emi(?:a|c)", r"^glucose\b", "LOW"),
    ("hypercalcaemia", r"hypercalc(?:a)?emi(?:a|c)", r"^calcium\b", "HIGH"),
    ("hypocalcaemia", r"hypocalc(?:a)?emi(?:a|c)", r"^calcium\b", "LOW"),
    ("hyperkalaemia", r"hyperkal(?:a)?emi(?:a|c)", r"^(?:k\s+)?potassium\b", "HIGH"),
    ("hypokalaemia", r"hypokal(?:a)?emi(?:a|c)", r"^(?:k\s+)?potassium\b", "LOW"),
    ("hypernatraemia", r"hypernatr(?:a)?emi(?:a|c)", r"^(?:na\s+)?sodium\b", "HIGH"),
    ("hyponatraemia", r"hyponatr(?:a)?emi(?:a|c)", r"^(?:na\s+)?sodium\b", "LOW"),
    ("hyperuricaemia", r"hyperuric(?:a)?emi(?:a|c)", r"^uric\s+acid\b", "HIGH"),
    ("hypercholesterolaemia", r"hypercholesterol(?:a)?emi(?:a|c)",
     r"^(?:cholesterol,?\s*total|ldl\s+cholesterol)\b", "HIGH"),
    ("hypertriglyceridaemia", r"hypertriglycerid(?:a)?emi(?:a|c)", r"^triglycerides?\b", "HIGH"),
    ("hyperbilirubinaemia", r"hyperbilirubin(?:a)?emi(?:a|c)", r"^bili(?:rubin)?\.?\s*total\b", "HIGH"),
    ("azotaemia", r"azot(?:a)?emi(?:a|c)", r"^urea\b", "HIGH"),
]
_FINDINGS = [(lab, re.compile(r"(?i)\b" + w + r"\b"), re.compile(n), st) for lab, w, n, st in _FINDINGS]
_FIND_CUT = re.compile(r"(?i)(?<!\d)[.;:](?!\d)|\b(?:but|however|although|though|whereas|yet|except|while)\b")
_FIND_NEG = re.compile(r"(?i)\b(?:no|not|without|absence\s+of|neither|nor|free\s+of)\b")
_FIND_NEG_BLOCK = re.compile(
    r"(?i)^(?:no|not|without)\s+(?:\w+\s+){0,2}?(?:mention|data|information|history|records?|details"
    r"|documentation|symptoms?|signs?|features?|complaints?)\b|^not\s+(?:exclud\w*|rul\w*|only|just)\b")
_FIND_AFTER_NEG = re.compile(
    r"(?i)^\s*(?:is|are|was|were|has\s+been|have\s+been)?\s*(?:absent|excluded|ruled\s+out"
    r"|not\s+(?:present|seen|detected|found|evident|noted|shown|indicated|suggested|supported))\b")
_FIND_HEDGE = re.compile(
    r"(?i)\b(?:rul(?:e|es|ed|ing)\s+out|exclud\w*|screen\w*\s+for|assess\w*\s+for|evaluat\w*\s+for"
    r"|check\w*\s+for|test\w*\s+for|monitor\w*\s+for|look\w*\s+for|risk\s+of|prevent\w*"
    r"|progress\w*\s+to|lead\w*\s+to|caus\w*|differentiat\w*|distinguish\w*|whether)\b")
_FIND_SOFT = re.compile(r"(?i)\b(?:unlikely|less\s+likely|not\s+supported|ruled\s+out"
                        r"|typically|usually|classically|characteri[sz]ed\s+by"
                        r"|would\s+(?:be\s+)?(?:considered|suspected|expected)"
                        r"|if\s+(?:\w+\s+){0,3}(?:were|was)\s+(?:low|high|abnormal|present|reduced|raised))\b")
_FIND_AFTER_HEDGE = re.compile(r"(?i)^\s*(?:develops?|occurs?|arises?|is\s+suspected)\b")


def _finding_mode(s: str, m) -> str:
    """Session 52 (cont. 3): 'denied', 'claim' or 'other' (hedged, 'no symptoms of', ...)."""
    head = re.sub(r"^\s*(?:[-*\u2022]|\d+[.)])\s*", "", s)
    off = len(s) - len(head)
    d = re.search(r"\s[\u2013\u2014-]\s", head)
    if d and m.end() <= off + d.start() and len(re.findall(r"[A-Za-z]+", head[:d.start()])) <= 8:
        return "other"   
    before = _FIND_CUT.split(s[:m.start()])[-1]
    after = _FIND_CUT.split(s[m.end():])[0]
    negs = list(_FIND_NEG.finditer(before))
    if negs:
        n = negs[-1]
        if _FIND_NEG_BLOCK.match(before[n.start():]):
            return "other"
        if len(re.findall(r"[A-Za-z]+", before[n.end():])) <= 8:
            return "denied"
    if _FIND_AFTER_NEG.match(after):
        return "denied"
    if _FIND_HEDGE.search(before) or _FIND_SOFT.search(before + " " + after) or _FIND_AFTER_HEDGE.match(after):
        return "other"
    return "claim"


def _finding_rows(rows, name_re):
    return [r for r in rows if " - Urine" not in r.get("test", "")
            and name_re.search(_english_test_name(r.get("test", "")).lower())]


def _finding_row_text(r) -> str:
    head = " ".join(x for x in (r.get("test", ""), r.get("value", ""), r.get("unit") or "") if x)
    return f"{head} (range {r.get('ref') or '-'})"


def _finding_quote(s: str) -> str:
    s = s.strip()
    return s if len(s) <= 200 else s[:200] + "..."


def _finding_scan(answer, mode):
    for s in _sentences(answer or ""):
        t = s.replace("*", "")
        for lab, word, name_re, want in _FINDINGS:
            for m in word.finditer(t):
                if _finding_mode(t, m) == mode:
                    yield lab, name_re, want, t
                    break


def denied_blood_findings(rows, answer) -> list:
    """Session 52 (cont. 3): the answer denies a finding ('no significant lymphopenia') that
    the table shows (Lymphocytes (absolute) LOW). One warning per finding word."""
    out, seen = [], set()
    for lab, name_re, want, t in _finding_scan(answer, "denied"):
        if lab in seen:
            continue
        bad = [r for r in _finding_rows(rows, name_re) if r.get("status") == want]
        if bad:
            seen.add(lab)
            out.append("The answer may deny an abnormal blood result: "
                       + "; ".join(_finding_row_text(r) for r in bad) + f': "{_finding_quote(t)}"')
    return out


def unsupported_findings(rows, answer) -> list:
    """Session 52 (cont. 3): the answer claims a finding ('if hypercalcemia persists', 'mild
    anaemia') while every matching row in the table is read and none is in that direction."""
    out, seen = [], set()
    for lab, name_re, want, t in _finding_scan(answer, "claim"):
        if lab in seen:
            continue
        found = [r for r in _finding_rows(rows, name_re) if r.get("status") in ("HIGH", "LOW", "normal")]
        if found and not any(r.get("status") == want for r in found):
            seen.add(lab)
            table = "; ".join(" ".join(x for x in (r.get("test", ""), r.get("value", ""),
                                                   r.get("unit") or "", r.get("status", "")) if x)
                              for r in found)
            out.append(f"The answer names a finding the lab table does not show: {lab} "
                       f"(table: {table}): \"{_finding_quote(t)}\"")
    return out
