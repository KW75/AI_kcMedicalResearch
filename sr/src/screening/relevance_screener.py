import json, logging, os, time
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
                 model="claude-opus-4-7", api_key: Optional[str]=None):
        self.pico=pico_criteria; self.inclusion=inclusion_criteria
        self.exclusion=exclusion_criteria; self.model=model
        self.client=anthropic.Anthropic(
            api_key=api_key or os.environ["ANTHROPIC_API_KEY"])

    def _prompt(self):
        return PROMPT.format(
            pico      = "\n".join(f"  {k.upper()}: {v}" for k,v in self.pico.items()),
            inclusion = "\n".join(f"  - {c}" for c in self.inclusion),
            exclusion = "\n".join(f"  - {c}" for c in self.exclusion))

    def screen_by_file_id(self, file_id, filename="") -> dict:
        try:
            resp = self.client.beta.messages.create(
                model=self.model, max_tokens=1024,
                messages=[{"role":"user","content":[
                    {"type":"document","source":{"type":"file","file_id":file_id},
                     "cache_control":{"type":"ephemeral"}},
                    {"type":"text","text":self._prompt()}]}],
                betas=[BETA_HEADER])
            raw = resp.content[0].text.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"): raw=raw[4:]
            r = json.loads(raw)
            r.update({"file_id":file_id,"filename":filename,"error":None})
            return r
        except Exception as e:
            logger.error(f"Screening failed {filename}: {e}")
            return {"file_id":file_id,"filename":filename,"decision":"UNCERTAIN",
                    "confidence":0.0,"pico_match":{},"exclusion_reasons":[],
                    "rationale":f"Error: {e}","is_rct":None,"error":str(e)}

    def screen_batch(self, upload_records, delay_seconds=1.0) -> list[dict]:
        results=[]
        for i,r in enumerate(upload_records,1):
            logger.info(f"[SCREEN {i}/{len(upload_records)}] {r['filename']}")
            results.append(self.screen_by_file_id(r["file_id"],r["filename"]))
            if i<len(upload_records): time.sleep(delay_seconds)
        return results
