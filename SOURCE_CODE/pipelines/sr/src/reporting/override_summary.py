"""Session 39 (item 4c): which studies count as reviewer-entered data.

StudyOverrides.apply writes override_fields as "; "-joined entries:
"field(absent->v)", "field(old->v)" (a value changed), "field(confirmed v)"
(reviewer agreed with the AI), or bare names (first_author, year,
exclude_from_meta). Only a changed value is "values entered by a reviewer".
Used by both the HTML and the Word report so their counts cannot differ.
"""


def override_changed_values(override_fields) -> bool:
    """True if the reviewer changed at least one value."""
    return "->" in str(override_fields or "")


def override_confirmed_only(override_fields) -> bool:
    """True if the reviewer only confirmed values, changing none."""
    s = str(override_fields or "")
    return "(confirmed " in s and "->" not in s


def study_label(r) -> str:
    m = r.get("study_metadata") or {}
    return f"{m.get('first_author') or r.get('filename', '?')} ({m.get('year', '')})"
