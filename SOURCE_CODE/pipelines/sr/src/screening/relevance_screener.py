# SOURCE_CODE/pipelines/sr/src/screening/relevance_screener.py
import json, logging, os, time
from pathlib import Path
from typing import Optional
import anthropic

logger      = logging.getLogger(__name__)
BETA_HEADER = "files-api-2025-04-14"

# Screening reads the FRONT of the paper (title/abstract/methods carry the
# PICO signal). Both the text path and the OCR fallback share one budget:
MAX_SCREEN_PAGES = 8     # pages considered, both extraction paths
MAX_SCREEN_CHARS = 6000  # total chars passed to the screening prompt

PROMPT = """You are a systematic review methodologist performing full-text screening.
PICO CRITERIA:\n{pico}\nINCLUSION:\n{inclusion}\nEXCLUSION:\n{exclusion}
The attached PDF is a candidate RCT. Return ONLY valid JSON:
{{"decision":"INCLUDE"|"EXCLUDE"|"UNCERTAIN","confidence":<0.0-1.0>,
"pico_match":{{"population":true|false|null,"intervention":true|false|null,
"comparator":true|false|null,"outcome":true|false|null,"study_design":true|false|null}},
"exclusion_reasons":["..."],"rationale":"<=150 words","is_rct":true|false|null}}
Bias toward INCLUDE when uncertain."""

