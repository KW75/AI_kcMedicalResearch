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
        return api_key or os.environ["OPENAI_API_KEY"], None   # default OpenAI base
    if provider == "ollama":
        base = os.environ.get("OLLAMA_URL", "http://localhost:11434") + "/v1"
        return "ollama", base
    raise ValueError(f"Unknown provider: {provider}")


class RoB2Assessor:
    def __init__(self, model="qwen3.7-plus", provider="qwen", api_key: Optional[str]=None):
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
                model=self.model, max_tokens=1024,
                messages=[{"role":"user","content":[
                    {"type":"document","source":{"type":"file","file_id":file_id},
                     "cache_control":{"type":"ephemeral"}},
                    {"type":"text","text":ROB2_PROMPT}]}],
                betas=[BETA_HEADER])
            raw = resp.content[0].text.strip()
            if raw.startswith("```"):
                raw=raw.split("```")[1]
                if raw.startswith("json"): raw=raw[4:]
            r = json.loads(raw)
            r.update({"file_id":file_id,"filename":filename,"error":None})
            return r
        except Exception as e:
            return {"file_id":file_id,"filename":filename,"error":str(e),
                    "domains":{},"overall_judgment":"High"}

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
            max_tokens=1024,
            extra_body={"enable_thinking": False},
        )
        return resp.choices[0].message.content.strip()

    def assess_by_pdf_path(self, pdf_path: str, filename="") -> dict:
        """Vision-based assessment for non-Anthropic providers."""
        try:
            from pdf2image import convert_from_path
            import io, base64
            poppler = os.environ.get("POPPLER_PATH")
            pages   = convert_from_path(pdf_path, dpi=150, poppler_path=poppler)
            images  = []
            for page in pages:
                buf = io.BytesIO()
                page.save(buf, format="PNG")
                images.append(base64.b64encode(buf.getvalue()).decode())
            raw = self._call_with_images(images, ROB2_PROMPT)
            if raw.startswith("```"):
                raw=raw.split("```")[1]
                if raw.startswith("json"): raw=raw[4:]
            r = json.loads(raw)
            r.update({"file_id": None, "filename": filename, "error": None})
            return r
        except Exception as e:
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
    

