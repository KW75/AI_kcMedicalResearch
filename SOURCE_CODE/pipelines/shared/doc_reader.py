"""Shared .docx reader for writing / appraisal input (Session 48).

Before: every .docx reader used doc.paragraphs only, so Word tables were
never read. read_docx walks paragraphs and tables in document order:
each table row becomes 'cell | cell | cell' (a merged cell once per row),
empty paragraphs and empty rows are skipped.
"""
from __future__ import annotations


def _table_rows(table) -> list[str]:
    rows = []
    for row in table.rows:
        cells, seen = [], set()
        for cell in row.cells:
            key = id(cell._tc)  # merged cells share one _tc
            if key in seen:
                continue
            seen.add(key)
            cells.append(" ".join(cell.text.split()))
        if any(cells):
            rows.append(" | ".join(cells))
    return rows


def read_docx(path) -> str:
    """Text of a .docx: paragraphs and table rows in document order."""
    import docx
    from docx.table import Table

    doc = docx.Document(str(path))
    lines: list[str] = []
    for block in doc.iter_inner_content():
        if isinstance(block, Table):
            lines.extend(_table_rows(block))
        elif block.text.strip():
            lines.append(block.text)
    return "\n".join(lines)
