"""SaMD mode (launcher menu 9): clinical decision support (Session 49).

Step 1 (PR D): choose files in input/samd/, take the doctor's extra text,
save clinician_input.txt, inputs.json and run.log in reports/samd/<run_id>/.
Step 2 (PR E): read every chosen file first (text layers need no AI), then
one AI call per image page: lab reports are transcribed, clinical photos
described without a diagnosis -> step2_<nn>_<file>.txt.
Step 3 (PR E): one reasoning call over the whole case -> case.md and
reasoning.md (intended use on top).
A failed or empty AI reply stops the job: no half answer is written.
Step 4 (PR F): report.py computes the lab table (status from the printed
reference range, not the AI), checks the answer and writes
output/samd/<run_id>/report.md, .html (opened in the browser) and .docx.
pipelines.ocr and ollama_models are imported lazily (pillow, pymupdf).
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
TEXT_EXT = {".txt", ".docx", ".pdf"}  # what the OCR reader can read
INPUT_EXT = IMAGE_EXT | TEXT_EXT

HEADINGS = (
    "## Working diagnosis",
    "## Differential diagnoses",
    "## Red flags",
    "## Suggested next tests",
    "## Other clinically important points",
    "## Missing information",
)

IMAGE_PROMPT = (
    "This image comes from a patient's clinical record. First line: write "
    "exactly TYPE: TEXT if the image is mainly printed or written text (lab "
    "report, results table, letter, prescription), otherwise TYPE: PHOTO. "
    "Then, for TEXT: transcribe all text exactly as written, keeping line "
    "breaks, numbers, units, reference ranges and flags (H, L, *); do not "
    "summarise, correct or add anything; write [illegible] for a word you "
    "cannot read. For PHOTO: describe only what is visible (body site, "
    "size, colour, shape, border, surface, distribution, any scale or "
    "ruler) in plain words; do not name a diagnosis. Write symbols as "
    "plain characters, not LaTeX."
)

REASONING_PROMPT = (
    "You are assisting a doctor with clinical decision support. The doctor "
    "makes every decision. Use only the case below; do not invent history, "
    "findings or results. When you cite a lab value, copy the number and "
    "unit exactly as in the source and name the source. Before you call a "
    "result high, low, abnormal or borderline, compare it with its reference "
    "range in the source: a value inside its range is normal and must be "
    "called normal. If the results do not support the premise of the "
    "doctor's question (for example, no anaemia), say so first. If the age "
    "or sex in the doctor's notes differs from the documents, state both "
    "and do not choose one. Address every finding the doctor typed. Do not "
    "say a finding is absent unless the case says so. If the premise is not "
    "supported, the working diagnosis must explain the doctor's main "
    "complaint from the abnormal findings, not the premise. Do not say why "
    "a test was ordered unless the source says so. Answer in English "
    "with exactly these headings, in this order:\n"
    + "\n".join(HEADINGS) + "\n"
    "Under Working diagnosis give the most likely diagnosis and why. Under "
    "Differential diagnoses list the main alternatives, most likely first; "
    "for each give the findings for and against it. Under Red flags list "
    "dangerous diagnoses that must not be missed and the findings that "
    "would point to them. Under Suggested next tests list the tests that "
    "would best separate the diagnoses. Under Missing information list what "
    "is not in the case but would change the assessment.\n\n"
    "CASE\n"
)


class _Stop(Exception):
    """A step failed; the job stops and no answer is written."""


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
    """'image' for photos, else the extension (txt, docx, pdf)."""
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
    log("Type or paste lines; an empty line ends (put notes with blank lines "
        "in a .txt file in input/samd/). Enter at once = none.")
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
    _write_log(run_dir, log_lines)


def _write_log(run_dir: Path, lines) -> None:
    (run_dir / "run.log").write_text(
        "\n".join(lines) + "\n", encoding="utf-8", newline="\n")


# --- AI model ----------------------------------------------------------------

def _ollama():
    import ollama_models  # lazy: top-level module, stdlib only
    return ollama_models


def _local_vision_models() -> list:
    from ..ocr import cli as ocr_cli
    om = _ollama()
    try:
        return ocr_cli.vision_models(om.list_ollama_models, om.model_capabilities)
    except Exception:
        return []


def choose_call(provider, model, *, confirm=None, input_fn=input, log=print,
                models_fn=None, caps_fn=None, pick_fn=None):
    """The AI call for this case, or None (job stops after step 1).

    --provider qwen/openai: run_cli has already shown the cloud banner and
    asked, so confirm is not used. Ollama: a vision model is needed; if
    none is pulled, a cloud provider is offered and confirm asks once.
    """
    from ..ocr import cli as ocr_cli
    from ..ocr import engine
    if provider in ocr_cli.CLOUD_KEYS:
        name = ocr_cli._cloud_model(provider, model)
        log(f"AI: {provider} {name or '(default model)'} (cloud; confirmed "
            f"before the job started).")
        return engine.cloud_call(provider, name)
    if provider != "ollama":
        log(f"SaMD: {provider} cannot read clinical photos and lab images. "
            f"Use ollama (local), qwen or openai.")
        return None
    if model:
        caps_fn = caps_fn or _ollama().model_capabilities
        try:
            caps = caps_fn(None, model)
        except Exception:
            caps = []
        if "vision" not in caps:
            log(f"Model {model} cannot read images (no 'vision' capability) or "
                f"is not pulled. Use a vision model, e.g. "
                f"{ocr_cli.DEFAULT_VISION_MODEL}.")
            return None
        log(f"AI: Ollama {model} (local).")
        return engine.ollama_call(model)
    models = (models_fn or _local_vision_models)()
    if models:
        pick = pick_fn or _ollama().pick_vision_model
        name = pick(models, input_fn=input_fn, log=log,
                    preferred=ocr_cli.DEFAULT_VISION_MODEL)
        if not name:
            log("No model chosen.")
            return None
        log(f"AI: Ollama {name} (local).")
        return engine.ollama_call(name)
    log(f"No pulled Ollama model can read images. Run: ollama pull "
        f"{ocr_cli.DEFAULT_VISION_MODEL}, or pull one in launcher "
        f"10 Setup -> 2 Local AI.")
    choices = ocr_cli._cloud_choices() if confirm else []
    if not choices:
        return None
    log("A cloud AI can do the analysis instead, but clinical photos, lab "
        "images and the case text will leave this machine. Remove names, "
        "faces, record numbers and other identifiers first.")
    for i, p in enumerate(choices, start=1):
        log(f"  {i}. {p}")
    answer = input_fn("Cloud provider number (Enter = cancel): ").strip()
    if not answer:
        log("Cancelled.")
        return None
    chosen = ocr_cli._pick(choices, answer)
    if chosen is None:
        log("Not a valid number.")
        return None
    if not confirm(chosen):
        log("Cloud not confirmed.")
        return None
    return engine.cloud_call(chosen, ocr_cli._cloud_model(chosen, None))


# --- steps 2-3 ---------------------------------------------------------------

def read_pages(path):
    """Pages of one file via the OCR reader (lazy: pillow, pymupdf)."""
    from ..ocr import reader
    return reader.read_input(path)


def _case_limit() -> int:
    """Characters of case text that fit the model's context (OCR budget)."""
    from ..ocr import engine
    return engine._budget_chars()


