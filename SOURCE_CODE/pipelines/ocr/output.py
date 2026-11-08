"""OCR output files: records and summary/synopsis (.docx + .md).

Record = summary at the top, full OCR text below, one heading per page that
says how the page was read. OCR text is written VERBATIM: each line becomes a
plain paragraph, with no markdown -> Word list/heading conversion, so a line
like "3) BP 140/90" is never renumbered or turned into a bullet.
Every file ends with a note naming the model and saying it is AI-produced.
"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

import docx

SUMMARY_KINDS = {"SUMMARY", "SYNOPSIS"}
METHOD_LABELS = {"text": "text layer", "vision": "AI read"}
_UNSAFE = re.compile(r"[^\w-]")
_UNSAFE_STEM = re.compile(r'[<>:"/\\|?*\s]')
# Characters an XML/Word file cannot hold (tab, newline, CR are kept).
# Broken PDF font encodings (e.g. Ang 2010) can put these in the text layer.
_XML_BAD = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\ud800-\udfff\ufffe\uffff]")


def _clean(text):
    """Remove characters Word cannot store; None stays None."""
    return _XML_BAD.sub("", text) if text else text


def make_header(name: str, now: datetime | None = None) -> str:
    """'<name>_<YYYY-MM-DD>' from the typed name; blank -> 'OCR_<date>_<HHMM>'."""
    now = now or datetime.now()
    safe = _UNSAFE.sub("", re.sub(r"\s+", "_", (name or "").strip()))
    if not safe.strip("_"):
        return f"OCR_{now:%Y-%m-%d_%H%M}"
    return f"{safe}_{now:%Y-%m-%d}"


def ai_note(model: str) -> str:
    return (f"Produced by AI (model: {model}). OCR and summaries can contain "
            f"errors; check against the original document.")


def _record_stem(header: str, source_name: str) -> str:
    src = Path(source_name)
    stem = _UNSAFE_STEM.sub("_", src.stem)
    ext = src.suffix.lower().lstrip(".")
    return f"{header}_{stem}_{ext}" if ext else f"{header}_{stem}"


METHOD_LABELS.update({
    "hybrid": "text layer + AI symbols",
    "hybrid_unresolved": "text layer, [?] not resolved",
    "hybrid_partial": "text layer + AI symbols, some [?] left",
})


def _page_heading(page: dict) -> str:
    label = METHOD_LABELS.get(page.get("method"), "read")
    return f"Page {page['page']} ({label})"


def write_record(out_dir, header: str, source_name: str, summary: str,
                 pages: list[dict], model: str, rec_dir=None) -> tuple[Path, Path]:
    """Write <rec_dir or out_dir/records>/<header>_<stem>_<ext>.docx and .md."""
    rec_dir = Path(rec_dir) if rec_dir else Path(out_dir) / "records"
    rec_dir.mkdir(parents=True, exist_ok=True)
    summary = _clean(summary) or ""
    pages = [{**p, "text": _clean(p.get("text"))} for p in pages]

    stem = _record_stem(header, source_name)
    docx_path, md_path = rec_dir / f"{stem}.docx", rec_dir / f"{stem}.md"

    # Markdown
    md = [f"# {source_name}", "", "## Summary", "", summary.strip(), "",
          "## Full text", ""]
    for page in pages:
        md += [f"### {_page_heading(page)}", "",
               page.get("text") or "(no text read)", ""]
    md += ["---", "", f"*{ai_note(model)}*", ""]
    md_path.write_text("\n".join(md), encoding="utf-8")

    # Word
    document = docx.Document()
    document.add_heading(source_name, level=0)
    document.add_heading("Summary", level=2)
    for line in summary.strip().splitlines():
        document.add_paragraph(line)
    document.add_heading("Full text", level=2)
    for page in pages:
        document.add_heading(_page_heading(page), level=3)
        for line in (page.get("text") or "(no text read)").splitlines():
            document.add_paragraph(line)
    _add_note(document, model)
    document.save(str(docx_path))
    return docx_path, md_path


def write_summary(out_dir, header: str, kind: str, text: str,
                  model: str) -> tuple[Path, Path]:
    """Write <header>_SUMMARY or <header>_SYNOPSIS (.docx + .md)."""
    if kind not in SUMMARY_KINDS:
        raise ValueError(f"Unknown summary kind: {kind!r}")
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    text = _clean(text) or ""
    docx_path = out_dir / f"{header}_{kind}.docx"
    md_path = out_dir / f"{header}_{kind}.md"
    title = f"{header} {kind.title()}"

    md_path.write_text(
        "\n".join([f"# {title}", "", text.strip(), "", "---", "",
                   f"*{ai_note(model)}*", ""]),
        encoding="utf-8")

    document = docx.Document()
    document.add_heading(title, level=0)
    for line in text.strip().splitlines():
        document.add_paragraph(line)
    _add_note(document, model)
    document.save(str(docx_path))
    return docx_path, md_path


def _add_note(document, model: str) -> None:
    run = document.add_paragraph().add_run(ai_note(model))
    run.italic = True
