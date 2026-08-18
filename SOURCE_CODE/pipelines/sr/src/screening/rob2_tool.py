# SOURCE_CODE/pipelines/sr/src/screening/rob2_tool.py
import json, logging, os, time
from typing import Optional
import anthropic

logger      = logging.getLogger(__name__)
BETA_HEADER = "files-api-2025-04-14"

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
            return r
        except Exception as e:
            return {"file_id": file_id, "filename": filename, "error": str(e),
                    "domains": {}, "overall_judgment": "High"}

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
        for attempt, max_chars in enumerate([6000, 3000]):
            truncated = pdf_text[:max_chars] if len(pdf_text) > max_chars else pdf_text
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

    def assess_by_pdf_path(self, pdf_path: str, filename="") -> dict:
        """Text-based RoB 2.0 assessment using pdfplumber with OCR fallback."""
        try:
            pdf_text = ""

            # --- Attempt 1: pdfplumber ---
            try:
                import pdfplumber
                with pdfplumber.open(pdf_path) as pdf:
                    chunks = []
                    for p in pdf.pages[:20]:
                        t = p.extract_text() or ""
                        if t.strip():
                            chunks.append(t[:800])
                    pdf_text = "\n\n".join(chunks).strip()
            except Exception as txt_err:
                logger.warning(f"pdfplumber failed for {filename}: {txt_err}")

            # --- Detect garbled CID-font text and fall back to OCR ---
            if not pdf_text or "(cid:" in pdf_text or pdf_text.count(" ") < 20:
                logger.info(f"Garbled text detected for {filename}  - switching to OCR")
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
                    doc = fitz.open(pdf_path)
                    total_pages = len(doc)
                    if total_pages <= 6:
                        selected = list(range(total_pages))
                    else:
                        selected = list(range(3)) + list(range(3, total_pages))[:9]
                    ocr_chunks = []
                    for i in selected:
                        pix = doc[i].get_pixmap(matrix=fitz.Matrix(2, 2))
                        img = Image.open(io.BytesIO(pix.tobytes("png")))
                        t = pytesseract.image_to_string(img).strip()
                        if t:
                            ocr_chunks.append(t[:1500])
                    pdf_text = "\n\n".join(ocr_chunks).strip()
                    logger.info(f"OCR extracted {len(pdf_text)} chars from {filename}")
                except Exception as ocr_err:
                    logger.warning(f"OCR failed for {filename}: {ocr_err}")

            if not pdf_text:
                pdf_text = f"[Could not extract text from {filename}]"
            if len(pdf_text) > 6000:
                pdf_text = pdf_text[:6000] + "\n...[truncated]"

            raw = self._call_with_text(pdf_text, ROB2_PROMPT)
            from ..utils.json_utils import extract_json
            r = extract_json(raw)
            r.update({"file_id": None, "filename": filename, "error": None})
            return r
        except Exception as e:
            logger.error(f"RoB2 assessment failed {filename}: {e}")
            return {"file_id": None, "filename": filename, "error": str(e),
                    "domains": {}, "overall_judgment": "High"}

    def assess_batch(self, included_records, delay_seconds=1.5) -> list:
        results = []
        for i, r in enumerate(included_records, 1):
            logger.info(f"[ROB2 {i}/{len(included_records)}] {r['filename']}")
            if self.provider == "anthropic":
                results.append(self.assess_by_file_id(r["file_id"], r["filename"]))
            else:
                results.append(self.assess_by_pdf_path(
                    r.get("pdf_path", ""), r["filename"]))
            if i < len(included_records):
                time.sleep(delay_seconds)
        return results