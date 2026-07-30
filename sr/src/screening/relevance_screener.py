import base64, json, logging, os, time
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
                 model="claude-opus-4-7", api_key: Optional[str] = None,
                 provider: str = "anthropic"):
        self.pico       = pico_criteria
        self.inclusion  = inclusion_criteria
        self.exclusion  = exclusion_criteria
        self.model      = model
        self.provider   = provider.lower()
        self.client     = anthropic.Anthropic(
            api_key=api_key or os.environ.get("ANTHROPIC_API_KEY", ""))

    def _prompt(self):
        return PROMPT.format(
            pico      = "\n".join(f"  {k.upper()}: {v}" for k, v in self.pico.items()),
            inclusion = "\n".join(f"  - {c}" for c in self.inclusion),
            exclusion = "\n".join(f"  - {c}" for c in self.exclusion))

    def screen_by_file_id(self, file_id: str, filename: str = "") -> dict:
        """Screen using Anthropic Files API (requires anthropic provider)."""
        try:
            resp = self.client.beta.messages.create(
                model=self.model, max_tokens=1024,
                messages=[{"role": "user", "content": [
                    {"type": "document", "source": {"type": "file", "file_id": file_id},
                     "cache_control": {"type": "ephemeral"}},
                    {"type": "text", "text": self._prompt()}]}],
                betas=[BETA_HEADER])
            raw = resp.content[0].text.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            r = json.loads(raw)
            r.update({"file_id": file_id, "filename": filename, "error": None})
            return r
        except Exception as e:
            logger.error(f"Screening failed {filename}: {e}")
            return {"file_id": file_id, "filename": filename, "decision": "UNCERTAIN",
                    "confidence": 0.0, "pico_match": {}, "exclusion_reasons": [],
                    "rationale": f"Error: {e}", "is_rct": None, "error": str(e)}

    def screen_by_pdf_path(self, pdf_path: str, filename: str = "") -> dict:
        """
        Screen by converting PDF pages to base64 images and sending via
        vision API. Works with any OpenAI-compatible provider.
        """
        try:
            try:
                from pdf2image import convert_from_path
                import os as _os
                poppler = _os.environ.get("POPPLER_PATH")
                pages   = convert_from_path(pdf_path, dpi=120,
                                            poppler_path=poppler,
                                            first_page=1, last_page=6)
                images  = []
                for pg in pages:
                    import io
                    buf = io.BytesIO()
                    pg.save(buf, format="JPEG", quality=70)
                    b64 = base64.b64encode(buf.getvalue()).decode()
                    images.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{b64}",
                                      "detail": "low"},
                    })
            except Exception as img_err:
                logger.warning(f"pdf2image failed for {filename}: {img_err} — using text fallback")
                images = []

            # Build content: images (if any) + text prompt
            content = images + [{"type": "text", "text": self._prompt()}]

            # Call provider via OpenAI-compatible endpoint
            import urllib.request, json as _json
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

            # If no images, send text-only with PDF filename as context
            if not images:
                content = [{"type": "text",
                            "text": f"Article filename: {filename}\n\n" + self._prompt()}]

            payload = _json.dumps({
                "model":    self.model,
                "messages": [{"role": "user", "content": content}],
                "max_tokens": 1024,
                "stream":   False,
            }).encode()
            req = urllib.request.Request(
                url, data=payload,
                headers={"Content-Type": "application/json",
                         "Authorization": f"Bearer {api_key}"},
                method="POST")
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = _json.loads(resp.read())
            raw = data["choices"][0]["message"]["content"].strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            r = _json.loads(raw)
            r.update({"file_id": None, "filename": filename, "error": None})
            return r
        except Exception as e:
            logger.error(f"Screening failed {filename}: {e}")
            return {"file_id": None, "filename": filename, "decision": "UNCERTAIN",
                    "confidence": 0.0, "pico_match": {}, "exclusion_reasons": [],
                    "rationale": f"Error: {e}", "is_rct": None, "error": str(e)}

    def screen_batch(self, upload_records, delay_seconds: float = 1.0) -> list[dict]:
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
