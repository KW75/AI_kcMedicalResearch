# SOURCE_CODE/pipelines/sr/src/screening/relevance_screener.py
import json, logging, os, time
from pathlib import Path
from typing import Optional
import anthropic

logger      = logging.getLogger(__name__)
BETA_HEADER = "files-api-2025-04-14"

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
                    pages    = pdf.pages[:8]
                    pdf_text = "\n\n".join(p.extract_text() or "" for p in pages).strip()
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
                    pytesseract.pytesseract.tesseract_cmd = (
                        r"C:\Program Files\Tesseract-OCR\tesseract.exe"
                    )
                    doc = fitz.open(pdf_path)
                    ocr_chunks = []
                    for i in range(min(8, len(doc))):
                        pix = doc[i].get_pixmap(matrix=fitz.Matrix(2, 2))
                        img = Image.open(io.BytesIO(pix.tobytes("png")))
                        t = pytesseract.image_to_string(img).strip()
                        if t:
                            ocr_chunks.append(t[:800])
                    pdf_text = "\n\n".join(ocr_chunks).strip()
                    logger.info(f"OCR extracted {len(pdf_text)} chars from {filename}")
                except Exception as ocr_err:
                    logger.warning(f"OCR failed for {filename}: {ocr_err}")

            if not pdf_text:
                pdf_text = f"[Could not extract text from {filename}]"
            if len(pdf_text) > 6000:
                pdf_text = pdf_text[:6000] + "\n...[truncated]"
            full_prompt = (
                f"Article filename: {filename}\n\n"
                f"--- ARTICLE TEXT (first 8 pages) ---\n{pdf_text}\n"
                f"--- END OF ARTICLE TEXT ---\n\n"
                + self._prompt()
            )
            import urllib.request as _ur
            import urllib.error as _ue
            import json as _json

            provider_urls = {
                "deepseek": "https://api.deepseek.com/chat/completions",
                "qwen":     "https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions",
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
            try:
                with _ur.urlopen(req, timeout=120) as resp:
                    data = _json.loads(resp.read())
            except _ue.HTTPError as http_err:
                body = http_err.read().decode("utf-8", errors="replace")
                logger.error(f"HTTP {http_err.code} from {self.provider}: {body[:500]}")
                raise
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