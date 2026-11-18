"""OCR terminal prompts for --mode ocr (launcher menu 8).

input/ocr/ decides what runs:
  one file      -> function 1: record + <header>_SUMMARY
  several files -> menu 8 asks (kind="ask", Session 48):
    1 Papers   -> function 1 per file: own record + <file name>_SUMMARY
    2 Synopsis -> function 2: one record each + <header>_SYNOPSIS of all
Then two questions: scan title/name (header of the output files) and the
vision model. Checks that need no typing run first, so a job that cannot run
never asks a question.

Which AI reads the page images:
- --provider ollama (default): a pulled local model with 'vision'.
- --provider qwen / openai: cloud. run_cli in main.py has already shown the
  [CLOUD] banner and got consent, so Ollama is not asked.
- ollama with no local vision model: offers qwen/openai (only those with an
  API key set). Runs only if confirm(provider) says yes ([CLOUD] banner +
  typed "y"). Enter cancels.
The AI note in every output file names the model, plus "(provider, cloud)"
when the pages left this machine.
"""
from __future__ import annotations

import os
from pathlib import Path

from . import engine, reader

# Session 48: OCR prefers the shared vision model (ollama_models.VISION_MODEL;
# test_ocr_s48_vision_default.py checks the two names match). gemma4:e4b
# left most [?] unfilled and misread table values; qwen3-vl read them right.
DEFAULT_VISION_MODEL = "qwen3-vl:30b-a3b-instruct"
CLOUD_KEYS = {"qwen": "DASHSCOPE_API_KEY", "openai": "OPENAI_API_KEY"}


def vision_models(list_fn, caps_fn, host=None) -> list[dict]:
    """Pulled Ollama models that report 'vision' (shared with SR, Session 42)."""
    import ollama_models  # lazy
    return ollama_models.vision_models(list_fn, caps_fn, host)


def _default_model(names: list[str]) -> str:
    """Default vision model: DEFAULT_VISION_MODEL if pulled, else the shared
    rule in ollama_models (Session 48)."""
    import ollama_models  # lazy
    return ollama_models.default_vision_model(names, preferred=DEFAULT_VISION_MODEL)


def _pick_local_model(models: list[dict], input_fn=input, log=print):
    """Session 48: ask which pulled vision model reads the pages. Enter =
    DEFAULT_VISION_MODEL if pulled; not pulled -> warning, then the old rule
    (OLLAMA_MODEL, gemma4:e4b, first). None = job not run."""
    import ollama_models  # lazy
    pulled = {ollama_models._with_tag(m["name"]) for m in models}
    if ollama_models._with_tag(DEFAULT_VISION_MODEL) not in pulled:
        log(f"WARNING: {DEFAULT_VISION_MODEL} is not pulled; OCR uses a "
            f"smaller vision model, which misses or misreads more symbols "
            f"and table values. Run: ollama pull {DEFAULT_VISION_MODEL}")
    return ollama_models.pick_vision_model(models, input_fn=input_fn, log=log,
                                           preferred=DEFAULT_VISION_MODEL)


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
        log(f"  Not written: {name}: {err}")  # Session 48: read may be fine
    if result["summary"]:
        log(f"Summary file: {result['summary'][0]}")


def _cloud_choices() -> list[str]:
    """Cloud providers that can read images and have an API key set."""
    return [p for p, key in CLOUD_KEYS.items() if os.getenv(key, "").strip()]


def _cloud_model(provider: str, model):
    """The cloud model that will read the pages (named in the AI note)."""
    if model:
        return model
    import providers  # lazy
    if provider == "qwen":
        return providers.QWEN_VISION_MODEL
    return providers.get_default_model(provider) or None


def _offer_cloud(choices, confirm, input_fn, log):
    """No local vision model: offer a cloud provider. None = not run."""
    log("A cloud AI can read the pages instead, but page images and the "
        "text of your documents will leave this machine (the cloud AI also "
        "writes the summary).")
    for i, p in enumerate(choices, start=1):
        log(f"  {i}. {p}")
    answer = input_fn("Cloud provider number (Enter = cancel): ").strip()
    if not answer:
        log("Cancelled. Job not run.")
        return None
    provider = _pick(choices, answer)
    if provider is None:
        log("Not a valid number. Job not run.")
        return None
    if not confirm(provider):
        log("Cloud not confirmed. Job not run.")
        return None
    return provider


