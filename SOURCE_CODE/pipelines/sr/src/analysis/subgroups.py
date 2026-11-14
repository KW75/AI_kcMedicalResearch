"""Item 11 (Session 39): subgroups by control type and an estimate
excluding waiting-list trials (Word/HTML report).

Control type, option C: the reviewer's comparator_type
(study_overrides.yaml) wins; otherwise the extracted control_group label.
An unrecognised reviewer value or an unmatched label -> unclassified:
listed by name, never pooled, never guessed into a subgroup.
Not the [SENSITIVITY] line in main.py (needs-review studies) - a
different check."""
import re

WAITING_LIST = "waiting_list"
USUAL_CARE = "usual_care"
ATTENTION_PLACEBO = "attention_placebo"
UNCLASSIFIED = "unclassified"
REVIEWER_TYPES = (WAITING_LIST, USUAL_CARE, ATTENTION_PLACEBO)
LABELS = {
    WAITING_LIST: "Waiting list",
    USUAL_CARE: "Usual care",
    ATTENTION_PLACEBO: "Attention placebo",
    UNCLASSIFIED: "Unclassified",
}
MIN_SUBGROUP_K = 3

# Order matters: waiting list first.
_LABEL_PATTERNS = (
    (WAITING_LIST, re.compile(r"(?i)wait(?:ing)?[\s_-]*list|\bWLC?\b")),
    (ATTENTION_PLACEBO, re.compile(r"(?i)attention|placebo|sham")),
    (USUAL_CARE, re.compile(
        r"(?i)usual|\bUC\b|\bUMC\b|\bTAU\b|standard care|routine care")),
)


def classify_comparator(result):
    """Return (control type, source). source = 'reviewer', 'label', or a
    'reviewer value ... not recognised' message."""
    result = result or {}
    rv = str(result.get("comparator_type") or "").strip().lower()
    if rv:
        if rv in REVIEWER_TYPES:
            return rv, "reviewer"
        return UNCLASSIFIED, (f"reviewer value {rv!r} not recognised "
                              f"(use {', '.join(REVIEWER_TYPES)})")
    label = str(result.get("control_group") or "")
    for ctype, pat in _LABEL_PATTERNS:
        if pat.search(label):
            return ctype, "label"
    return UNCLASSIFIED, "label"


def _ctype(row):
    ct = row.get("comparator_type") or UNCLASSIFIED
    return ct if ct in LABELS else UNCLASSIFIED


def subgroup_summary(rows, pool, min_k=MIN_SUBGROUP_K):
    """rows: pooled rows, each with 'study' and 'comparator_type'.
    pool(list_of_rows) -> dict with pooled_effect, ci_lower, ci_upper, I2.
    Returns entries: kind ('subgroup'/'sensitivity'), key, label,
    studies, k, result (None = not pooled), note."""
    def _entry(kind, key, label, members, may_pool=True, extra=""):
        k = len(members)
        e = {"kind": kind, "key": key, "label": label,
             "studies": [m.get("study", "?") for m in members],
             "k": k, "result": None, "note": ""}
        if not may_pool:
            e["note"] = ("Not pooled - control type unknown; set "
                         "comparator_type in study_overrides.yaml.")
        elif k == 0:
            e["note"] = "No studies."
        elif k == 1:
            e["note"] = "1 study - not pooled."
        else:
            try:
                e["result"] = pool(members)
            except Exception as exc:
                e["note"] = f"Pooling failed ({type(exc).__name__}: {exc})."
            else:
                if k < min_k:
                    e["note"] = (f"Only {k} studies (< {min_k}) - "
                                 f"interpret with caution.")
        if extra:
            e["note"] = (e["note"] + " " + extra).strip()
        return e

    by = {}
    for r in rows:
        by.setdefault(_ctype(r), []).append(r)
    out = []
    for key in (WAITING_LIST, USUAL_CARE, ATTENTION_PLACEBO, UNCLASSIFIED):
        if by.get(key):
            out.append(_entry("subgroup", key, LABELS[key], by[key],
                              may_pool=(key != UNCLASSIFIED)))
    non_wl = [r for r in rows if _ctype(r) not in (WAITING_LIST, UNCLASSIFIED)]
    unc = [r.get("study", "?") for r in by.get(UNCLASSIFIED, [])]
    extra = f"Left out (control type unknown): {', '.join(unc)}." if unc else ""
    out.append(_entry("sensitivity", "excluding_waiting_list",
                      "Excluding waiting-list trials", non_wl, extra=extra))
    return out



def subgroup_log_lines(summary, effect_measure, rows=None):
    """Run-log lines for main.py, all prefixed [SUBGROUP]. rows (optional)
    lists each study's control type and where it came from."""
    lines = ["[SUBGROUP] Control-type subgroups (item 11; not the "
             "[SENSITIVITY] check):"]
    for r in rows or []:
        ct = r.get("comparator_type") or UNCLASSIFIED
        src = r.get("comparator_source") or "?"
        lines.append(f"[SUBGROUP]   {r.get('study', '?')}: "
                     f"{LABELS.get(ct, ct)} (from {src})")
    for e in summary:
        line = (f"[SUBGROUP] {e['label']} (k={e['k']}: "
                f"{', '.join(e['studies']) or '-'})")
        res = e["result"]
        if res:
            line += (f": {effect_measure} {res['pooled_effect']:.3f} "
                     f"[{res['ci_lower']:.3f},{res['ci_upper']:.3f}] "
                     f"I2={res['I2']:.1f}%")
        if e["note"]:
            line += f" - {e['note']}"
        lines.append(line)
    return lines



SUBGROUP_INTRO = (
    "Subgroups by control type, and an estimate excluding waiting-list "
    "trials. Control type is the reviewer's entry (comparator_type in "
    "input/sr/study_overrides.yaml) or, if none, the extracted control-group "
    "label. Exploratory: groups with fewer than 3 studies are unreliable. "
    "This is not the needs-review comparison in the run log.")

def subgroup_report_lines(summary, effect_measure):
    """Word/HTML report rows (shared): (group, studies, estimate, note).
    estimate is '' when the group was not pooled."""
    out = []
    for e in summary or []:
        res = e.get("result")
        est = (f"{effect_measure} {res['pooled_effect']:.3f} (95% CI "
               f"{res['ci_lower']:.3f} to {res['ci_upper']:.3f}); "
               f"I\u00b2={res['I2']:.1f}%") if res else ""
        out.append((f"{e['label']} (k={e['k']})",
                    ", ".join(e["studies"]) or "-", est, e.get("note", "")))
    return out
