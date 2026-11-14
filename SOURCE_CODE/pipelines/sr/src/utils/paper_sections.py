"""Pick the parts of a paper's shared text that RoB2 needs (Session 38).

RoB2 judges randomisation, deviations, missing data, measurement and
reporting. Those facts sit in Methods and Results, which usually start
after the first 6000 characters. This module sends:
  start of the paper (title + abstract, up to START_CHARS)
  + the Methods section
  + the Results section
  + lines naming a trial registry that are not already in that text
within one limit. No Methods heading -> the old behaviour (first
fallback_chars), never a failure.

A heading is a line on its own: "Methods", "METHODS", "2. Methods",
"Methods." (Tesseract stray dot), "Materials and methods",
"Patients and methods", "Methods and material". A structured-abstract
label such as "Methods: 60 women..." is not a heading. If Methods appears
more than once (abstract with own-line headings), the longest Methods
span wins.

Registration lines (Session 38 rerun 20261111_081840): Ang's NCT00965601
and Karlsson's NCT01004458 sit in the abstract after START_CHARS or in end
matter, so RoB2 said "no trial registration". A line counts only if it has
a registry ID (NCT + 8 digits, zero or letter O as Tesseract reads it;
ISRCTN) or the registry name clinicaltrials.gov. The word "registered"
alone does not count ("registered polysomnographic technologist").
Stdlib only.
"""
import re

START_CHARS = 1500
TRUNC = "\n...[truncated]"
SKIP = "\n...[skipped to Methods]\n"
REG_SEP = "\n...[registration]\n"
REG_MAX_CHARS = 500

_NUM = r"(?:\d+(?:\.\d+)*\.?\s+)?"      # "2 ", "2. ", "2.1 "
_TAIL = r"\s*\.?\s*$"                   # optional stray dot
_WHO = r"(?:materials?|patients?|subjects?|participants?)"
METHODS_RE = re.compile(
    r"^\s*" + _NUM
    + r"(?:" + _WHO + r"\s+and\s+)?methods?"
    + r"(?:\s+and\s+" + _WHO + r")?"     # Session 38: "Methods and material" (Jensen)
    + _TAIL, re.I)
RESULTS_RE = re.compile(r"^\s*" + _NUM + r"results?" + _TAIL, re.I)
END_RE = re.compile(
    r"^\s*" + _NUM
    + r"(?:discussion|conclusions?|references|bibliography|acknowledge?ments?)"
    + _TAIL, re.I)
REG_RE = re.compile(r"NCT\s?[0O]\d{7}|ISRCTN\s?\d+|clinicaltrials\.gov", re.I)


def _headings(text, pattern):
    """Start offsets of lines that are exactly a heading."""
    out, pos = [], 0
    for line in text.split("\n"):
        if pattern.match(line):
            out.append(pos)
        pos += len(line) + 1
    return out


def _first_after(offsets, pos):
    return next((o for o in offsets if o > pos), None)


def _cut(s, n):
    return s if len(s) <= n else s[:n] + TRUNC


def _add_registration(text, out):
    """Append registry lines of text that out does not already contain."""
    picked, total = [], 0
    for line in text.split("\n"):
        s = line.strip()
        if not s or not REG_RE.search(s) or s in out or s in picked:
            continue
        if total + len(s) + 1 > REG_MAX_CHARS:
            break
        picked.append(s)
        total += len(s) + 1
    if not picked:
        return out, 0
    return out + REG_SEP + "\n".join(picked), len(picked)


def rob2_text(text, limit=50000, fallback_chars=6000):
    """Return (text to send, note for the log)."""
    text = text or ""
    methods = _headings(text, METHODS_RE)
    if not methods:
        note = f"no Methods heading found, using first {fallback_chars} chars"
        out = text if len(text) <= fallback_chars else text[:fallback_chars] + TRUNC
        out, n_reg = _add_registration(text, out)
        if n_reg:
            note += f"; registration lines added: {n_reg}"
        return out, note

    results = _headings(text, RESULTS_RE)
    ends = _headings(text, END_RE)

    def methods_end(m):
        r = _first_after(results, m)
        if r is not None:
            return r
        e = _first_after(ends, m)
        return e if e is not None else len(text)

    m = max(methods, key=lambda o: methods_end(o) - o)
    meth = text[m:methods_end(m)].rstrip()
    r = _first_after(results, m)
    if r is not None:
        e = _first_after(ends, r)
        res = text[r:e if e is not None else len(text)].rstrip()
    else:
        res = ""

    start = text[:min(START_CHARS, m)].rstrip()
    sep = "\n" if m <= START_CHARS else SKIP
    budget = max(limit - len(start), 0)
    half = budget // 2
    if not res:
        meth_n, res_n = budget, 0
    elif len(meth) <= half:
        meth_n = len(meth)
        res_n = budget - meth_n
    elif len(res) <= half:
        res_n = len(res)
        meth_n = budget - res_n
    else:
        meth_n, res_n = half, budget - half

    out = (start + sep if start else "") + _cut(meth, meth_n)
    if res:
        out += "\n" + _cut(res, res_n)
    out, n_reg = _add_registration(text, out)

    if res:
        note = f"Methods {len(meth)} + Results {len(res)} chars"
    else:
        note = (f"Methods {len(meth)} chars, no Results heading "
                f"(Methods runs to the next end heading)")
    if n_reg:
        note += f"; registration lines added: {n_reg}"
    note += f"; sent {len(out)} of {len(text)} chars"
    return out, note
