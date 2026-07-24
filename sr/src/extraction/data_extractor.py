import json, logging, os, time
from typing import Optional
import anthropic

logger      = logging.getLogger(__name__)
BETA_HEADER = "files-api-2025-04-14"

EXTRACTION_PROMPT_TEMPLATE = '''You are a clinical data extractor for a systematic review.

THE REVIEW'S SPECIFIED PRIMARY OUTCOME IS:
  {outcome}

REVIEW PICO CONTEXT:
  POPULATION:   {population}
  INTERVENTION: {intervention}
  COMPARATOR:   {comparator}

CRITICAL: Extract data for the REVIEW'S outcome above, not whichever outcome the
source paper itself calls "primary." Set outcome_match true if found, false if not.
Return null for any field you cannot find. Return ONLY valid JSON matching this schema:
{{"study_metadata":{{"first_author":null,"year":null,"country":null,
  "funding_source":null,"trial_registration_id":null,"journal":null,"doi":null}},
 "participants":{{"n_intervention":null,"n_control":null,"n_total":null,
  "mean_age_intervention":null,"mean_age_control":null,
  "percent_female_intervention":null,"percent_female_control":null,
  "inclusion_criteria_summary":null,"exclusion_criteria_summary":null,
  "condition_or_diagnosis":null}},
 "intervention":{{"name":null,"dose":null,"route":null,
  "frequency":null,"duration_weeks":null,"co_interventions":null}},
 "comparator":{{"name":null,"dose":null,
  "type":"placebo|active_comparator|usual_care|no_treatment|other"}},
 "primary_outcome":{{"outcome_match":true|false,
  "match_rationale":"<=40 word note",
  "name":null,"time_point":null,
  "effect_measure":"OR|RR|MD|SMD|HR|other",
  "effect_estimate":null,"ci_lower_95":null,"ci_upper_95":null,"p_value":null,
  "n_events_intervention":null,"n_events_control":null,
  "mean_intervention":null,"sd_intervention":null,
  "mean_control":null,"sd_control":null}},
 "secondary_outcomes":[{{"name":null,"time_point":null,"effect_measure":null,
  "effect_estimate":null,"ci_lower_95":null,"ci_upper_95":null,"p_value":null}}],
 "adverse_events":{{"any_adverse_event_rr":null,"serious_adverse_event_rr":null,
  "withdrawals_due_to_ae":null,"notes":null}}}}'''


class DataExtractor:
    def __init__(self, pico_criteria: Optional[dict]=None,
                 pico_outcome: Optional[str]=None,
                 model: str="qwen3.7-plus",
                 provider: str="qwen",
                 api_key: Optional[str]=None):
        self.provider = provider.lower()
        self.model    = model
        self.pico     = pico_criteria or {}
        self.outcome  = pico_outcome or self.pico.get("outcome")
        if not self.outcome:
            logger.warning("DataExtractor: no review outcome specified — "
                           "will extract paper's own primary outcome.")
        if self.provider == "anthropic":
            self.client = anthropic.Anthropic(
                api_key=api_key or os.environ["ANTHROPIC_API_KEY"])
        else:
            from openai import OpenAI
            from sr.src.screening.rob2_tool import _openai_compat_creds
            _key, _base = _openai_compat_creds(self.provider, api_key)
            self.client = OpenAI(api_key=_key, base_url=_base)

    def _prompt(self) -> str:
        return EXTRACTION_PROMPT_TEMPLATE.format(
            outcome      = self.outcome or "(not specified)",
            population   = self.pico.get("population", "(not specified)"),
            intervention = self.pico.get("intervention", "(not specified)"),
            comparator   = self.pico.get("comparator", "(not specified)"),
        )

    def extract_by_file_id(self, file_id, filename="") -> dict:
        """Anthropic Files API path only."""
        if self.provider != "anthropic":
            raise RuntimeError(
                "extract_by_file_id requires Anthropic. "
                "Use extract_by_pdf_path() for other providers."
            )
        try:
            resp = self.client.beta.messages.create(
                model=self.model, max_tokens=4096,
                messages=[{"role":"user","content":[
                    {"type":"document","source":{"type":"file","file_id":file_id},
                     "cache_control":{"type":"ephemeral"}},
                    {"type":"text","text":self._prompt()}]}],
                betas=[BETA_HEADER])
            raw = resp.content[0].text.strip()
            if raw.startswith("```"):
                raw=raw.split("```")[1]
                if raw.startswith("json"): raw=raw[4:]
            r = json.loads(raw)
            r.update({"file_id":file_id,"filename":filename,"extraction_error":None})
            return r
        except Exception as e:
            return {"file_id":file_id,"filename":filename,"extraction_error":str(e)}

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
            max_tokens=4096,
            extra_body={"enable_thinking": False},
        )
        return resp.choices[0].message.content.strip()

    def extract_by_pdf_path(self, pdf_path: str, filename="") -> dict:
        """Vision-based extraction for non-Anthropic providers."""
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
            raw = self._call_with_images(images, self._prompt())
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"): raw = raw[4:]
            r = json.loads(raw)
            r.update({"file_id": None, "filename": filename, "extraction_error": None})
            return r
        except Exception as e:
            return {"file_id": None, "filename": filename, "extraction_error": str(e)}

    def extract_batch(self, included_records, delay_seconds=2.0) -> list[dict]:
        results = []
        for i, r in enumerate(included_records, 1):
            logger.info(f"[EXTRACT {i}/{len(included_records)}] {r['filename']}")
            if self.provider == "anthropic":
                results.append(self.extract_by_file_id(r["file_id"], r["filename"]))
            else:
                results.append(self.extract_by_pdf_path(
                    r.get("pdf_path", ""), r["filename"]))
            if i < len(included_records):
                time.sleep(delay_seconds)
        return results
