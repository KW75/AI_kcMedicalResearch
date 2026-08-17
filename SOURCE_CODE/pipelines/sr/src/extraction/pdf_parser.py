from pathlib import Path
import fitz

def extract_text(pdf_path: Path, max_chars: int = 30_000) -> str:
    try:
        doc  = fitz.open(str(pdf_path))
        text = "\n\n".join(page.get_text() for page in doc)
        doc.close()
        return text[:max_chars]
    except Exception as e:
        return f"[PDF extraction error: {e}]"
