# SOURCE_CODE/pipelines/sr/src/screening/rob2_tool.py
import json, logging, os, time
from typing import Optional
import anthropic

logger      = logging.getLogger(__name__)
BETA_HEADER = "files-api-2025-04-14"

# Session 38: the model gets rob2_text's pick (start + Methods + Results +
# registration lines, up to MAX_ROB2_SECTION_CHARS). MAX_ROB2_PAGES and
# MAX_ROB2_CHARS are the page-reading budget when no shared text is given;
# MAX_ROB2_CHARS is also the no-Methods fallback and the cut on the retry
# after an empty answer.
MAX_ROB2_PAGES = 12    # pages considered, both extraction paths
MAX_ROB2_CHARS = 6000  # page-reading budget; no-Methods fallback; retry cut
MAX_ROB2_SECTION_CHARS = 50000  # Methods + Results sent to the RoB2 prompt (Session 38: 20000 cut ITT/dropout text; McCrae needs ~48000, ~12k tokens); MAX_ROB2_CHARS stays the page-reading budget

ROB2_PROMPT = """You are a Cochrane methodologist applying RoB 2.0.
Assess the attached RCT across five domains. Return ONLY valid JSON:
{"study":"<FirstAuthor Year>",
 "domains":{"randomisation":"Low|Some concerns|High",
            "deviations":"Low|Some concerns|High",
            "missing_data":"Low|Some concerns|High",
            "outcome_measurement":"Low|Some concerns|High",
            "reported_result":"Low|Some concerns|High"},
 "overall_judgment":"Low|Some concerns|High",
 "justifications":{"randomisation":"<text>","deviations":"<text>",
                   "missing_data":"<text>","outcome_measurement":"<text>",
                   "reported_result":"<text>"}}"""


def _openai_compat_creds(provider: str, api_key: Optional[str] = None):
    """Return (api_key, base_url) for OpenAI-compatible providers."""
    if provider == "qwen":
        return (
            api_key or os.environ["DASHSCOPE_API_KEY"],
            os.environ.get("DASHSCOPE_BASE_URL",
                           "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"),
        )
    if provider == "groq":
        return api_key or os.environ["GROQ_API_KEY"], "https://api.groq.com/openai/v1"
    if provider == "deepseek":
        return api_key or os.environ["DEEPSEEK_API_KEY"], "https://api.deepseek.com"
    if provider == "openai":
        return api_key or os.environ["OPENAI_API_KEY"], None
    if provider == "ollama":
        base = os.environ.get("OLLAMA_URL", "http://localhost:11434") + "/v1"
        return "ollama", base
    raise ValueError(f"Unknown provider: {provider}")


_ROB2_KEYS = ("randomisation", "deviations", "missing_data",
              "outcome_measurement", "reported_result")
NOT_ASSESSED = "Not assessed"


def _norm_judgement(v):
    """'High risk' / 'LOW' / 'some concerns' -> High / Low / Some concerns."""
    s = str(v or "").strip().lower()
    if "high" in s:
        return "High"
    if "some" in s or "concern" in s:
        return "Some concerns"
    if "low" in s:
        return "Low"
    return None


def apply_rob2_overall(result: dict) -> dict:
    """RoB 2 overall from the domains (Session 37: Ang had a High domain but
    the model said 'Some concerns'). Any High -> High; all five Low -> Low;
    all five assessed otherwise -> Some concerns; domains missing and none
    High -> Not assessed. The model's own answer is kept in overall_model."""
    doms = result.get("domains")
    if not isinstance(doms, dict):
        doms = {}
    result["domains"] = {k: (_norm_judgement(v) or v) for k, v in doms.items()}
    vals = [_norm_judgement(result["domains"].get(k)) for k in _ROB2_KEYS]
    result["overall_model"] = result.get("overall_judgment")
    if "High" in vals:
        overall = "High"
    elif None in vals:
        overall = NOT_ASSESSED
    elif all(v == "Low" for v in vals):
        overall = "Low"
    else:
        overall = "Some concerns"
    if overall != _norm_judgement(result["overall_model"]):
        logger.info(f"[ROB2] {result.get('filename', '?')}: overall set to "
                    f"'{overall}' by the domain rule (model said "
                    f"'{result['overall_model']}')")
    result["overall_judgment"] = overall
    return result


