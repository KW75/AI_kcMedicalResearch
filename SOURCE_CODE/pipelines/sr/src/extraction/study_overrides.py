"""
Generic study metadata resolution and manual overrides for SR extraction.

Two mechanisms, in priority order:

1. resolve_pdf_metadata()  - derive first_author / year / doi from the PDF
   itself when the model did not return them. Works for any paper.

2. StudyOverrides           - a reviewer-maintained YAML file of verified
   values, keyed by filename. Applied last so a human decision always wins.

Every override that fires is recorded on the result under
"override_fields" and "override_note" so it shows up in extracted_data.csv
and can be reported in the review's methods section.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

# Fields a reviewer may override. Anything else in the YAML is ignored
# (with a warning) so typos cannot silently inject junk into results.
METADATA_FIELDS = ("first_author", "year", "doi", "study", "study_id")

NUMERIC_FIELDS = (
    "n_intervention",
    "n_control",
    "mean_intervention",
    "sd_intervention",
    "mean_control",
    "sd_control",
)

ALLOWED_FIELDS = METADATA_FIELDS + NUMERIC_FIELDS + ("note",)

_MISSING_STRINGS = {"", "none", "null", "nan", "na", "n/a", "not reported", "not stated"}


def is_missing(value) -> bool:
    """True when a value should be treated as absent."""
    if value is None:
        return True
    if isinstance(value, float) and value != value:  # NaN
        return True
    if isinstance(value, (list, tuple, dict)) and not value:
        return True
    return str(value).strip().lower() in _MISSING_STRINGS


# --------------------------------------------------------------------------
# 1. Generic metadata resolution from the PDF
# --------------------------------------------------------------------------

_DOI_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Za-z0-9]+\b")
_YEAR_RE = re.compile(r"\b(19[5-9]\d|20[0-4]\d)\b")

_INITIALS_RE = re.compile(r"^(?:[A-Z]\.?){1,3}$")

# Words that appear where an author line is expected but are not names.
_NOT_A_NAME = {
    "department", "university", "faculty", "school", "institute", "hospital",
    "college", "centre", "center", "psychology", "medicine", "abstract",
    "keywords", "introduction", "correspondence", "springer", "elsevier",
    "wiley", "taylor", "francis", "sage", "bmc", "plos", "unknown", "author",
    "microsoft", "word", "adobe", "acrobat", "pdflatex", "latex",
    "conclusion", "conclusions", "results", "methods", "method",
    "background", "objective", "objectives", "discussion", "purpose",
    "aim", "aims", "summary", "trial", "study", "design", "setting",
    "participants", "intervention", "outcome", "outcomes", "table",
    "figure", "received", "revised", "published", "article",
}


def _is_initials(token: str) -> bool:
    return bool(_INITIALS_RE.match(token.strip()))


def _first_author_from_string(raw):
    """
    Best-effort surname from an author string.

    Handles "Lami, Marta J.", "Sanchez AI, Lami MJ", "Marta J. Lami",
    "M. P. Martinez and A. E. Sanchez". Returns None when the input does
    not look like a person's name. This is a heuristic: callers should
    treat the result as a suggestion to be checked, not as ground truth.
    """
    if not raw:
        return None

    text = str(raw).strip()
    # First author only.
    first = re.split(r"\s*(?:;|\band\b|&|\n)\s*", text)[0].strip()
    if not first:
        return None

    parts = [p.strip() for p in first.split(",") if p.strip()]
    segment = parts[0] if parts else first

    tokens = [t.strip(".,") for t in segment.split() if t.strip(".,")]
    named = [t for t in tokens if not _is_initials(t)]
    if not named:
        return None

    # "Surname, Given" and "Surname II" both put the surname first.
    # "Given M. Surname" puts it last.
    idx = 0 if len(parts) > 1 else len(named) - 1
    candidate = named[idx]

    # Keep surname particles together: "van der Berg" not "van".
    _PARTICLES = {"van", "von", "de", "del", "della", "di", "da", "du",
                  "der", "den", "le", "la", "dos", "das", "ter"}
    if candidate.lower() in _PARTICLES:
        joined = [candidate]
        for nxt in named[idx + 1:]:
            joined.append(nxt)
            if nxt.lower() not in _PARTICLES:
                break
        candidate = " ".join(joined)

    if candidate.lower() in _NOT_A_NAME:
        return None
    if not re.fullmatch(r"[A-Za-z\u00C0-\u024F'` -]{2,40}", candidate):
        return None
    if any(t.lower() in _NOT_A_NAME for t in tokens):
        return None
    return candidate


def _year_from_text(text: str, doi: str = ""):
    """Best-effort publication year from front-matter text."""
    if not text:
        return None

    # Prefer an explicit copyright / published line.
    for pattern in (
        r"(?:\u00a9|\(c\)|copyright)\s*(19[5-9]\d|20[0-4]\d)",
        r"published\s+(?:online\s+)?[^\n]{0,40}?(19[5-9]\d|20[0-4]\d)",
        r"accepted[^\n]{0,40}?(19[5-9]\d|20[0-4]\d)",
    ):
        m = re.search(pattern, text, re.I)
        if m:
            return int(m.group(1))

    years = [int(y) for y in _YEAR_RE.findall(text[:4000])]
    if years:
        # Most frequent, tie-broken by most recent.
        return max(set(years), key=lambda y: (years.count(y), y))
    return None


def resolve_pdf_metadata(pdf_path) -> dict:
    """
    Derive first_author / year / doi / title from a PDF.

    Returns {} on any failure - this is a best-effort enrichment, never a
    hard dependency. Requires PyMuPDF; import is local so the module stays
    usable in environments without it.
    """
    out = {}
    try:
        import fitz
    except ImportError:
        logger.debug("PyMuPDF unavailable; skipping PDF metadata resolution")
        return out

    try:
        doc = fitz.open(str(pdf_path))
    except Exception as exc:
        logger.debug("Could not open %s for metadata: %s", pdf_path, exc)
        return out

    try:
        meta = doc.metadata or {}

        try:
            front = doc[0].get_text("text") or ""
        except Exception:
            front = ""

        doi = ""
        m = _DOI_RE.search(front) or _DOI_RE.search(str(meta.get("subject") or ""))
        if m:
            doi = m.group(0).rstrip(".,;)")
            out["doi"] = doi

        author = _first_author_from_string(meta.get("author") or "")
        if not author:
            # Try the line following the title on page 1.
            for line in front.splitlines()[:40]:
                line = line.strip()
                if len(line) < 8 or len(line) > 200:
                    continue
                if re.search(r"\b(?:university|department|abstract|keywords)\b", line, re.I):
                    break
                if re.search(r"[A-Z][a-z]+", line) and ("," in line or " and " in line) and not re.search(r"\d", line):
                    author = _first_author_from_string(line)
                    if author:
                        break
        if author:
            out["first_author"] = author
            out["_metadata_source"] = "pdf_auto"

        year = _year_from_text(front, doi)
        if not year:
            year = _year_from_text(str(meta.get("creationDate") or ""))
        if year:
            out["year"] = int(year)

    except Exception as exc:
        logger.debug("Metadata resolution failed for %s: %s", pdf_path, exc)
    finally:
        try:
            doc.close()
        except Exception:
            pass

    return out


# --------------------------------------------------------------------------
# 2. Reviewer-maintained overrides
# --------------------------------------------------------------------------

class StudyOverrides:
    """Loads and applies per-study manual corrections keyed by filename."""

    def __init__(self, path=None):
        self.path = Path(path) if path else None
        self.entries = {}
        self._load()

    def _load(self):
        if not self.path or not self.path.exists():
            logger.info("No study overrides file at %s", self.path)
            return

        try:
            import yaml
            with open(self.path, "r", encoding="utf-8") as fh:
                raw = yaml.safe_load(fh) or {}
        except Exception as exc:
            logger.warning("Could not read overrides %s: %s", self.path, exc)
            return

        if not isinstance(raw, dict):
            logger.warning("Overrides file %s is not a mapping; ignoring", self.path)
            return

        for key, value in raw.items():
            if not isinstance(value, dict):
                logger.warning("Override for %r is not a mapping; skipped", key)
                continue

            unknown = set(value) - set(ALLOWED_FIELDS)
            if unknown:
                logger.warning("Override for %r has unknown fields %s; ignored",
                               key, sorted(unknown))

            cleaned = {k: v for k, v in value.items() if k in ALLOWED_FIELDS}
            if cleaned:
                self.entries[str(key).strip().lower()] = cleaned

        logger.info("Loaded %d study override(s) from %s",
                    len(self.entries), self.path)

    def lookup(self, filename: str):
        """Match on exact filename, then on stem, then on substring."""
        if not filename:
            return None

        name = str(filename).replace("\\", "/").split("/")[-1].strip().lower()
        if name in self.entries:
            return self.entries[name]

        stem = name[:-4] if name.endswith(".pdf") else name
        for key, entry in self.entries.items():
            key_stem = key[:-4] if key.endswith(".pdf") else key
            if key_stem == stem or key_stem in stem:
                return entry
        return None

    def apply(self, result: dict, filename: str = "") -> dict:
        """
        Apply a matching override to result, in place.

        Metadata fields fill only when missing. Numeric outcome fields
        replace whatever the extractor produced, because the reason to
        record them is that the extractor gets them wrong. Every change
        is recorded for the audit trail.
        """
        if not isinstance(result, dict):
            return result

        entry = self.lookup(filename or result.get("filename") or "")
        if not entry:
            return result

        applied = []

        for field in METADATA_FIELDS:
            if field in entry and is_missing(result.get(field)):
                result[field] = entry[field]
                applied.append(field)

        po = result.get("primary_outcome")
        if not isinstance(po, dict):
            po = {}
            result["primary_outcome"] = po

        participants = result.get("participants")
        if not isinstance(participants, dict):
            participants = {}
            result["participants"] = participants

        for field in NUMERIC_FIELDS:
            if field not in entry:
                continue

            value = entry[field]

            # The restructure step moves flat keys into primary_outcome /
            # participants before overrides run, so check the nested
            # containers too or every "before" reads as None.
            before = result.get(field)
            if is_missing(before):
                before = po.get(field)
            if is_missing(before) and field.startswith("n_"):
                before = participants.get(field)
            if is_missing(before):
                alt = (field.replace("n_", "") + "_n") if field.startswith("n_") else None
                if alt:
                    before = po.get(alt)

            result[field] = value
            if field.startswith("n_"):
                participants[field] = value
                po[field] = value
                po[field.replace("n_", "") + "_n"] = value
            else:
                po[field] = value

            if is_missing(before):
                applied.append(f"{field}(absent->{value})")
            elif str(before) != str(value):
                applied.append(f"{field}({before}->{value})")
            else:
                applied.append(f"{field}(confirmed {value})")

        if applied:
            result["override_fields"] = "; ".join(applied)
            if entry.get("note"):
                result["override_note"] = entry["note"]
            numeric_changed = [a for a in applied if "(" in a]
            level = logger.warning if numeric_changed else logger.info
            level("MANUAL OVERRIDE applied to %s -> %s",
                  filename, result["override_fields"])

        return result
