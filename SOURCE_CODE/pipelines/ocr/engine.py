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
    "If the image has no text, reply [no text]. Write symbols as plain "
    "characters (±, ≥, −), not LaTeX."
)
SUMMARY_PROMPT = (
    "Summarise the document below. Use only information in the text; do not "
    "add facts. Keep key numbers, dates, names and units exactly as written. "
    "Use short headings and bullet points. Write symbols as plain "
    "characters (±, ≥, −), not LaTeX."
)
SYNOPSIS_PROMPT = (
    "Write one synopsis of the document set below, using the per-file "
    "summaries. Use only information in the summaries; do not add facts. "
    "Say which file each point comes from, e.g. (from <file name>)."
)


# --- Long text: summarise in parts so nothing is cut silently ----------------
# Ollama silently drops prompt text past num_ctx (OLLAMA_CONTEXT, default
# 32768). The window also holds the answer (num_predict 8192), so the text
# budget is (context - answer - prompt room) at a cautious 3 chars/token.
PART_PROMPT = (
    "This is one part of a longer text. Write concise notes on this part "
    "only. Keep every number, unit, name and date exactly as written. Do not "
    "add anything that is not in the text."
)
COMBINE_PROMPT = (
    "The notes below were made from consecutive parts of one longer text, "
    "in order. Use them as the source for this task."
)
CHARS_PER_TOKEN = 3
ANSWER_TOKENS = 8192
PROMPT_TOKENS = 1000
MAX_ROUNDS = 3
MIN_SHRINK = 0.8   # a round of notes must cut the text to <= 80%


class TooLongError(ValueError):
    """The text could not be brought within the context budget."""


def _budget_chars() -> int:
    """How many characters of document text fit in one prompt."""
    import os
    ctx = int(os.getenv("OLLAMA_CONTEXT", "32768"))
    return max(2000, (ctx - ANSWER_TOKENS - PROMPT_TOKENS) * CHARS_PER_TOKEN)


def _split(text: str, limit: int) -> list[str]:
    """Split at paragraph breaks (then spaces) into parts <= limit chars."""
    pieces = []
    for para in text.split("\n\n"):
        while len(para) > limit:
            cut = para.rfind(" ", 0, limit)
            if cut <= 0:
                cut = limit
            pieces.append(para[:cut])
            para = para[cut:].lstrip(" ")
        pieces.append(para)
    parts, cur = [], ""
    for piece in pieces:
        if cur and len(cur) + 2 + len(piece) > limit:
            parts.append(cur)
            cur = piece
        else:
            cur = f"{cur}\n\n{piece}" if cur else piece
    if cur:
        parts.append(cur)
    return parts


