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

CRITICAL INSTRUCTIONS:
1. Extract data for the REVIEW'S outcome above, not whichever outcome the paper calls "primary."
2. Set outcome_match true if the outcome or a closely related pain measure is found, false if not.
3. Search ALL tables, figures captions, and results paragraphs for means, SDs, and group n values.
4. n_intervention and n_control are the number of participants per arm — look in participant flow,
   Table 1, or the results section. Do NOT leave these null if sample size is mentioned anywhere.
5. mean_intervention/mean_control are post-intervention scores (or change scores if post not given).
6. If only change-from-baseline scores are reported, use those as mean_intervention/mean_control.
7. Return null ONLY if the value is genuinely absent from the text.
Return ONLY valid JSON matching this schema:

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
    def __init__(self, pico_criteria: Optional[dict] = None,
                 pico_outcome: Optional[str] = None,
                 model: str = "qwen3.7-plus",
                 provider: str = "qwen",
                 api_key: Optional[str] = None):
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
                messages=[{"role": "user", "content": [
                    {"type": "document", "source": {"type": "file", "file_id": file_id},
                     "cache_control": {"type": "ephemeral"}},
                    {"type": "text", "text": self._prompt()}
                ]}],
                betas=[BETA_HEADER])
            raw = resp.content[0].text.strip()
            from sr.src.utils.json_utils import extract_json
            r = extract_json(raw)
            r.update({"file_id": file_id, "filename": filename, "extraction_error": None})
            return r
        except Exception as e:
            return {"file_id": file_id, "filename": filename, "extraction_error": str(e)}

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

    def _call_with_text(self, pdf_text: str, prompt: str) -> str:
        """Send PDF text as plain string via OpenAI-compatible API."""
        full = f"{prompt}\n\n--- ARTICLE TEXT ---\n{pdf_text}\n--- END ---"
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": full}],
            max_tokens=4096,
            extra_body={"enable_thinking": False},
        )
        content = resp.choices[0].message.content
        if not content or not content.strip():
            raise ValueError("Empty response from model")
        return content.strip()

    def extract_by_pdf_path(self, pdf_path: str, filename="") -> dict:
        """Text-based extraction using pdfplumber with pymupdf+OCR fallback."""
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

            # --- Attempt 2: pymupdf direct text (handles CID fonts better) ---
            if not pdf_text or "(cid:" in pdf_text or pdf_text.count(" ") < 20:
                logger.info(f"pdfplumber garbled for {filename} — trying pymupdf")
                try:
                    import fitz
                    doc = fitz.open(pdf_path)
                    total_pages = len(doc)
                    if total_pages <= 6:
                        selected = list(range(total_pages))
                    else:
                        selected = list(range(3)) + list(range(3, total_pages))[:9]
                    mupdf_chunks = []
                    for i in selected:
                        t = doc[i].get_text().strip()
                        if t and len(t.split()) > 10:
                            mupdf_chunks.append(t[:1500])
                    candidate = "\n\n".join(mupdf_chunks).strip()
                    if candidate and candidate.count(" ") >= 20 and "\x00" not in candidate:
                        pdf_text = candidate
                        logger.info(
                            f"pymupdf extracted {len(pdf_text)} chars "
                            f"from {filename}")
                except Exception as mupdf_err:
                    logger.warning(f"pymupdf failed for {filename}: {mupdf_err}")

            # --- Attempt 3: OCR fallback (last resort) ---
            if not pdf_text or "(cid:" in pdf_text or pdf_text.count(" ") < 20:
                logger.info(f"Garbled text detected for {filename} — switching to OCR")
                try:
                    import fitz
                    import pytesseract
                    import io
                    from PIL import Image
                    pytesseract.pytesseract.tesseract_cmd = (
                        r"C:\Program Files\Tesseract-OCR\tesseract.exe"
                    )
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
            if len(pdf_text) > 14000:
                pdf_text = pdf_text[:14000] + "\n...[truncated]"

            if not pdf_text:
                pdf_text = f"[Could not extract text from {filename}]"
            if len(pdf_text) > 14000:
                pdf_text = pdf_text[:14000] + "\n...[truncated]"

            raw = self._call_with_text(pdf_text, self._prompt())
            from sr.src.utils.json_utils import extract_json
            r = extract_json(raw)
            r.update({"file_id": None, "filename": filename, "extraction_error": None})
            return r
        except Exception as e:
            logger.error(f"Extraction failed {filename}: {e}")
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
