"""SaMD mode (launcher menu 9): clinical decision support. Session 49 stub.

PR D: choose files in input/samd/, take the doctor's extra text, and save
step 1 in reports/samd/<run_id>/ (clinician_input.txt, inputs.json,
run.log). No AI call yet; reading images, reasoning and the browser
report come in the next PRs. Stdlib only.
"""
from __future__ import annotations

import json
from datetime import datetime
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


def reports_dir(base_dir) -> Path:
    return Path(base_dir) / "reports" / "samd"


def list_inputs(folder: Path) -> list[str]:
    """File names in folder that SaMD can read, sorted (case-insensitive)."""
    return sorted(
        (p.name for p in folder.iterdir()
         if p.is_file() and p.suffix.lower() in INPUT_EXT),
        key=str.lower,
    )


def file_kind(name: str) -> str:
    """'image' for photos, else the extension (txt, md, docx, pdf)."""
    ext = Path(name).suffix.lower()
    return "image" if ext in IMAGE_EXT else ext.lstrip(".")


def new_run_id(now=None) -> str:
    """Run folder name, same shape as SR runs: YYYYMMDD_HHMMSS."""
    return (now or datetime.now()).strftime("%Y%m%d_%H%M%S")


def choose_files(files, input_fn=input, log=print):
    """Enter = all files; '1,3' = those, in list order. None = not run."""
    answer = input_fn("Files to use: numbers separated by commas "
                      "(Enter = all): ").strip()
    if not answer:
        return list(files)
    picked = set()
    for part in answer.replace(" ", "").split(","):
        if not part.isdigit() or not 1 <= int(part) <= len(files):
            log(f"Not a valid file number: {part or '(empty)'}. Job not run.")
            return None
        picked.add(int(part) - 1)
    return [f for i, f in enumerate(files) if i in picked]


def read_clinician_text(input_fn=input, log=print) -> str:
    """Lines typed by the doctor; an empty line (or end of input) ends."""
    log("Extra clinical information (history, findings, your question).")
    log("Type or paste lines; an empty line ends. Enter at once = none.")
    lines = []
    while True:
        try:
            line = input_fn("> " if not lines else "  ")
        except EOFError:
            break
        if not line.strip():
            break
        lines.append(line.rstrip())
    return "\n".join(lines)


def save_step1(run_dir: Path, *, run_id, folder, files, text, provider,
               model, log_lines) -> None:
    """Write clinician_input.txt, inputs.json and run.log (LF, UTF-8)."""
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "clinician_input.txt").write_text(
        text + "\n" if text else "", encoding="utf-8", newline="\n")
    info = {
        "run_id": run_id,
        "provider": provider,
        "model": model or "",
        "files": [{"name": n, "kind": file_kind(n),
                   "bytes": (folder / n).stat().st_size} for n in files],
        "clinician_text_chars": len(text),
    }
    (run_dir / "inputs.json").write_text(
        json.dumps(info, indent=2) + "\n", encoding="utf-8", newline="\n")
    (run_dir / "run.log").write_text(
        "\n".join(log_lines) + "\n", encoding="utf-8", newline="\n")


def run(base_dir, model=None, *, provider="ollama", confirm=None,
        input_fn=input, log=print, now=None):
    """Choose inputs, take the doctor's text, save step 1. None = not run."""
    lines = []

    def say(msg=""):
        lines.append(msg)
        log(msg)

    folder = input_dir(base_dir)
    folder.mkdir(parents=True, exist_ok=True)
    say()
    say("SaMD - clinical decision support")
    say(INTENDED_USE)
    files = list_inputs(folder)
    if files:
        say(f"Files in input/samd/ ({len(files)}):")
        for i, name in enumerate(files, 1):
            say(f"  {i}. {name}")
        files = choose_files(files, input_fn, say)
        if files is None:
            return None
    else:
        say("No files in input/samd/. Put clinical photos, photos of lab "
            "reports, notes (.txt/.docx) or PDFs there, or type the case below.")
    text = read_clinician_text(input_fn, say)
    if not files and not text:
        say("Nothing to analyse (no files, no text). Job not run.")
        return None
    run_id = new_run_id(now)
    run_dir = reports_dir(base_dir) / run_id
    say(f"Using {len(files)} file(s) and {len(text)} characters of typed text.")
    say(f"Step files: reports/samd/{run_id}/")
    say("SaMD analysis is not built yet (Session 49 stub): no AI call made.")
    save_step1(run_dir, run_id=run_id, folder=folder, files=files, text=text,
               provider=provider, model=model, log_lines=lines)
    return {"run_id": run_id, "run_dir": run_dir, "files": files,
            "ai_called": False}
