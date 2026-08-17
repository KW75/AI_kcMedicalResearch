import re
from pathlib import Path
import fitz

def extract_metadata(pdf_path: Path) -> dict:
    try:
        doc  = fitz.open(str(pdf_path))
        text = "".join(doc[p].get_text() for p in range(min(2, len(doc))))
        doc.close()
    except Exception:
        text = ""
    doi_m = re.search(r"10\.\d{4,9}/[^\s\"'<>]+", text)
    doi   = doi_m.group(0).rstrip(".,;") if doi_m else None
    yr_m  = re.search(r"\b(19[9]\d|20[0-2]\d)\b", text)
    year  = int(yr_m.group(0)) if yr_m else None
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return {"filename": pdf_path.name,
            "title_guess": lines[0][:200] if lines else pdf_path.stem,
            "year_guess": year, "doi_guess": doi,
            "raw_text_preview": text[:500]}