def read_sources(folder: Path, files, say):
    """[(name, pages)] for every chosen file; None if one cannot be read."""
    out = []
    for name in files:
        try:
            out.append((name, list(read_pages(folder / name))))
        except Exception as e:
            say(f"Could not read {name}: {e}. Job stopped; no AI call made.")
            return None
    return out


def parse_image_reply(reply):
    """(kind, body): 'transcription', 'photo description' or
    'image (type not stated)' when the TYPE line is missing."""
    text = (reply or "").strip()
    first, _, rest = text.partition("\n")
    tag = first.strip().upper().replace(" ", "")
    if tag == "TYPE:TEXT":
        return "transcription", rest.strip()
    if tag == "TYPE:PHOTO":
        return "photo description", rest.strip()
    return "image (type not stated)", text


def describe_sources(sources, call, run_dir: Path, say):
    """Step 2: text layers as they are, one AI call per image page.
    Returns [(name, kind, text)]; raises _Stop on a failed or empty reply."""
    done = []
    for n, (name, pages) in enumerate(sources, 1):
        parts, kinds = [], []
        for i, page in enumerate(pages, 1):
            where = f"{name} page {i}" if len(pages) > 1 else name
            if (page.get("text") or "").strip():
                kind, body = "text layer", page["text"].strip()
            elif page.get("png"):
                say(f"Step 2: AI reads {where} ...")
                try:
                    reply = call(IMAGE_PROMPT, images=[page["png"]])
                except Exception as e:
                    raise _Stop(f"AI call failed on {where}: {e}")
                kind, body = parse_image_reply(reply)
                if not body:
                    raise _Stop(f"AI gave an empty reply for {where}")
            else:
                continue
            kinds.append(kind)
            parts.append(f"--- page {i} ({kind}) ---\n{body}"
                         if len(pages) > 1 else body)
        kind = ", ".join(dict.fromkeys(kinds)) or "empty"
        body = "\n\n".join(parts)
        (run_dir / f"step2_{n:02d}_{name}.txt").write_text(
            f"{name} ({kind})\n\n{body}\n", encoding="utf-8", newline="\n")
        done.append((name, kind, body))
    return done


