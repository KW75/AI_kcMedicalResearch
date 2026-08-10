# SOURCE_CODE/pipelines/sr/src/extraction/data_extractor.py
import json, logging, os, time
import base64
import io
import re
from typing import Optional
from PIL import Image
import anthropic
import fitz

logger = logging.getLogger(__name__)
BETA_HEADER = "files-api-2025-04-14"


EXTRACTION_PROMPT_TEMPLATE = '''You are a clinical data extractor for a systematic review.

THE REVIEW'S SPECIFIED PRIMARY OUTCOME IS:
  {outcome}

REVIEW PICO CONTEXT:
  POPULATION:   {population}
  INTERVENTION: {intervention}
  COMPARATOR:   {comparator}

CRITICAL: Extract data for the REVIEW'S outcome above.

PRIORITIZE THESE OUTCOMES IN THIS ORDER:
1. Pain intensity (VAS, NRS, MPQ, FIQ pain, pain severity)
2. If pain intensity not available, extract the closest pain-related outcome
3. Do NOT extract sleep outcomes (PSQI, ISI) unless no pain data exists

Return the data in this exact nested JSON structure:

{{
  "study_metadata": {{
    "first_author": null,
    "year": null,
    "journal": null,
    "doi": null
  }},
  "participants": {{
    "n_intervention": null,
    "n_control": null
  }},
  "primary_outcome": {{
    "outcome_match": true,
    "match_rationale": "brief explanation",
    "mean_intervention": null,
    "sd_intervention": null,
    "mean_control": null,
    "sd_control": null
  }}
}}

If you find pain-related outcome data, fill in the numeric values. If not, set outcome_match to false.

DO NOT fabricate values. Return null if not found.
'''