class RoB2Assessor:
    def __init__(self, model="qwen-plus-latest", provider="qwen", api_key: Optional[str] = None):
        # NOTE: default matches providers.py's QWEN_MODEL default (text
        # model). The previous default ("qwen3.7-plus") didn't match
        # anything in providers.py's model registry. assess_by_pdf_path()
        # only ever calls _call_with_text() - _call_with_images() exists in
        # this class but is never actually invoked from any code path - so
        # the text model, not the vision model, is the correct default here.
        # In normal pipeline usage this default is overridden by sr/main.py
        # passing model=args.model explicitly, but it's a landmine for
        # direct construction (tests, scripts) that omit model.
        self.provider = provider.lower()
        self.model    = model
        if self.provider == "anthropic":
            self.client = anthropic.Anthropic(
                api_key=api_key or os.environ["ANTHROPIC_API_KEY"])
        else:
            from openai import OpenAI
            _key, _base = _openai_compat_creds(self.provider, api_key)
            self.client = OpenAI(api_key=_key, base_url=_base)

    def assess_by_file_id(self, file_id, filename="") -> dict:
        """Anthropic Files API path only."""
        if self.provider != "anthropic":
            raise RuntimeError(
                "assess_by_file_id requires Anthropic. "
                "Use assess_by_pdf_path() for other providers."
            )
        try:
            resp = self.client.beta.messages.create(
                model=self.model, max_tokens=2048,
                messages=[{"role": "user", "content": [
                    {"type": "document", "source": {"type": "file", "file_id": file_id},
                     "cache_control": {"type": "ephemeral"}},
                    {"type": "text", "text": ROB2_PROMPT}
                ]}],
                betas=[BETA_HEADER])
            raw = resp.content[0].text.strip()
            from ..utils.json_utils import extract_json
            r = extract_json(raw)
            r.update({"file_id": file_id, "filename": filename, "error": None})
            return apply_rob2_overall(r)
        except Exception as e:
            return {"file_id": file_id, "filename": filename, "error": str(e),
                    "domains": {}, "overall_judgment": NOT_ASSESSED,
                    "overall_model": None}

    def _call_with_images(self, base64_images: list, prompt: str) -> str:
        """Send PDF pages as base64 images via OpenAI-compatible vision API."""
        content = [{"type": "text", "text": prompt}]
        for img in base64_images[:5]:
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{img}"}
            })
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": content}],
            max_tokens=2048,
            extra_body={"enable_thinking": False},
        )
        return resp.choices[0].message.content.strip()

    def _call_with_text(self, pdf_text: str, prompt: str) -> str:
        """Send PDF text via OpenAI-compatible API with retry on empty response."""
        # Session 38: first try sends the whole text (rob2_text already limits
        # it to MAX_ROB2_SECTION_CHARS); only the retry after an empty answer
        # is cut to MAX_ROB2_CHARS. Was [6000, 3000]: the model saw 6000 max.
        for attempt, max_chars in enumerate([len(pdf_text), MAX_ROB2_CHARS]):
            truncated = pdf_text[:max_chars]
            logger.info("[ROB2 SEND] attempt %d: %d of %d chars to the model",
                        attempt + 1, len(truncated), len(pdf_text))
            full = f"{prompt}\n\n--- ARTICLE TEXT ---\n{truncated}\n--- END ---"
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": full}],
                max_tokens=2048,
                extra_body={"enable_thinking": False},
            )
            content = resp.choices[0].message.content
            if content and content.strip():
                return content.strip()
            if attempt == 0:
                time.sleep(2)
        raise ValueError("Empty response from model after retry")

    def assess_by_pdf_path(self, pdf_path: str, filename="", paper_text=None) -> dict:
        """Text-based RoB 2.0 assessment using pdfplumber with OCR fallback."""
        try:
            pdf_text = paper_text or ""
            if not paper_text:   # Session 37: shared text given -> do not reopen the PDF

                # --- Attempt 1: pdfplumber ---
                try:
                    import pdfplumber
                    with pdfplumber.open(pdf_path) as pdf:
                        chunks = []
                        _total = 0
                        for p in pdf.pages[:MAX_ROB2_PAGES]:
                            t = (p.extract_text() or "").strip()
                            if t:
                                chunks.append(t)
                                _total += len(t)
                            if _total >= MAX_ROB2_CHARS:
                                break
                        pdf_text = "\n\n".join(chunks).strip()
                except Exception as txt_err:
                    logger.warning(f"pdfplumber failed for {filename}: {txt_err}")

                # --- Detect an unusable text layer and fall back to OCR ---
                _fallback_reason = None
                if not pdf_text:
                    _fallback_reason = "no extractable text layer"
                elif "(cid:" in pdf_text:
                    _fallback_reason = "CID markers in text layer"
                elif pdf_text.count(" ") < 20:
                    _fallback_reason = "text layer nearly space-free (possible broken CMap, see #18)"
                if _fallback_reason:
                    logger.info(
                        f"Unusable text layer for {filename} "
                        f"({_fallback_reason}) - switching to OCR"
                    )
                    try:
                        import fitz
                        import pytesseract
                        import io
                        from PIL import Image
                        import sys
                        if sys.platform == "win32":
                            # Common default install location on Windows. Only
                            # override if it's actually there - if the user
                            # installed elsewhere or added tesseract to PATH,
                            # leave pytesseract's own discovery alone.
                            _default_win_path = (
                                r"C:\Program Files\Tesseract-OCR\tesseract.exe"
                            )
                            if os.path.exists(_default_win_path):
                                pytesseract.pytesseract.tesseract_cmd = _default_win_path
                        # On macOS/Linux/Docker, tesseract is expected on PATH
                        # (e.g. via apt-get/brew install tesseract-ocr) - setting
                        # a Windows-only absolute path here would silently break
                        # OCR everywhere else.
                        # One shared budget, filled front-to-back, with early
                        # stop once met. The old per-page t[:1500] cap over up
                        # to 12 pages saturated at 12*1500 + 11*2 = 18022
                        # chars (the exact counts seen in real runs), of which
                        # the prompt truncation then kept only the first 6000
                        # - most of the OCR time bought nothing. (The old page
                        # selection list(range(3)) + list(range(3, n))[:9] was
                        # also just the first 12 pages, written confusingly.)
                        ocr_chunks = []
                        _total = 0
                        _pages_ocred = 0
                        with fitz.open(pdf_path) as doc:
                            for i in range(min(MAX_ROB2_PAGES, len(doc))):
                                pix = doc[i].get_pixmap(matrix=fitz.Matrix(2, 2))
                                img = Image.open(io.BytesIO(pix.tobytes("png")))
                                t = pytesseract.image_to_string(img).strip()
                                _pages_ocred += 1
                                if t:
                                    ocr_chunks.append(t)
                                    _total += len(t)
                                if _total >= MAX_ROB2_CHARS:
                                    break
                        pdf_text = "\n\n".join(ocr_chunks).strip()
                        _note = (
                            f" (prompt uses first {MAX_ROB2_CHARS})"
                            if len(pdf_text) > MAX_ROB2_CHARS else ""
                        )
                        logger.info(
                            f"OCR extracted {len(pdf_text)} chars from "
                            f"{_pages_ocred} page(s) of {filename}{_note}"
                        )
                    except Exception as ocr_err:
                        logger.warning(f"OCR failed for {filename}: {ocr_err}")

            if not pdf_text:
                pdf_text = f"[Could not extract text from {filename}]"
            # Session 38: Methods + Results instead of the first 6000 chars;
            # no Methods heading -> first MAX_ROB2_CHARS as before.
            from ..utils.paper_sections import rob2_text
            pdf_text, _sec_note = rob2_text(
                pdf_text, limit=MAX_ROB2_SECTION_CHARS,
                fallback_chars=MAX_ROB2_CHARS)
            logger.info(f"[ROB2 TEXT] {filename}: {_sec_note}")

            raw = self._call_with_text(pdf_text, ROB2_PROMPT)
            from ..utils.json_utils import extract_json
            r = extract_json(raw)
            r.update({"file_id": None, "filename": filename, "error": None})
            return apply_rob2_overall(r)
        except Exception as e:
            logger.error(f"RoB2 assessment failed {filename}: {e}")
            return {"file_id": None, "filename": filename, "error": str(e),
                    "domains": {}, "overall_judgment": NOT_ASSESSED,
                    "overall_model": None}

    def assess_batch(self, included_records, delay_seconds=1.5) -> list:
        results = []
        for i, r in enumerate(included_records, 1):
            logger.info(f"[ROB2 {i}/{len(included_records)}] {r['filename']}")
            if self.provider == "anthropic":
                results.append(self.assess_by_file_id(r["file_id"], r["filename"]))
            else:
                results.append(self.assess_by_pdf_path(
                    r.get("pdf_path", ""), r["filename"],
                    paper_text=r.get("paper_text")))
            if i < len(included_records):
                time.sleep(delay_seconds)
        return results