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

class RoB2Assessor:
    def __init__(self, model="claude-opus-4-7", api_key: Optional[str]=None):
        self.model=model
        self.client=anthropic.Anthropic(
            api_key=api_key or os.environ["ANTHROPIC_API_KEY"])

    def assess_by_file_id(self, file_id, filename="") -> dict:
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

    def assess_batch(self, included_records, delay_seconds=1.5) -> list[dict]:
        results=[]
        for i,r in enumerate(included_records,1):
            logger.info(f"[ROB2 {i}/{len(included_records)}] {r['filename']}")
            results.append(self.assess_by_file_id(r["file_id"],r["filename"]))
            if i<len(included_records): time.sleep(delay_seconds)
        return results
