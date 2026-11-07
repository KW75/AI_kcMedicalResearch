"""OCR engine: reader -> vision model -> record -> SUMMARY / SYNOPSIS.

Function 1 (run_single): one file -> one record + <header>_SUMMARY.
Function 2 (run_set): every supported file in a folder -> one record each,
then <header>_SYNOPSIS built from the per-file summaries.
Both use _process_file, so a record looks the same either way.

Records go to <records_root>/<header>/ (reports/ocr/<header>/ from the CLI);
without records_root they go to <out_dir>/records/. A header already used
(records folder or SUMMARY/SYNOPSIS exists) gets _2, _3, ... so a repeat
scan never overwrites an earlier one.

`call(prompt, images=None) -> str` is the AI. The default is the local
Ollama model; tests pass a fake, so Ollama never needs to run.
"""
from __future__ import annotations

from pathlib import Path

from . import output, reader

TRANSCRIBE_PROMPT = (
    "Transcribe all text in this image exactly as written. Keep the original "
    "line breaks, numbering, units and punctuation. Do not summarise, correct, "
    "translate or add anything. If a word cannot be read, write [illegible]. "
    "If the image has no text, reply [no text]."
)
SUMMARY_PROMPT = (
    "Summarise the document below. Use only information in the text; do not "
    "add facts. Keep key numbers, dates, names and units exactly as written. "
    "Use short headings and bullet points."
)
SYNOPSIS_PROMPT = (
    "Write one synopsis of the document set below, using the per-file "
    "summaries. Use only information in the summaries; do not add facts. "
    "Say which file each point comes from, e.g. (from <file name>)."
)


def ollama_call(model: str):
    """Default AI: the chosen local Ollama model (images sent base64)."""
    def _call(prompt, images=None):
        import providers  # lazy: keeps this module importable without it
        return providers.call_ollama_provider(prompt, model=model, images=images)
    return _call


def _header_taken(header: str, out_dir, records_root) -> bool:
    if records_root is not None and (Path(records_root) / header).exists():
        return True
    out = Path(out_dir)
    return any(out.glob(f"{header}_SUMMARY.*")) or any(out.glob(f"{header}_SYNOPSIS.*"))


def unique_header(name: str, out_dir, records_root=None, now=None) -> str:
    """Header from the typed name (blank -> OCR_<date>_<time>); _2, _3 if used."""
    base = output.make_header(name, now)
    header, n = base, 2
    while _header_taken(header, out_dir, records_root):
        header, n = f"{base}_{n}", n + 1
    return header


def _rec_dir(records_root, header: str):
    return Path(records_root) / header if records_root is not None else None


def _process_file(path: Path, out_dir, header: str, model: str, call, log,
                  rec_dir=None) -> str:
    """Read one file, transcribe image pages, summarise, write the record."""
    done = []
    for page in reader.read_input(path):
        if page["text"] is not None:
            done.append({"page": page["page"], "text": page["text"], "method": "text"})
        else:
            log(f"    page {page['page']}: AI reading...")
            text = call(TRANSCRIBE_PROMPT, images=[page["png"]]).strip()
            done.append({"page": page["page"], "text": text, "method": "vision"})
    full = "\n\n".join(f"[Page {p['page']}]\n{p['text']}" for p in done)
    log("    summarising...")
    summary = call(f"{SUMMARY_PROMPT}\n\nFile: {path.name}\n\n{full}").strip()
    output.write_record(out_dir, header, path.name, summary, done, model,
                        rec_dir=rec_dir)
    return summary


def run_single(path, out_dir, name: str, model: str, call=None, now=None,
               log=print, records_root=None) -> dict:
    """Function 1: one file -> record + <header>_SUMMARY."""
    path = Path(path)
    call = call or ollama_call(model)
    header = unique_header(name, out_dir, records_root, now)
    rec_dir = _rec_dir(records_root, header)
    result = {"header": header, "records": [], "failed": [], "summary": None}
    log(f"[1/1] {path.name}")
    try:
        summary = _process_file(path, out_dir, header, model, call, log, rec_dir)
    except Exception as exc:
        result["failed"].append((path.name, str(exc)))
        log(f"    FAILED: {exc}")
        return result
    result["records"].append(path.name)
    result["summary"] = output.write_summary(
        out_dir, header, "SUMMARY", f"Source: {path.name}\n\n{summary}", model)
    return result


def run_set(folder, out_dir, name: str, model: str, call=None, now=None,
            log=print, records_root=None) -> dict:
    """Function 2: every supported file -> one record each + <header>_SYNOPSIS.

    A file that fails is listed in result["failed"]; the rest still finish.
    No synopsis is written if every file fails.
    """
    files = reader.list_inputs(folder)
    if not files:
        raise ValueError(f"No supported files in {folder} "
                         f"(accepted: {', '.join(sorted(reader.SUPPORTED_EXTS))})")
    call = call or ollama_call(model)
    header = unique_header(name, out_dir, records_root, now)
    rec_dir = _rec_dir(records_root, header)
    result = {"header": header, "records": [], "failed": [], "summary": None}
    summaries = []
    for i, path in enumerate(files, start=1):
        log(f"[{i}/{len(files)}] {path.name}")
        try:
            summaries.append((path.name, _process_file(path, out_dir, header,
                                                       model, call, log, rec_dir)))
            result["records"].append(path.name)
        except Exception as exc:
            result["failed"].append((path.name, str(exc)))
            log(f"    FAILED: {exc}")
    if not summaries:
        return result
    log("Writing synopsis...")
    body = "\n\n".join(f"### {n}\n{s}" for n, s in summaries)
    synopsis = call(f"{SYNOPSIS_PROMPT}\n\n{body}").strip()
    if result["failed"]:
        synopsis += ("\n\nNot included (could not be read): "
                     + ", ".join(n for n, _ in result["failed"]))
    result["summary"] = output.write_summary(out_dir, header, "SYNOPSIS",
                                             synopsis, model)
    return result