def _summarise(task_prompt: str, text: str, call, log, head: str = "") -> str:
    """One call if the text fits; otherwise notes per part, then combine."""
    budget = _budget_chars()
    rounds = 0
    while len(text) > budget:
        rounds += 1
        if rounds > MAX_ROUNDS:
            raise TooLongError(f"text still too long after {MAX_ROUNDS} "
                               "rounds of notes")
        parts = _split(text, budget)
        log(f"    long text: summarised in {len(parts)} parts")
        notes = []
        for p in parts:
            words = max(150, len(p) // 24)
            notes.append(call(f"{PART_PROMPT} Use at most {words} words."
                              f"\n\n{p}").strip())
        new = "\n\n".join(f"[Part {i}]\n{n}" for i, n in enumerate(notes, 1))
        if len(new) > len(text) * MIN_SHRINK:
            raise TooLongError("the notes were not shorter than the text "
                               f"({len(text):,} -> {len(new):,} characters)")
        text = new
    if rounds:
        return call(f"{task_prompt}\n\n{head}{COMBINE_PROMPT}\n\n{text}").strip()
    return call(f"{task_prompt}\n\n{head}{text}").strip()


def ollama_call(model: str):
    """Default AI: the chosen local Ollama model (images sent base64)."""
    def _call(prompt, images=None):
        import providers  # lazy: keeps this module importable without it
        return providers.call_ollama_provider(prompt, model=model, images=images)
    return _call


def cloud_call(provider: str, model):
    """Cloud AI (qwen/openai) for OCR, used only after the user agreed.
    Page images go as image_url parts (providers._user_content)."""
    def _call(prompt, images=None):
        import providers  # lazy
        fn = {"qwen": providers.call_qwen_provider,
              "openai": providers.call_openai_provider}[provider]
        return fn(prompt, model=model, images=images)
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


# --- Hybrid read: PDF page whose symbol font lost its signs ------------------
# The reader gives the text layer with each lost symbol as [?] (page["hint"])
# plus the page image. The model fills only the [?]; fill_symbols() checks
# that nothing else changed, so letters and digits always come from the text
# layer. If the check fails the page keeps its visible [?] and a WARNING.
FILL_PROMPT = (
    "The text below was copied from the text layer of this page image. Its "
    "font lost some symbols; each lost symbol is shown as [?]. Look at the "
    "image and return the whole text with each [?] replaced by the symbol "
    "printed there (for example ±, =, −, <, >, ≤, ≥, ×, °). Change nothing "
    "else: keep every word, number, line break and hyphen. Use plain "
    "characters, not LaTeX. Reply with the text only."
)
MARK = "[?]"
_FILL = r"([^\s\w$\\\[\]]{1,3}?)"


def _loose(part: str) -> str:
    """Regex for one stretch of text between [?] marks; spacing may differ."""
    import re
    out = []
    for piece in re.split(r"(-?\s+)", part):
        if not piece:
            continue
        if not piece.strip():
            out.append(r"\s*+")
        elif piece[0] == "-" and not piece[1:].strip():
            out.append(r"-?\s*+" if "\n" in piece else r"-\s*+")
        else:
            out.append(re.escape(piece))
    return "".join(out)


def symbol_fills(marked: str, answer: str):
    """Fill for each [?] in marked, or None if anything else changed.

    Compared after NFKC (so the ligature fi equals fi) and ignoring spacing and
    end-of-line hyphens. Each fill must be 1-3 symbol characters: no letters,
    digits, dollar sign, backslash or square brackets.
    """
    import re
    import unicodedata
    norm = unicodedata.normalize("NFKC", marked).split(MARK)
    if len(marked.split(MARK)) != len(norm):
        return None
    pattern = _FILL.join(_loose(p) for p in norm)
    found = re.search(pattern, unicodedata.normalize("NFKC", answer or ""))
    return None if not found else list(found.groups())


def _put(marked: str, fills) -> str:
    parts = marked.split(MARK)
    out = [parts[0]]
    for fill, part in zip(fills, parts[1:]):
        out += [fill, part]
    return "".join(out)


def fill_symbols(marked: str, answer: str):
    """marked with each [?] filled from answer, or None if anything else changed.

    The original text, line breaks included, is kept.
    """
    fills = symbol_fills(marked, answer)
    return None if fills is None else _put(marked, fills)


# ASCII stand-ins a model writes for a lost sign; a dash in a [?] is a minus.
_SAME_SIGN = {"+/-": "\u00b1", "+-": "\u00b1", ">=": "\u2265", "<=": "\u2264",
              "-": "\u2212", "\u2013": "\u2212"}


def normal_fill(fill: str) -> str:
    import unicodedata
    f = unicodedata.normalize("NFKC", fill).strip()
    return _SAME_SIGN.get(f, f)


def codes_agree(codes, fills) -> bool:
    """Same font:code -> same sign; different codes of one font -> different signs.

    Refuses e.g. Ang p1 "versus [?]10.8 [?] 24.1" filled "+-10.8 +- 24.1" (minus and
    plus-minus are different codes) and "mean = SD 4.4 +- 13.7" (one code, two signs).
    """
    if len(codes) != len(fills):
        return False
    seen = {}
    for code, fill in zip(codes, fills):
        if seen.setdefault(code, fill) != fill:
            return False
    items = list(seen.items())
    for a, (c1, f1) in enumerate(items):
        for c2, f2 in items[a + 1:]:
            if f1 == f2 and c1.rsplit(":", 1)[0] == c2.rsplit(":", 1)[0]:
                return False
    return True


def _accept(line: str, texts, codes):
    """line filled from the first answer text that passes every check, or None."""
    for t in texts:
        fills = symbol_fills(line, t)
        if fills is None:
            continue
        fills = [normal_fill(f) for f in fills]
        if codes and not codes_agree(codes, fills):
            continue
        return _put(line, fills)
    return None


# --- Per-line fill: only lines with [?] go to the model ----------------------
# A small model cannot copy back a whole page unchanged, so each line with
# [?] is sent on its own (numbered, LINES_PER_CALL per call, with the image)
# and checked on its own by fill_symbols(); a refused line keeps its [?].
LINES_PROMPT = (
    "The numbered lines below were copied from the text layer of this page "
    "image. Their font lost some symbols; each lost symbol is shown as [?]. "
    "Find each line in the image and write it again with each [?] replaced "
    "by the symbol printed there (for example ±, =, −, <, >, ≤, ≥, ×, °). "
    "Keep the line number and change nothing else. Use plain characters, "
    "not LaTeX. Reply with the numbered lines only, one per line, as: "
    "number| text"
)
LINES_PER_CALL = 5


def fill_lines(hint: str, ask, codes=None):
    """(text, [?] left, refused): fill [?] line by line; ask(prompt) -> answer.

    AI lines are matched by content, not by number: a small model often puts
    the right line under the wrong number (Ang p4: up to 10 lines off). Each
    answer line may fill the line it was numbered for or any other line of
    the page that still has [?], but only where fill_symbols() accepts it
    (same text, only symbols in the [?]). A row is tried with and without
    its number prefix, since text lines can start with "1.6;".
    refused lists (line, answer under its number or None) for lines that
    kept their [?].
    """
    import re
    lines = hint.split("\n")
    todo = [i for i, line in enumerate(lines) if MARK in line]
    numbered = {}  # line index -> answer the model gave under that number
    line_codes = {}  # line index -> font:code of each [?] on that line
    if codes is not None and len(codes) == hint.count(MARK):
        k = 0
        for i, line in enumerate(lines):
            line_codes[i] = codes[k:k + line.count(MARK)]
            k += line.count(MARK)
    for start in range(0, len(todo), LINES_PER_CALL):
        batch = [i for i in todo[start:start + LINES_PER_CALL] if MARK in lines[i]]
        if not batch:
            continue  # already filled by an earlier answer
        body = "\n".join(f"{k}| {lines[i]}" for k, i in enumerate(batch, 1))
        answer = ask(f"{LINES_PROMPT}\n\n{body}") or ""
        for row in answer.splitlines():
            if not row.strip():
                continue
            m = re.match(r"^\s*(\d+)\s*[|:.)]\s?(.*)$", row)
            own = None
            texts = [row.strip()]
            if m:
                texts.insert(0, m.group(2))
                k = int(m.group(1))
                if 1 <= k <= len(batch):
                    own = batch[k - 1]
                    numbered.setdefault(own, m.group(2))
            elif len(batch) == 1:
                own = batch[0]
                numbered.setdefault(own, row.strip())
            order = ([own] if own is not None else []) + [i for i in todo if i != own]
            for i in order:
                if MARK not in lines[i]:
                    continue
                filled = _accept(lines[i], texts, line_codes.get(i))
                if filled is not None:
                    lines[i] = filled
                    break
    refused = [(lines[i], numbered.get(i)) for i in todo if MARK in lines[i]]
    text = "\n".join(lines)
    return text, text.count(MARK), refused


# --- Document-wide vote per font code ---------------------------------------
# One font code always prints the same sign, so fills of one font:code are
# compared over the whole document. Ang: "P [?] 0.01" was filled "<" and
# "adjusted P [?] 0.8" ">" while the same code is "=" everywhere else.
VOTE_MIN = 2
VOTE_SHARE = 0.8


def _font(code: str) -> str:
    return code.rsplit(":", 1)[0]


def code_votes(pages):
    """(agreed, keep) from (codes, fills) per page; a fill of None is a [?].

    agreed: font:code -> sign with >= VOTE_MIN votes and >= VOTE_SHARE of the
    votes; every [?] with that code gets it and other fills are changed to it.
    keep: codes whose fills all agree (a single vote stays, is not copied).
    Any other code: its fills go back to [?]. Two codes of one font cannot be
    the same sign, so such codes are trusted by neither list.
    """
    from collections import Counter
    count = {}
    for codes, fills in pages:
        for c, f in zip(codes, fills):
            if f is not None:
                count.setdefault(c, Counter())[f] += 1
    agreed, keep = {}, set()
    for c, cnt in count.items():
        sign, n = cnt.most_common(1)[0]
        if n >= VOTE_MIN and n >= VOTE_SHARE * sum(cnt.values()) - 1e-9:
            agreed[c] = sign
        if len(cnt) == 1:
            keep.add(c)
    same = {}
    for c, sign in agreed.items():
        same.setdefault((_font(c), sign), []).append(c)
    for cs in same.values():
        if len(cs) > 1:
            for c in cs:
                del agreed[c]
                keep.discard(c)
    taken = {(_font(c), sign) for c, sign in agreed.items()}
    for c in list(keep):
        if c not in agreed and (_font(c), next(iter(count[c]))) in taken:
            keep.discard(c)
    return agreed, keep


def _fills_from(hint: str, text: str):
    """Sign put in each [?] of hint to give text (None = still [?]), or None."""
    import re
    parts = hint.split(MARK)
    m = re.fullmatch("(.{1,3}?)".join(re.escape(p) for p in parts), text, re.S)
    return None if not m else [None if g == MARK else g for g in m.groups()]


def _vote_pages(done, hybrid, log):
    """Apply the document-wide vote to hybrid pages, then warn per page."""
    found = []
    for idx, n, hint, codes in hybrid:
        ok = codes is not None and len(codes) == hint.count(MARK)
        found.append(_fills_from(hint, done[idx]["text"]) if ok else None)
    agreed, keep = code_votes(
        [(h[3], f) for h, f in zip(hybrid, found) if f is not None])
    for (idx, n, hint, codes), fills in zip(hybrid, found):
        if fills is not None:
            new = [agreed[c] if c in agreed else f if c in keep else None
                   for c, f in zip(codes, fills)]
            pairs = list(zip(fills, new))
            changed = sum(1 for f, g in pairs if f is not None and g is not None and f != g)
            added = sum(1 for f, g in pairs if f is None and g is not None)
            back = sum(1 for f, g in pairs if f is not None and g is None)
            if changed or added:
                log(f"    page {n}: document vote (same font code): {changed} "
                    f"fill(s) corrected, {added} [?] filled")
            if back:
                log(f"    page {n}: {back} fill(s) disagree with the same font "
                    "code elsewhere - back to [?]")
            done[idx]["text"] = _put(hint, [g if g is not None else MARK for g in new])
        total = hint.count(MARK)
        left = done[idx]["text"].count(MARK)
        if left:
            log(f"    WARNING: page {n}: {left} of {total} [?] left (AI changed "
                "other text on those lines) - check against the PDF")
        done[idx]["method"] = ("hybrid" if not left else
                               "hybrid_unresolved" if left == total else "hybrid_partial")


def _process_file(path: Path, out_dir, header: str, model: str, call, log,
                  rec_dir=None) -> str:
    """Read one file, transcribe image pages, summarise, write the record."""
    done = []
    debug = []  # (page, line, AI answer) for lines that kept their [?]
    hybrid = []  # (index in done, page, hint, codes) for the vote
    for page in reader.read_input(path):
        if page["text"] is not None:
            done.append({"page": page["page"], "text": page["text"], "method": "text"})
        elif page.get("hint"):
            n = page["page"]
            total = page["hint"].count(MARK)
            log(f"    page {n}: lost symbols, AI filling {total} [?] line by line...")
            text, left, refused = fill_lines(
                page["hint"], lambda p, png=page["png"]: call(p, images=[png]),
                codes=page.get("codes"))
            debug += [(n, line, ans) for line, ans in refused]
            hybrid.append((len(done), n, page["hint"], page.get("codes")))
            done.append({"page": n, "text": text, "method": "hybrid"})
        else:
            log(f"    page {page['page']}: AI reading...")
            text = call(TRANSCRIBE_PROMPT, images=[page["png"]]).strip()
            done.append({"page": page["page"], "text": text, "method": "vision"})
    _vote_pages(done, hybrid, log)
    full = "\n\n".join(f"[Page {p['page']}]\n{p['text']}" for p in done)
    if debug:
        dbg = Path(out_dir) / f"{header}_FILL_DEBUG.txt"
        dbg.parent.mkdir(parents=True, exist_ok=True)
        dbg.write_text("".join(
            f"[Page {n}]\nTEXT: {line}\nAI:   "
            f"{ans if ans is not None else '(no line returned)'}\n\n"
            for n, line, ans in debug), encoding="utf-8")
        log(f"    AI answers for refused lines: {dbg}")
    log("    summarising...")
    try:
        summary = _summarise(SUMMARY_PROMPT, full, call, log,
                             head=f"File: {path.name}\n\n")
    except TooLongError as exc:
        log(f"    WARNING: summary not written: {exc}")
        summary = (f"[Summary not written: {exc}. The full text below is "
                   "complete. Raise OLLAMA_CONTEXT or use a model with a "
                   "larger context.]")
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
    try:
        synopsis = _summarise(SYNOPSIS_PROMPT, body, call, log)
    except TooLongError as exc:
        log(f"    WARNING: synopsis not written: {exc}")
        synopsis = (f"[Synopsis not written: {exc}. The summary of each "
                    f"file follows.]\n\n{body}")
    if result["failed"]:
        synopsis += ("\n\nNot included (could not be read): "
                     + ", ".join(n for n, _ in result["failed"]))
    result["summary"] = output.write_summary(out_dir, header, "SYNOPSIS",
                                             synopsis, model)
    return result