KIND_MENU = (
    "1. Papers   - each file is its own paper: own record + own SUMMARY",
    "2. Synopsis - one record each + one SYNOPSIS summarising all papers "
    "in input/ocr",
)


def _ask_kind(input_fn, log):
    """Session 48: several files -> Papers or Synopsis. Enter / no keyboard
    = Synopsis; Ctrl+C or a bad answer = None (job not run)."""
    log("Write them as")
    for line in KIND_MENU:
        log(line)
    try:
        answer = input_fn("Papers or Synopsis (number, Enter = 2): ").strip()
    except EOFError:
        log("No keyboard: Synopsis.")
        return "synopsis"
    except KeyboardInterrupt:
        log("Cancelled. Job not run.")
        return None
    if answer in ("", "2"):
        return "synopsis"
    if answer == "1":
        return "papers"
    log("Not a valid number. Job not run.")
    return None


def _run_papers(files, out_dir, label, log, rep_dir, run_single, extra):
    """Session 48 Papers: each file is its own paper - run_single per file,
    header = the file's name (_2, _3 if used). No SYNOPSIS."""
    combined = {"header": None, "records": [], "failed": [], "summary": None,
                "papers": []}
    for i, f in enumerate(files, start=1):
        log(f"Paper {i}/{len(files)}: {f.name}")
        res = run_single(f, out_dir, f.stem, label, log=log,
                         records_root=rep_dir, **extra)
        _report(res, rep_dir, log)
        combined["papers"].append(res)
        combined["records"] += res["records"]
        combined["failed"] += res["failed"]
    return combined


def run(base_dir, model=None, *, provider="ollama", confirm=None,
        input_fn=input, list_fn=None, caps_fn=None,
        run_single=None, run_set=None, log=print, kind="synopsis"):
    """Ask the questions, run the engine, return its result (None = not run)."""
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

    cloud = provider in CLOUD_KEYS
    models = None
    if not cloud:
        if list_fn is None or caps_fn is None:
            import ollama_models  # lazy: tests pass fakes
            list_fn = list_fn or ollama_models.list_ollama_models
            caps_fn = caps_fn or ollama_models.model_capabilities
        if model:
            if "vision" not in caps_fn(None, model):
                log(f"Model {model} cannot read images (no 'vision' capability) "
                    f"or is not pulled. Use a vision model, e.g. "
                    f"{DEFAULT_VISION_MODEL}. Job not run.")
                return None
        else:
            models = vision_models(list_fn, caps_fn)
            if not models:
                pull = (f"No pulled Ollama model can read images. Run: ollama "
                        f"pull {DEFAULT_VISION_MODEL}, or pull one in launcher "
                        f"10 Setup -> 2 Local AI (vision models: "
                        f"https://ollama.com/search?c=vision).")
                choices = _cloud_choices() if confirm else []
                if not choices:
                    log(pull + " Job not run.")
                    return None
                log(pull)
                provider = _offer_cloud(choices, confirm, input_fn, log)
                if provider is None:
                    return None
                cloud = True
                models = None

    if len(files) == 1:
        log(f"1 file: {files[0].name} -> record + SUMMARY")
    else:
        if kind == "ask":  # Session 48: menu 8 asks Papers / Synopsis next
            log(f"{len(files)} files in {in_dir}")
        else:
            log(f"{len(files)} files in {in_dir} -> one record each + SYNOPSIS:")
        for f in files:
            log(f"  {f.name}")

    papers = False
    if len(files) > 1 and kind != "synopsis":
        if kind == "ask":
            kind = _ask_kind(input_fn, log)
            if kind is None:
                return None
        papers = kind == "papers"

    name = ""
    if not papers:
        name = input_fn("Scan title/name (header of the output files; "
                        "Enter = OCR_<date>_<time>): ").strip()

    if models:
        model = _pick_local_model(models, input_fn=input_fn, log=log)
        if model is None:
            return None

    extra = {}
    label = model
    if cloud:
        real = _cloud_model(provider, model)
        label = f"{real or 'default model'} ({provider}, cloud)"
        extra["call"] = engine.cloud_call(provider, real)

    log(f"Model: {label}. Output: {out_dir}")
    if papers:
        return _run_papers(files, out_dir, label, log, rep_dir, run_single,
                           extra)
    if len(files) == 1:
        result = run_single(files[0], out_dir, name, label, log=log,
                            records_root=rep_dir, **extra)
    else:
        result = run_set(in_dir, out_dir, name, label, log=log,
                         records_root=rep_dir, **extra)
    _report(result, rep_dir, log)
    return result
