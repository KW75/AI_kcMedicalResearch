"""SaMD mode (launcher menu 9): clinical decision support. Session 49 stub.

Lists input/samd/ and prints the intended-use statement. No AI call yet;
reading images, reasoning and the browser report come in the next PRs.
Stdlib only.
"""
from __future__ import annotations

from pathlib import Path

INTENDED_USE = (
    "Intended use: decision support for a clinician, for research and "
    "evaluation; not a cleared or certified medical device. The clinician "
    "makes every decision."
)

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".gif", ".webp"}
TEXT_EXT = {".txt", ".md", ".docx", ".pdf"}
INPUT_EXT = IMAGE_EXT | TEXT_EXT


def input_dir(base_dir) -> Path:
    return Path(base_dir) / "input" / "samd"


def list_inputs(folder: Path) -> list[str]:
    """File names in folder that SaMD can read, sorted (case-insensitive)."""
    return sorted(
        (p.name for p in folder.iterdir()
         if p.is_file() and p.suffix.lower() in INPUT_EXT),
        key=str.lower,
    )


def run(base_dir, model=None, *, provider="ollama", confirm=None,
        log=print) -> dict:
    """Stub: show the intended use and the input files; no AI call."""
    folder = input_dir(base_dir)
    folder.mkdir(parents=True, exist_ok=True)
    log("")
    log("SaMD - clinical decision support")
    log(INTENDED_USE)
    files = list_inputs(folder)
    if files:
        log(f"Files in input/samd/ ({len(files)}):")
        for i, name in enumerate(files, 1):
            log(f"  {i}. {name}")
    else:
        log("No files in input/samd/. Put clinical photos, photos of lab "
            "reports, notes (.txt/.docx) or PDFs there.")
    log("SaMD analysis is not built yet (Session 49 stub): no AI call made.")
    return {"files": files, "ai_called": False}