class RelevanceScreener:
    def __init__(self, pico_criteria, inclusion_criteria, exclusion_criteria,
                 model="claude-opus-4-7", api_key=None, provider="anthropic"):
        self.pico      = pico_criteria
        self.inclusion = inclusion_criteria
        self.exclusion = exclusion_criteria
        self.model     = model
        self.provider  = provider.lower()
        self.client    = anthropic.Anthropic(
            api_key=api_key or os.environ.get("ANTHROPIC_API_KEY", ""))

    def _prompt(self):
        return PROMPT.format(
            pico      = "\n".join(f"  {k.upper()}: {v}" for k, v in self.pico.items()),
            inclusion = "\n".join(f"  - {c}" for c in self.inclusion),
            exclusion = "\n".join(f"  - {c}" for c in self.exclusion))

    def screen_by_file_id(self, file_id, filename="") -> dict:
        try:
            resp = self.client.beta.messages.create(
                model=self.model, max_tokens=1024,
                messages=[{"role": "user", "content": [
                    {"type": "document", "source": {"type": "file", "file_id": file_id},
                     "cache_control": {"type": "ephemeral"}},
                    {"type": "text", "text": self._prompt()}]}],
                betas=[BETA_HEADER])
            raw = resp.content[0].text.strip()
            # Use relative import
            from ..utils.json_utils import extract_json
            r = extract_json(raw)
            r.update({"file_id": file_id, "filename": filename, "error": None})
            return r
        except Exception as e:
            logger.error(f"Screening failed {filename}: {e}")
            return {"file_id": file_id, "filename": filename, "decision": "UNCERTAIN",
                    "confidence": 0.0, "pico_match": {}, "exclusion_reasons": [],
                    "rationale": f"Error: {e}", "is_rct": None, "error": str(e)}

    def screen_by_pdf_path(self, pdf_path, filename="") -> dict:
        try:
            pdf_text = ""
            try:
                import pdfplumber
                with pdfplumber.open(pdf_path) as pdf:
                    pages    = pdf.pages[:MAX_SCREEN_PAGES]
                    pdf_text = "\n\n".join(p.extract_text() or "" for p in pages).strip()
            except Exception as txt_err:
                logger.warning(f"pdfplumber failed for {filename}: {txt_err}")

            # --- Detect an unusable text layer and fall back to OCR ---
            # Three distinct conditions were previously logged under one
            # blanket "Garbled text detected" message; name the reason so
            # the log distinguishes a scan from a broken-CMap layer (#18).
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
                    # One shared budget, filled front-to-back, matching the
                    # pdfplumber path. The old per-page t[:800] cap starved
                    # screening of the abstract and saturated at exactly
                    # 8*800 + 7*2 = 6414 chars on every >=8-page paper -
                    # the identical "OCR extracted 6414 chars" lines seen
                    # across four different PDFs in real runs.
                    ocr_chunks = []
                    _total = 0
                    _pages_ocred = 0
                    with fitz.open(pdf_path) as doc:
                        for i in range(min(MAX_SCREEN_PAGES, len(doc))):
                            pix = doc[i].get_pixmap(matrix=fitz.Matrix(2, 2))
                            img = Image.open(io.BytesIO(pix.tobytes("png")))
                            t = pytesseract.image_to_string(img).strip()
                            _pages_ocred += 1
                            if t:
                                ocr_chunks.append(t)
                                _total += len(t)
                            if _total >= MAX_SCREEN_CHARS:
                                # Budget met - anything OCR'd beyond this
                                # would be cut by the prompt truncation
                                # below, so stop paying OCR time for it.
                                break
                    pdf_text = "\n\n".join(ocr_chunks).strip()
                    _note = (
                        f" (prompt uses first {MAX_SCREEN_CHARS})"
                        if len(pdf_text) > MAX_SCREEN_CHARS else ""
                    )
                    logger.info(
                        f"OCR extracted {len(pdf_text)} chars from "
                        f"{_pages_ocred} page(s) of {filename}{_note}"
                    )
                except Exception as ocr_err:
                    logger.warning(f"OCR failed for {filename}: {ocr_err}")

            if not pdf_text:
                pdf_text = f"[Could not extract text from {filename}]"
            if len(pdf_text) > MAX_SCREEN_CHARS:
                pdf_text = pdf_text[:MAX_SCREEN_CHARS] + "\n...[truncated]"
            full_prompt = (
                f"Article filename: {filename}\n\n"
                f"--- ARTICLE TEXT (first {MAX_SCREEN_PAGES} pages) ---\n{pdf_text}\n"
                f"--- END OF ARTICLE TEXT ---\n\n"
                + self._prompt()
            )
            import urllib.request as _ur
            import urllib.error as _ue
            import json as _json

            # Honor DASHSCOPE_BASE_URL like the extraction/RoB2 modules do
            # (Session 13, #37): a hardcoded URL here silently diverges
            # from the endpoint every other stage is configured to use.
            _dashscope_base = os.environ.get(
                "DASHSCOPE_BASE_URL",
                "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
            ).rstrip("/")
            provider_urls = {
                "deepseek": "https://api.deepseek.com/chat/completions",
                "qwen":     f"{_dashscope_base}/chat/completions",
                "openai":   "https://api.openai.com/v1/chat/completions",
                "groq":     "https://api.groq.com/openai/v1/chat/completions",
                "ollama":   f"{os.environ.get('OLLAMA_HOST','http://localhost:11434')}/v1/chat/completions",
            }
            api_key_map = {
                "deepseek": os.environ.get("DEEPSEEK_API_KEY", ""),
                "qwen":     os.environ.get("DASHSCOPE_API_KEY", ""),
                "openai":   os.environ.get("OPENAI_API_KEY", ""),
                "groq":     os.environ.get("GROQ_API_KEY", ""),
                "ollama":   "ollama",
            }
            url     = provider_urls.get(self.provider, provider_urls["deepseek"])
            api_key = api_key_map.get(self.provider, "")
            payload = _json.dumps({
                "model":      self.model,
                "messages":   [{"role": "user", "content": full_prompt}],
                "max_tokens": 1024,
                "stream":     False,
            }).encode()
            req = _ur.Request(
                url, data=payload,
                headers={"Content-Type":  "application/json",
                         "Authorization": f"Bearer {api_key}"},
                method="POST")
            # Retry transient network failures. Observed in a real run: a
            # single "Remote end closed connection without response" during
            # screening silently removed a paper from the ENTIRE review
            # (screening error -> UNCERTAIN -> not INCLUDE -> dropped from
            # extraction, RoB2 and the pooled estimate) with one ERROR line
            # in ~100 lines of log. Auth errors (401/403) are never retried
            # - same principle as providers.py's #34 fix.
            import http.client as _hc
            _last_err = None
            for _attempt in range(1, 4):
                try:
                    with _ur.urlopen(req, timeout=120) as resp:
                        data = _json.loads(resp.read())
                    break
                except _ue.HTTPError as http_err:
                    body = http_err.read().decode("utf-8", errors="replace")
                    logger.error(
                        f"HTTP {http_err.code} from {self.provider}: {body[:500]}")
                    if http_err.code in (401, 403):
                        raise  # auth is never transient
                    _last_err = http_err
                except (_ue.URLError, _hc.HTTPException,
                        ConnectionError, TimeoutError, OSError) as net_err:
                    _last_err = net_err
                if _attempt < 3:
                    logger.warning(
                        f"Screening call attempt {_attempt}/3 failed for "
                        f"{filename} ({type(_last_err).__name__}: {_last_err})"
                        f" - retrying in {2 * _attempt}s")
                    time.sleep(2 * _attempt)
            else:
                raise _last_err
            raw = data["choices"][0]["message"]["content"].strip()
            from ..utils.json_utils import extract_json
            r = extract_json(raw)
            r.update({"file_id": None, "filename": filename, "error": None})
            return r
        except Exception as e:
            logger.error(f"Screening failed {filename}: {e}")
            return {"file_id": None, "filename": filename, "decision": "UNCERTAIN",
                    "confidence": 0.0, "pico_match": {}, "exclusion_reasons": [],
                    "rationale": f"Error: {e}", "is_rct": None, "error": str(e)}

    def screen_batch(self, upload_records, delay_seconds=1.0) -> list[dict]:
        results = []
        for i, r in enumerate(upload_records, 1):
            logger.info(f"[SCREEN {i}/{len(upload_records)}] {r['filename']}")
            if self.provider == "anthropic" and r.get("file_id"):
                results.append(self.screen_by_file_id(r["file_id"], r["filename"]))
            else:
                results.append(self.screen_by_pdf_path(
                    r.get("pdf_path", ""), r["filename"]))
            if i < len(upload_records):
                time.sleep(delay_seconds)
        return results