class DataExtractor:
    def __init__(self, pico_criteria: Optional[dict] = None,
                 pico_outcome: Optional[str] = None,
                 model: str = "qwen-vl-plus",
                 provider: str = "qwen",
                 api_key: Optional[str] = None):
        self.provider = provider.lower()
        self.model = model
        self.pico = pico_criteria or {}
        self.outcome = pico_outcome or self.pico.get("outcome")

        # --- Vision support check ---
        # Only these providers support vision API
        vision_providers = ["qwen", "openai", "anthropic", "groq"]
        if self.provider not in vision_providers:
            raise ValueError(
                f"❌ Provider '{self.provider}' does NOT support vision API.\n"
                "The SR pipeline requires vision-based extraction (images of PDF pages).\n\n"
                "Supported providers for SR mode:\n"
                "  • qwen     (recommended) - Qwen vision model\n"
                "  • openai   - GPT-4 vision\n"
                "  • anthropic - Claude vision\n"
                "  • groq     - Vision models available\n\n"
                "Please use one of the supported providers:\n"
                "  python src/main.py --mode sr --provider qwen"
            )

        if not self.outcome:
            logger.warning("DataExtractor: no review outcome specified")

        if self.provider == "anthropic":
            self.client = anthropic.Anthropic(
                api_key=api_key or os.environ["ANTHROPIC_API_KEY"])
        else:
            from openai import OpenAI
            from ..screening.rob2_tool import _openai_compat_creds
            _key, _base = _openai_compat_creds(self.provider, api_key)
            self.client = OpenAI(api_key=_key, base_url=_base)

    def _prompt(self) -> str:
        return EXTRACTION_PROMPT_TEMPLATE.format(
            outcome=self.outcome or "(not specified)",
            population=self.pico.get("population", "(not specified)"),
            intervention=self.pico.get("intervention", "(not specified)"),
            comparator=self.pico.get("comparator", "(not specified)")
        )

    def _score_page(self, page_num: int, total_pages: int, text: str) -> int:
        """Score a page based on medical research indicators and position"""
        score = 0
        text_lower = text.lower()
        
        # Comprehensive medical outcome indicators
        indicators = {
            # Pain outcomes
            'pain': 4, 'vas': 5, 'nrs': 5, 'fiq': 5, 'mpq': 5, 'bpi': 5,
            'psqi': 5, 'pain intensity': 5, 'pain severity': 5,
            'visual analog': 4, 'numerical rating': 4, 'mcgill': 5,
            
            # Quality of Life
            'qol': 5, 'quality of life': 5, 'eq-5d': 5, 'sf-36': 5,
            'sf-12': 5, 'whoqol': 5, 'hrqol': 5,
            
            # Clinical outcomes
            'mortality': 5, 'death': 5, 'survival': 4, 'complication': 4,
            'adverse event': 4, 'readmission': 5, 'rehospitalization': 5,
            'admission rate': 5, 'complication rate': 5,
            'infection': 4, 'bleeding': 4, 'stroke': 4,
            
            # Functional outcomes
            'adl': 4, 'iadl': 4, 'functional': 3, 'disability': 3,
            'physical function': 4, 'mobility': 3,
            
            # Laboratory/Physiological
            'hba1c': 5, 'glucose': 4, 'blood pressure': 4,
            'cholesterol': 4, 'bmi': 4, 'weight': 4,
            
            # Mental Health
            'depression': 4, 'anxiety': 4, 'hads': 5, 'bdi': 5,
            'gad': 5, 'phq': 5, 'phq-9': 5,
            
            # Sleep
            'sleep quality': 5, 'insomnia': 5, 'isi': 5,
            'sleep disturbance': 4,
            
            # Statistical/Table indicators
            'mean': 3, 'sd': 3, 'standard deviation': 3,
            'median': 2, 'iqr': 2, 'p value': 3,
            'confidence interval': 3, 'ci': 3,
            'effect size': 3, 'odds ratio': 3,
            
            # Group indicators
            'intervention': 4, 'control': 4, 'treatment': 3,
            'placebo': 4, 'usual care': 4,
            
            # Table indicators
            'table': 5, 'figure': 3, 'tab.': 4, 'table ': 5,
            'fig.': 3, 'figure ': 3
        }
        
        for term, weight in indicators.items():
            if term in text_lower:
                score += weight
        
        # Bonus for multiple numbers in a row (table-like)
        number_rows = len(re.findall(r'\d+\.?\d*\s+\d+\.?\d*\s+\d+\.?\d*', text))
        if number_rows > 0:
            score += min(number_rows, 10)
        
        # Bonus for column-like structure (multiple groups)
        group_patterns = ['intervention', 'control', 'cbt', 'umc', 'placebo', 'waitlist']
        found_groups = sum(1 for p in group_patterns if p in text_lower)
        if found_groups >= 2:
            score += 5
        
        # Bonus for pages with table + mean/sd or pain + mean/sd
        if 'table' in text_lower and ('mean' in text_lower or 'sd' in text_lower):
            score += 15
        
        if 'pain' in text_lower and ('mean' in text_lower or 'sd' in text_lower):
            score += 15
               
        # Position bias: favor pages in the middle-to-end of the paper
        position_ratio = page_num / max(total_pages, 1)
        
        if 0.3 <= position_ratio <= 0.8:
            score += 8
        elif 0.8 < position_ratio <= 0.95:
            score += 5
        elif position_ratio > 0.95:
            score -= 5
        
        # Penalize first 2 pages (abstract/introduction)
        if page_num < 2:
            score -= 10
        
        return score

    def _get_page_images(self, pdf_path: str, filename: str) -> list:
        """Convert PDF pages to base64 images with smart page selection"""
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        
        # Score each page
        page_scores = []
        for page_num in range(total_pages):
            page = doc[page_num]
            text = page.get_text()
            score = self._score_page(page_num, total_pages, text)
            page_scores.append((page_num, score))
        
        # Sort by score (highest first)
        page_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Select pages
        selected = []
        
        # Get top scoring pages
        if page_scores and page_scores[0][1] > 5:
            # Get top 5 scoring pages
            top_pages = [p[0] for p in page_scores[:5]]
            
            # Add context pages around them
            context_pages = set()
            for p in top_pages:
                for offset in [-2, -1, 0, 1, 2]:
                    if 0 <= p + offset < total_pages:
                        context_pages.add(p + offset)
            
            selected = sorted(context_pages)[:10]
            
            # Ensure we have at least 4 pages
            if len(selected) < 4:
                for p in page_scores[:8]:
                    if p[0] not in selected:
                        selected.append(p[0])
                        if len(selected) >= 8:
                            break
                selected = sorted(selected)
        
        # Fallback if no good pages found
        if not selected:
            if total_pages <= 8:
                selected = list(range(total_pages))
            else:
                pages = set()
                pages.update(range(min(3, total_pages)))
                pages.update(range(max(0, total_pages - 4), total_pages))
                if total_pages > 10:
                    mid = total_pages // 2
                    pages.update([mid - 1, mid, mid + 1])
                selected = sorted(pages)[:10]
        
        logger.info(f"[VISION] Selected {len(selected)} pages (out of {total_pages}) for {filename}")
        logger.info(f"[VISION] Page scores: {[(p+1, s) for p, s in page_scores[:5] if s > 0]}")
        
        # Convert selected pages to images
        base64_images = []
        for page_num in selected:
            if page_num < total_pages:
                pix = doc[page_num].get_pixmap(matrix=fitz.Matrix(2, 2))
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                buffered = io.BytesIO()
                img.save(buffered, format="PNG")
                img_base64 = base64.b64encode(buffered.getvalue()).decode()
                base64_images.append(img_base64)
        
        return base64_images

    def _get_page_images_smart(self, pdf_path: str, filename: str) -> list:
        """Original smart page selection"""
        return self._get_page_images(pdf_path, filename)

    def _get_page_images_expanded(self, pdf_path: str, filename: str) -> list:
        """Expanded page selection - more pages, wider context"""
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        
        if total_pages <= 10:
            return self._pages_to_images(doc, list(range(total_pages)))
        
        pages = set()
        pages.update(range(min(4, total_pages)))
        pages.update(range(max(0, total_pages - 6), total_pages))
        
        if total_pages > 12:
            step = max(1, (total_pages - 10) // 8)
            for i in range(4, total_pages - 6, step):
                pages.add(i)
        
        selected = sorted(pages)[:12]
        
        logger.info(f"[VISION] Expanded selection: {len(selected)} pages")
        return self._pages_to_images(doc, selected)
    
    def _get_page_images_results(self, pdf_path: str, filename: str) -> list:
        """Focus on results section - middle to end of paper"""
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        
        if total_pages <= 8:
            return self._pages_to_images(doc, list(range(total_pages)))
        
        start = int(total_pages * 0.3)
        end = int(total_pages * 0.8)
        
        if end - start < 4:
            start = max(0, start - 2)
            end = min(total_pages, end + 2)
        
        pages = list(range(start, end))
        pages.extend(range(max(0, total_pages - 3), total_pages))
        
        selected = sorted(set(pages))[:10]
        
        logger.info(f"[VISION] Results section: pages {[p+1 for p in selected]}")
        return self._pages_to_images(doc, selected)
    
    def _get_page_images_full(self, pdf_path: str, filename: str) -> list:
        """Sample pages across the entire document"""
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        
        if total_pages <= 12:
            return self._pages_to_images(doc, list(range(total_pages)))
        
        step = max(1, total_pages // 10)
        pages = list(range(0, total_pages, step))[:10]
        pages.extend([0, 1, 2])
        pages.extend([total_pages - 3, total_pages - 2, total_pages - 1])
        
        selected = sorted(set(pages))[:12]
        
        logger.info(f"[VISION] Full document sample: {[p+1 for p in selected]}")
        return self._pages_to_images(doc, selected)
    
    def _pages_to_images(self, doc, pages: list) -> list:
        """Convert page numbers to base64 images"""
        base64_images = []
        for page_num in pages:
            if page_num < len(doc):
                pix = doc[page_num].get_pixmap(matrix=fitz.Matrix(2, 2))
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                buffered = io.BytesIO()
                img.save(buffered, format="PNG")
                img_base64 = base64.b64encode(buffered.getvalue()).decode()
                base64_images.append(img_base64)
        
        return base64_images

    def _call_vision_api(self, base64_images: list, prompt: str) -> str:
        """Send images to vision API (Qwen, OpenAI, etc.)"""
        
        # --- Vision support check ---
        if self.provider not in ["qwen", "openai", "anthropic", "groq"]:
            raise RuntimeError(
                f"❌ Provider '{self.provider}' does NOT support vision API.\n"
                "Please use --provider qwen (recommended), openai, anthropic, or groq."
            )
        
        content = [{"type": "text", "text": prompt}]
        for img in base64_images[:5]:  # Max 5 pages
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{img}"}
            })

        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": content}],
            max_tokens=4096,
            temperature=0.1,
        )

        return resp.choices[0].message.content.strip()

    def extract_by_pdf_path(self, pdf_path: str, filename="") -> dict:
        """Extract data using vision API with fallback page selection"""
        try:
            logger.info(f"[VISION] Extracting from {filename}")

            # Define page selection strategies
            strategies = [
                ("smart", self._get_page_images_smart),
                ("expanded", self._get_page_images_expanded),
                ("results", self._get_page_images_results),
                ("full", self._get_page_images_full),
            ]
            
            result = None
            raw_response = None
            
            for strategy_name, strategy_func in strategies:
                logger.info(f"[VISION] Trying {strategy_name} strategy for {filename}")
                
                base64_images = strategy_func(pdf_path, filename)
                
                if not base64_images:
                    logger.warning(f"[VISION] No images from {strategy_name} strategy")
                    continue
                
                raw = self._call_vision_api(base64_images, self._prompt())
                raw_response = raw
                
                # Use relative import
                from ..utils.json_utils import extract_json
                r = extract_json(raw)
                
                if r and isinstance(r, dict):
                    has_mean = (r.get('mean_intervention') or 
                               r.get('primary_outcome', {}).get('mean_intervention'))
                    has_match = (r.get('outcome_match') or 
                                r.get('primary_outcome', {}).get('outcome_match'))
                    
                    if has_mean or has_match:
                        logger.info(f"[VISION] {strategy_name} strategy found data for {filename}")
                        result = r
                        break
                    else:
                        logger.info(f"[VISION] {strategy_name} strategy found no data, trying next")
                else:
                    logger.info(f"[VISION] {strategy_name} strategy returned invalid result")
            
            if not result:
                logger.warning(f"[VISION] All strategies failed for {filename}")
                return {
                    "file_id": None,
                    "filename": filename,
                    "extraction_error": "No data found with any page selection strategy"
                }
            
            # Re-structure data to nested format expected by meta-analysis
            if 'mean_intervention' in result or 'n_intervention' in result:
                primary_outcome = {}
                participants = {}
                
                for key in ['mean_intervention', 'sd_intervention', 'mean_control', 'sd_control', 
                           'outcome_match', 'match_rationale', 'name', 'time_point']:
                    if key in result and result[key] is not None:
                        primary_outcome[key] = result[key]
                
                for key in ['n_intervention', 'n_control']:
                    if key in result and result[key] is not None:
                        participants[key] = result[key]
                
                if primary_outcome:
                    result['primary_outcome'] = primary_outcome
                if participants:
                    result['participants'] = participants
                
                flat_keys = ['mean_intervention', 'sd_intervention', 'mean_control', 'sd_control', 
                           'outcome_match', 'match_rationale', 'n_intervention', 'n_control',
                           'name', 'time_point']
                for key in flat_keys:
                    result.pop(key, None)
            
            result.update({
                "file_id": None,
                "filename": filename,
                "extraction_error": None
            })

            logger.info(f"[VISION] Extraction complete for {filename}")
            return result

        except Exception as e:
            logger.error(f"[VISION] Extraction failed {filename}: {e}")
            return {
                "file_id": None,
                "filename": filename,
                "extraction_error": str(e),
                "primary_outcome": {},
                "participants": {}
            }

    def extract_batch(self, included_records, delay_seconds=2.0) -> list[dict]:
        results = []
        for i, r in enumerate(included_records, 1):
            logger.info(f"[EXTRACT {i}/{len(included_records)}] {r['filename']}")

            if self.provider == "anthropic":
                results.append(self._extract_anthropic(r["file_id"], r["filename"]))
            else:
                results.append(self.extract_by_pdf_path(
                    r.get("pdf_path", ""), r["filename"]))

            if i < len(included_records):
                time.sleep(delay_seconds)

        return results

    def _extract_anthropic(self, file_id, filename):
        """Anthropic-specific extraction"""
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
            from ..utils.json_utils import extract_json
            r = extract_json(raw)
            r.update({"file_id": file_id, "filename": filename, "extraction_error": None})
            return r
        except Exception as e:
            return {"file_id": file_id, "filename": filename, "extraction_error": str(e)}