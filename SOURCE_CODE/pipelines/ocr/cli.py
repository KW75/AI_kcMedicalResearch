"""OCR terminal prompts for --mode ocr (launcher menu 8).

input/ocr/ decides what runs:
  one file      -> function 1: record + <header>_SUMMARY
  several files -> function 2: every file -> one record each + <header>_SYNOPSIS
Then two questions: scan title/name (header of the output files) and the
vision model. Checks that need no typing (input files present, a vision
model pulled, --model can read images) run first, so a job that cannot run
never asks a question. Ollama only for now; main.py stops cloud providers.
"""
from __future__ import annotations

import os
from pathlib import Path

from . import engine, reader

DEFAULT_VISION_MODEL = "gemma4:e4b"


def vision_models(list_fn, caps_fn, host=None) -> list[dict]:
    """Pulled Ollama models that report the 'vision' capability."""
    return [m for m in list_fn(host) if "vision" in caps_fn(host, m["name"])]


def _default_model(names: list[str]) -> str:
    """OLLAMA_MODEL if it can read images, else gemma4:e4b, else the first."""
    env = os.getenv("OLLAMA_MODEL", "").strip()
    if env in names:
        return env
    if DEFAULT_VISION_MODEL in names:
        return DEFAULT_VISION_MODEL
    return names[0]


def _pick(options: list, answer: str):
    """1-based menu answer -> option, or None if not a valid number."""
    answer = (answer or "").strip()
    if answer.isdigit() and 1 <= int(answer) <= len(options):
        return options[int(answer) - 1]
    return None


def _report(result: dict, rep_dir: Path, log) -> None:
    if result["records"]:
        log(f"Done: {len(result['records'])} record(s) in {rep_dir / result['header']}")
    else:
        log("No records written.")
    for name, err in result["failed"]:
        log(f"  Could not read {name}: {err}")
    if result["summary"]:
        log(f"Summary file: {result['summary'][0]}")


def run(base_dir, model=None, *, input_fn=input, list_fn=None, caps_fn=None,
        run_single=None, run_set=None, log=print):
    """Ask the questions, run the engine, return its result (None = not run)."""
    if list_fn is None or caps_fn is None:
        import ollama_models  # lazy: tests pass fakes
        list_fn = list_fn or ollama_models.list_ollama_models
        caps_fn = caps_fn or ollama_models.model_capabilities
    run_single = run_single or engine.run_single
    run_set = run_set or engine.run_set
    in_dir = Path(base_dir) / "input" / "ocr"
    out_dir = Path(base_dir) / "output" / "ocr"
    rep_dir = Path(base_dir) / "reports" / "ocr"


    files = reader.list_inputs(in_dir)
    if not files:
        log(f"No supported files in {in_dir}. Accepted: "
            f"{', '.join(sorted(reader.SUPPORTED_EXTS))}. Job not run.")
        return None

    models = None
    if model:
        if "vision" not in caps_fn(None, model):
            log(f"Model {model} cannot read images (no 'vision' capability) "
                f"or is not pulled. Use a vision model, e.g. "
                f"{DEFAULT_VISION_MODEL}. Job not run.")
            return None
    else:
        models = vision_models(list_fn, caps_fn)
        if not models:
            log(f"No pulled Ollama model can read images. Run: ollama pull "
                f"{DEFAULT_VISION_MODEL}  (other vision models: "
                f"https://ollama.com/search?c=vision). Job not run.")
            return None

    if len(files) == 1:
        log(f"1 file: {files[0].name} -> record + SUMMARY")
    else:
        log(f"{len(files)} files in {in_dir} -> one record each + SYNOPSIS:")
        for f in files:
            log(f"  {f.name}")

    name = input_fn("Scan title/name (header of the output files; "
                    "Enter = OCR_<date>_<time>): ").strip()

    if models is not None:
        names = [m["name"] for m in models]
        default = _default_model(names)
        for i, m in enumerate(models, start=1):
            mark = "  (default)" if m["name"] == default else ""
            log(f"  {i}. {m['name']}  {m['size_gb']} GB{mark}")
        answer = input_fn("Model number (Enter = default): ").strip()
        if not answer:
            model = default
        else:
            picked = _pick(models, answer)
            if picked is None:
                log("Not a valid model number. Job not run.")
                return None
            model = picked["name"]

    log(f"Model: {model}. Output: {out_dir}")
    if len(files) == 1:
        result = run_single(files[0], out_dir, name, model, log=log,
                            records_root=rep_dir)
    else:
        result = run_set(in_dir, out_dir, name, model, log=log,
                         records_root=rep_dir)
    _report(result, rep_dir, log)
    return result