def build_case(text, described) -> str:
    parts = ["Doctor's notes:", text or "(none typed)"]
    for n, (name, kind, body) in enumerate(described, 1):
        parts += ["", f"Source {n}: {name} ({kind})", body or "(nothing read)"]
    return "\n".join(parts)


def missing_headings(answer: str) -> list[str]:
    lines = {line.strip().lower() for line in answer.splitlines()}
    return [h for h in HEADINGS if h.lower() not in lines]


def open_browser(path, log=print) -> None:
    """Show the report in the default browser (a local file, no server)."""
    try:
        import webbrowser
        webbrowser.open(Path(path).resolve().as_uri())
    except Exception as e:
        log(f"Could not open the browser ({e}); open the report file yourself.")


def write_report_step(base_dir, run_id, run_dir, text, described, case,
                      answer, miss, lines, say, result) -> None:
    """Step 4: lab table computed by code, checks, report in
    output/samd/<run_id>/ (.md, .html, .docx); HTML opened in the browser."""
    from . import report
    rows = report.parse_results(described)
    warnings = report.check_answer(rows, answer, case)
    warnings = list(warnings) + report.unmentioned_abnormal(rows, answer)  # Session 51 (cont. 12)
    warnings = list(warnings) + report.ckd_stage_mismatch(rows, answer)  # Session 51 (cont. 13)
    warnings = list(warnings) + report.denied_urine_findings(rows, answer)  # Session 51 (cont. 17)
    for w in warnings:
        say("WARNING: " + w)
    if miss:
        warnings.insert(0, "Headings missing from the answer: "
                        + ", ".join(h[3:] for h in miss))
    (run_dir / "results.json").write_text(
        json.dumps(rows, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8", newline="\n")
    ai_line = next((m for m in reversed(lines) if m.startswith("AI: ")), "")
    md = report.build_markdown(
        run_id=run_id, intended_use=INTENDED_USE, doctor_text=text,
        rows=rows, warnings=warnings, answer=answer,
        sources=[(n, k) for n, k, _ in described], ai_line=ai_line)
    out_dir = Path(base_dir) / "output" / "samd" / run_id
    paths = report.write_report(out_dir, md, title=f"SaMD report {run_id}",
                                log=say)
    say(f"Report: output/samd/{run_id}/report.html (also .md"
        + (", .docx)" if paths["docx"] else ")"))
    result["report"] = paths["html"]
    result["warnings"] = warnings
    open_browser(paths["html"], say)


def run(base_dir, model=None, *, provider="ollama", confirm=None,
        input_fn=input, log=print, now=None):
    """Steps 1-3. None = not run (nothing written); else a result dict."""
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
    save_step1(run_dir, run_id=run_id, folder=folder, files=files, text=text,
               provider=provider, model=model, log_lines=lines)
    result = {"run_id": run_id, "run_dir": run_dir, "files": files,
              "ai_called": False, "answer": None, "report": None,
              "warnings": []}
    try:
        sources = read_sources(folder, files, say)
        if sources is None:
            return result
        call = choose_call(provider, model, confirm=confirm,
                           input_fn=input_fn, log=say)
        if call is None:
            say("No AI model: step 1 saved, no analysis. Job stopped.")
            return result
        result["ai_called"] = True
        try:
            described = describe_sources(sources, call, run_dir, say)
            case = build_case(text, described)
            (run_dir / "case.md").write_text(
                case + "\n", encoding="utf-8", newline="\n")
            limit = _case_limit()
            if len(case) > limit:
                raise _Stop(f"Case text too long for the model's context "
                            f"({len(case)} characters, limit {limit}); use "
                            f"fewer or shorter files")
            say("Step 3: AI reasoning on the case ...")
            try:
                answer = (call(REASONING_PROMPT + case) or "").strip()
            except Exception as e:
                raise _Stop(f"AI call failed at step 3: {e}")
            if not answer:
                raise _Stop("AI gave an empty reply at step 3")
        except _Stop as e:
            say(f"{e}. No answer written.")
            return result
        path = run_dir / "reasoning.md"
        path.write_text(INTENDED_USE + "\n\n" + answer + "\n",
                        encoding="utf-8", newline="\n")
        miss = missing_headings(answer)
        if miss:
            say("WARNING: headings missing from the answer: "
                + ", ".join(h[3:] for h in miss) + ". Check it carefully.")
        say(f"Answer: reports/samd/{run_id}/reasoning.md")
        result["answer"] = path
        try:
            write_report_step(base_dir, run_id, run_dir, text, described,
                              case, answer, miss, lines, say, result)
        except Exception as e:
            say(f"Report not written ({e}); the answer is in "
                f"reports/samd/{run_id}/reasoning.md.")
        return result
    finally:
        _write_log(run_dir, lines)
