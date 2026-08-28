
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
    "outcome_selected": null,
    "timepoint_selected": null,
    "mean_intervention": null,
    "sd_intervention": null,
    "mean_control": null,
    "sd_control": null,
    "source_quote_intervention": null,
    "source_quote_control": null
  }}
}}

If you find pain-related outcome data, fill in the numeric values. If not, set outcome_match to false.

CRITICAL - SD vs SE: sd_intervention and sd_control must be STANDARD DEVIATIONS.
Do not use standard errors (SE, SEM), confidence intervals, t statistics,
F statistics, p values, or effect sizes for these fields. A standard error
is much smaller than a standard deviation for the same data (SE = SD /
sqrt(N)) and using it here will make the study's effect size look several
times larger than it really is. If the source reports "SE" or "SEM" next
to a value, do not put that value in sd_intervention or sd_control - either
find the actual SD elsewhere in the paper, or leave the field null.

CRITICAL - SOURCE QUOTES: for each arm, source_quote_intervention /
source_quote_control must be a VERBATIM copy of the sentence or table
row the mean and SD were read from - including any SD/SE label and any
timepoint words (baseline, post-treatment, week N) that appear around
the numbers. Copy exactly; do not paraphrase, translate, or clean up.
Both fields may hold the same quote if one row reports both arms. Set
null if you cannot point to the exact source text. These quotes are
how a human reviewer audits every number you extract.

CRITICAL - OUTCOME AND TIMEPOINT SELECTION: if the paper reports more than
one outcome that could satisfy the review's primary outcome, set
outcome_selected to the exact name of the one you extracted (e.g. "FIQ
pain score", "VAS pain intensity", "NFR threshold"). If the paper reports
the outcome at more than one timepoint (baseline, post-treatment,
follow-up, week 12, ...), set timepoint_selected to the one your numbers
come from. These two fields document WHICH row of the paper's results was
chosen - without them, two runs that pick different outcomes or timepoints
produce different effect sizes with no way to tell why. Leave null only
if the paper reports exactly one outcome at exactly one timepoint.

DO NOT fabricate values. Return null if not found.
'''

# Top-level trip conditions in DataExtractor._flag_suspect_source_quotes.
# REVIEWER_GUIDE.md §2.2 numbers these 1-5; tests/test_source_quote_doc_sync.py
# asserts the count matches so the doc can't drift. Branch 4 carries three
# mutually exclusive sub-checks (multi-timepoint / within-subject / #64 tabular).
SOURCE_QUOTE_WARNING_BRANCHES = (
    "missing_quote",
    "number_not_in_quote",
    "se_label_in_sd_quote",
    "timepoint_confusion",
    "verbatim_mismatch",
)

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
                f" - Provider '{self.provider}' does NOT support vision API.\n"
                "The SR pipeline requires vision-based extraction (images of PDF pages).\n\n"
                "Supported providers for SR mode:\n"
                "   - qwen     (recommended) - Qwen vision model\n"
                "   - openai   - GPT-4 vision\n"
                "   - anthropic - Claude vision\n"
                "   - groq     - Vision models available\n\n"
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


    @staticmethod
    def _value_present(value) -> bool:
        """Return True for meaningful JSON values; numeric zero is meaningful."""
        if isinstance(value, bool):
            return value
        return value is not None and value != "" and value != [] and value != {}

    def _first_present(self, source: dict, keys: list):
        """Return the first present value from source for any key in keys."""
        if not isinstance(source, dict):
            return None
        for key in keys:
            value = source.get(key)
            if self._value_present(value):
                return value
        return None

    def _coerce_extraction_result(self, result):
        """
        Normalize common model-output variants into the flat schema that the
        existing SR extraction/re-structure code already understands.
        """
        if not isinstance(result, dict):
            return result

        aliases = {
            "mean_intervention": ["intervention_mean", "treatment_mean", "experimental_mean"],
            "sd_intervention": ["intervention_sd", "treatment_sd", "experimental_sd"],
            "n_intervention": ["intervention_n", "treatment_n", "experimental_n"],
            "mean_control": ["control_mean", "comparator_mean"],
            "sd_control": ["control_sd", "comparator_sd"],
            "n_control": ["control_n", "comparator_n"],
            "outcome_match": ["matched_outcome"],
            # no alternate names; listed so the nested-primary copy loop
            # carries the #48 source quotes to the top level, from where
            # the restructure step rebuilds primary_outcome
            "source_quote_intervention": [],
            "source_quote_control": [],
            # #63: outcome-selection and timepoint-picking provenance.
            "outcome_selected": ["outcome_name", "selected_outcome"],
            "timepoint_selected": ["timepoint", "selected_timepoint",
                                    "assessment_timepoint"],
        }

        # Handle outputs shaped like:
        # {"best_meta_analysis_candidate": {"intervention_mean": ..., ...}}
        candidate = result.get("best_meta_analysis_candidate")
        if isinstance(candidate, dict):
            candidate_map = {
                "mean_intervention": "intervention_mean",
                "sd_intervention": "intervention_sd",
                "n_intervention": "intervention_n",
                "mean_control": "control_mean",
                "sd_control": "control_sd",
                "n_control": "control_n",
            }

            copied_numeric = False
            for dest, src in candidate_map.items():
                value = candidate.get(src)
                if not self._value_present(result.get(dest)) and self._value_present(value):
                    result[dest] = value
                    copied_numeric = True

            for dest in ["outcome_name", "timepoint", "intervention_group", "control_group"]:
                value = candidate.get(dest)
                if not self._value_present(result.get(dest)) and self._value_present(value):
                    result[dest] = value

            if copied_numeric and not self._value_present(result.get("outcome_match")):
                bits = [
                    str(candidate.get("outcome_name") or "").strip(),
                    str(candidate.get("timepoint") or "").strip(),
                ]
                result["outcome_match"] = " | ".join([b for b in bits if b]) or True

        # Copy alternate top-level names to canonical names.
        for dest, source_keys in aliases.items():
            if not self._value_present(result.get(dest)):
                value = self._first_present(result, source_keys)
                if self._value_present(value):
                    result[dest] = value

        # Copy nested primary_outcome values to top-level canonical names when needed.
        primary = result.get("primary_outcome")
        if isinstance(primary, dict):
            for dest, source_keys in aliases.items():
                if not self._value_present(result.get(dest)):
                    value = self._first_present(primary, [dest] + source_keys)
                    if self._value_present(value):
                        result[dest] = value

        self._derive_missing_sample_sizes(result)
        self._flag_group_timepoint_confusion(result)
        return result

    # Vocabulary that identifies a study TIMEPOINT, not a treatment arm.
    _TIMEPOINT_VOCAB_PATTERN = re.compile(
        r"\b("
        r"baseline|pre[-\s]?treatment|pre[-\s]?test|pre[-\s]?intervention|"
        r"post[-\s]?treatment|post[-\s]?test|post[-\s]?intervention|"
        r"follow[-\s]?up|endpoint|end[-\s]?of[-\s]?treatment|"
        r"week\s*\d+|month\s*\d+|day\s*\d+|"
        r"t\d\b|wk\d+"
        r")\b",
        re.IGNORECASE,
    )

    def _flag_group_timepoint_confusion(self, result: dict) -> None:
        """Deterministic tripwire for Known Issue #10."""
        if not isinstance(result, dict):
            return

        candidate = result.get("best_meta_analysis_candidate")
        candidate = candidate if isinstance(candidate, dict) else {}
        primary = result.get("primary_outcome")
        primary = primary if isinstance(primary, dict) else {}
        sources = [result, candidate, primary]

        intervention_group = self._clean_group_label(self._first_from_sources(
            sources, ["intervention_group", "treatment_group", "experimental_group"]))
        control_group = self._clean_group_label(self._first_from_sources(
            sources, ["control_group", "comparator_group"]))

        warning = None

        for label, value in (("intervention_group", intervention_group),
                              ("control_group", control_group)):
            if not value:
                continue
            if self._TIMEPOINT_VOCAB_PATTERN.search(str(value)):
                warning = (
                    f"{label}={value!r} looks like a timepoint label "
                    f"(baseline/post-treatment/follow-up/etc.), not a "
                    f"treatment arm name. If the source paper is reporting "
                    f"a within-subject pre/post comparison rather than a "
                    f"between-group comparison, this is NOT a valid effect "
                    f"size for this meta-analysis."
                )
                break

        if warning is None and intervention_group and control_group:
            if self._normalize_label(intervention_group) == self._normalize_label(control_group):
                warning = (
                    f"intervention_group and control_group are both "
                    f"{intervention_group!r} - the same group cannot be "
                    f"its own comparator. This looks like a within-subject "
                    f"(pre/post) contrast mislabeled as a between-group "
                    f"comparison."
                )

        result["group_timepoint_warning"] = warning
        if warning:
            logger.warning(
                "[GROUP/TIMEPOINT CHECK] Possible within/between-group "
                "confusion for %s: %s",
                result.get("filename", "?"), warning,
            )

    def _has_usable_extraction_result(self, result: dict) -> bool:
        """Mirror the existing acceptance gate, but handle zero values safely."""
        if not isinstance(result, dict):
            return False

        primary = result.get("primary_outcome")
        if not isinstance(primary, dict):
            primary = {}

        mean_intervention = self._first_present(
            result,
            ["mean_intervention", "intervention_mean", "treatment_mean"],
        )
        if not self._value_present(mean_intervention):
            mean_intervention = self._first_present(
                primary,
                ["mean_intervention", "intervention_mean", "treatment_mean"],
            )

        outcome_match = self._first_present(result, ["outcome_match", "matched_outcome"])
        if not self._value_present(outcome_match):
            outcome_match = self._first_present(primary, ["outcome_match", "matched_outcome"])

        return self._value_present(mean_intervention) or self._value_present(outcome_match)


    _LABEL_SENTINELS = {
        "null", "none", "n/a", "na", "nan", "not reported",
        "not stated", "not specified", "unknown", "unclear", "-", "",
    }

    @classmethod
    def _clean_group_label(cls, value):
        """Return the label, or None if it is a decline-sentinel."""
        if value is None:
            return None
        text = str(value).strip()
        if text.lower() in cls._LABEL_SENTINELS:
            return None
        return value

    @staticmethod
    def _normalize_label(value) -> str:
        """Normalize group/timepoint labels for fuzzy matching."""
        import re
        return re.sub(r"[^a-z0-9]+", "", str(value or "").lower())

    @staticmethod
    def _coerce_int(value):
        """Convert model-provided N values to int when safe."""
        if value is None or value == "":
            return None
        try:
            return int(float(str(value).strip()))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _coerce_float(value):
        """Convert model-provided numeric values to float when safe."""
        if value is None or value == "":
            return None
        try:
            return float(str(value).replace("?", "-").strip())
        except (TypeError, ValueError):
            return None

    def _numbers_close(self, left, right, tolerance: float = 1e-6) -> bool:
        """Compare model numeric values after safe float coercion."""
        left_float = self._coerce_float(left)
        right_float = self._coerce_float(right)
        if left_float is None or right_float is None:
            return False
        return abs(left_float - right_float) <= tolerance

    def _sample_size_key_order(self, timepoint) -> list:
        """Return likely sample-size keys for a named timepoint."""
        label = self._normalize_label(timepoint)

        if "follow" in label:
            return [
                "follow_up_n", "followup_n", "follow_up", "followup",
                "n_followup", "n_follow_up", "n_follow-up", "follow-up_n",
                "t3_n", "n_t3",
            ]

        if "post" in label or "end" in label:
            return [
                "post_n", "posttreatment_n", "post_intervention_n",
                "postintervention_n", "n_post", "n_post_treatment",
                "n_post_intervention", "t2_n", "n_t2",
            ]

        if "pre" in label or "baseline" in label:
            return [
                "pre_n", "pretreatment_n", "baseline_n",
                "n_pre", "n_pre_treatment", "n_baseline",
                "t1_n", "n_t1",
            ]

        return [
            "post_n", "n_post", "post_intervention_n", "n_post_intervention",
            "follow_up_n", "followup_n", "n_followup", "n_follow_up",
            "pre_n", "n_pre", "baseline_n", "n_baseline", "n",
        ]

    def _get_sample_size_for_group(self, result: dict, group, timepoint):
        """Find N for a group/timepoint from model-provided sample-size rows."""
        if not isinstance(result, dict) or not group:
            return None

        rows = (
            result.get("groups_n_by_timepoint")
            or result.get("sample_sizes")
            or result.get("group_sample_sizes")
            or []
        )
        if not isinstance(rows, list):
            return None

        target = self._normalize_label(group)
        keys = self._sample_size_key_order(timepoint)

        for row in rows:
            if not isinstance(row, dict):
                continue

            row_group = (
                row.get("group")
                or row.get("arm")
                or row.get("name")
                or row.get("label")
            )
            row_label = self._normalize_label(row_group)

            if not row_label:
                continue

            if not (row_label == target or row_label in target or target in row_label):
                continue

            value = self._first_present(row, keys)
            n_value = self._coerce_int(value)
            if n_value is not None:
                return n_value

        return None

    def _first_from_sources(self, sources: list, keys: list):
        """Return first present value from a list of dictionaries."""
        for source in sources:
            value = self._first_present(source, keys)
            if self._value_present(value):
                return value
        return None

    def _infer_group_timepoint_from_outcomes(self, result: dict, mean_value, sd_value):
        """Infer group/timepoint by matching extracted mean/SD against outcome tables."""
        outcomes = result.get("outcomes") if isinstance(result, dict) else None
        if not isinstance(outcomes, list):
            return None, None

        time_specs = [
            ("pre-treatment", ["pre_mean", "baseline_mean"], ["pre_sd", "baseline_sd"]),
            ("post-treatment", ["post_mean", "post_treatment_mean", "post_intervention_mean"], ["post_sd", "post_treatment_sd", "post_intervention_sd"]),
            ("follow-up", ["follow_up_mean", "followup_mean", "follow-up_mean"], ["follow_up_sd", "followup_sd", "follow-up_sd"]),
        ]

        for outcome in outcomes:
            if not isinstance(outcome, dict):
                continue

            groups = outcome.get("groups")
            if not isinstance(groups, list):
                continue

            for group_row in groups:
                if not isinstance(group_row, dict):
                    continue

                group_name = group_row.get("group") or group_row.get("arm")
                for timepoint, mean_keys, sd_keys in time_specs:
                    candidate_mean = self._first_present(group_row, mean_keys)
                    candidate_sd = self._first_present(group_row, sd_keys)

                    if (
                        self._numbers_close(mean_value, candidate_mean)
                        and self._numbers_close(sd_value, candidate_sd)
                    ):
                        return group_name, timepoint

        return None, None

    def _derive_missing_sample_sizes(self, result: dict) -> dict:
        """Fill missing n_intervention/n_control from common model output shapes."""
        if not isinstance(result, dict):
            return result

        candidate = result.get("best_meta_analysis_candidate")
        if not isinstance(candidate, dict):
            candidate = {}

        primary = result.get("primary_outcome")
        if not isinstance(primary, dict):
            primary = {}

        common_sources = [result, candidate, primary]

        timepoint = self._first_from_sources(
            common_sources,
            ["timepoint", "assessment_timepoint", "selected_timepoint"],
        )

        side_specs = [
            (
                "intervention",
                "n_intervention",
                "intervention_n",
                ["intervention_group", "treatment_group", "experimental_group"],
                ["mean_intervention", "intervention_mean", "treatment_mean", "experimental_mean"],
                ["sd_intervention", "intervention_sd", "treatment_sd", "experimental_sd"],
            ),
            (
                "control",
                "n_control",
                "control_n",
                ["control_group", "comparator_group"],
                ["mean_control", "control_mean", "comparator_mean"],
                ["sd_control", "control_sd", "comparator_sd"],
            ),
        ]

        for side, canonical_n, candidate_n, group_keys, mean_keys, sd_keys in side_specs:
            existing_n = self._first_from_sources(common_sources, [canonical_n, candidate_n])
            if self._coerce_int(existing_n) is not None:
                continue

            group = self._first_from_sources(common_sources, group_keys)
            mean_value = self._first_from_sources(common_sources, mean_keys)
            sd_value = self._first_from_sources(common_sources, sd_keys)
            side_timepoint = timepoint

            if not group or not side_timepoint:
                inferred_group, inferred_timepoint = self._infer_group_timepoint_from_outcomes(
                    result,
                    mean_value,
                    sd_value,
                )
                group = group or inferred_group
                side_timepoint = side_timepoint or inferred_timepoint

            n_value = self._get_sample_size_for_group(result, group, side_timepoint)
            if n_value is None:
                continue

            result[canonical_n] = n_value
            if isinstance(candidate, dict):
                candidate[candidate_n] = n_value

            if group:
                result.setdefault(f"{side}_group", group)
            if side_timepoint:
                result.setdefault("timepoint", side_timepoint)

        return result

    def _sample_size_from_text_for_group(self, extracted_text: str, group, timepoint):
        """Last-resort deterministic sample-size parser for table headers."""
        import re

        if not extracted_text or not group:
            return None

        group_norm = self._normalize_label(group)
        time_norm = self._normalize_label(timepoint)

        if "follow" in time_norm:
            n_index = 2
        elif "pre" in time_norm or "baseline" in time_norm:
            n_index = 0
        else:
            n_index = 1

        for raw_line in extracted_text.splitlines():
            line = re.sub(r"^\s*\d{4}:\s*", "", raw_line).strip()
            if "n" not in line.lower():
                continue

            n_values = [int(x) for x in re.findall(r"\bn\s*=\s*(\d+)", line, flags=re.I)]
            if len(n_values) <= n_index:
                continue

            lower = line.lower()
            normalized_line = self._normalize_label(line)

            matches_group = False

            if group_norm == "cbtip":
                matches_group = (
                    "cbt-ip" in lower
                    or lower.startswith("ip ")
                    or " ip (n" in lower
                    or normalized_line.startswith("ipn")
                )
            elif group_norm == "cbtp":
                matches_group = (
                    "cbt-p" in lower
                    or ("cbt-" in lower and "ip" not in lower)
                    or "cbtp" in normalized_line
                )
            elif group_norm == "umc":
                matches_group = "umc" in lower
            else:
                matches_group = group_norm in normalized_line

            if matches_group:
                return n_values[n_index]

        return None


    def _collect_candidate_group_names(self, result: dict) -> list:
        """Gather candidate arm names from extraction output."""
        if not isinstance(result, dict):
            return []

        candidate = result.get("best_meta_analysis_candidate")
        candidate = candidate if isinstance(candidate, dict) else {}
        primary = result.get("primary_outcome")
        primary = primary if isinstance(primary, dict) else {}
        sources = [result, candidate, primary]

        names = []

        for key in ("intervention_group", "treatment_group", "experimental_group",
                    "control_group", "comparator_group"):
            value = self._first_from_sources(sources, [key])
            if self._value_present(value):
                names.append(str(value).strip())

        rows = (
            result.get("groups_n_by_timepoint")
            or result.get("sample_sizes")
            or result.get("group_sample_sizes")
            or []
        )
        if isinstance(rows, list):
            for row in rows:
                if not isinstance(row, dict):
                    continue
                value = row.get("group") or row.get("arm") or row.get("name") or row.get("label")
                if self._value_present(value):
                    names.append(str(value).strip())

        seen = set()
        deduped = []
        for name in names:
            if name and name not in seen:
                seen.add(name)
                deduped.append(name)
        return deduped

    def _infer_group_timepoint_from_text(self, extracted_text: str, mean_value, sd_value,
                                          candidate_groups: list = None) -> tuple:
        """Infer group/timepoint from compacted table text rows."""
        import re

        if not extracted_text or not candidate_groups:
            return None, None

        timepoints = ["pre-treatment", "post-treatment", "follow-up"]

        for raw_line in extracted_text.splitlines():
            line = re.sub(r"^\s*\d{4}:\s*", "", raw_line).strip()
            if not line:
                continue

            pairs = re.findall(
                r"(?<![\w.])([-?]?\d+(?:\.\d+)?)\s*\(\s*([-?]?\d+(?:\.\d+)?)\s*\)",
                line,
            )
            if not pairs:
                continue

            group_name = None
            for candidate in candidate_groups:
                candidate = str(candidate).strip()
                if not candidate:
                    continue
                pattern = re.escape(candidate).replace(r"\-", r"[-\s]?")
                if re.search(rf"\b{pattern}\b", line, flags=re.I):
                    group_name = candidate
                    break

            if not group_name:
                continue

            for idx, (candidate_mean, candidate_sd) in enumerate(pairs[:3]):
                if (
                    self._numbers_close(mean_value, candidate_mean)
                    and self._numbers_close(sd_value, candidate_sd)
                ):
                    timepoint = timepoints[idx] if idx < len(timepoints) else None
                    return group_name, timepoint

        return None, None

    def _flag_possible_se_as_sd(self, result: dict, extracted_text: str) -> dict:
        """Deterministic tripwire for Known Issue #9 (SD/SE confusion)."""
        if not isinstance(result, dict) or not extracted_text:
            return result

        primary = result.get("primary_outcome")
        if not isinstance(primary, dict):
            primary = result

        se_pattern = re.compile(r"\b(SE|SEM|standard error)\b", re.IGNORECASE)
        warnings_found = []

        for field, label in (("sd_intervention", "intervention"), ("sd_control", "control")):
            value = primary.get(field)
            if value is None:
                continue
            value_str = str(value)
            for line in extracted_text.splitlines():
                if se_pattern.search(line) and value_str in line:
                    warnings_found.append(
                        f"{label} SD ({value}) appears on a source line "
                        f"containing 'SE'/'SEM'/'standard error' - verify "
                        f"this is really an SD, not a standard error, "
                        f"against the source PDF."
                    )
                    break

        result["sd_se_warning"] = " | ".join(warnings_found) if warnings_found else None
        if warnings_found:
            logger.warning(
                "[SD/SE CHECK] Possible SE-as-SD confusion for %s: %s",
                result.get("filename", "?"), result["sd_se_warning"],
            )

        return result


    _WITHIN_SUBJECT_PHRASES = re.compile(
        r"(relative to|compared (?:to|with)|versus|vs\.?|change[sd]? from|"
        r"improve[dment]* from|reduc\w+ from|from)\s+(?:the\s+)?"
        r"(baseline|pre[-\s]?treatment|pre[-\s]?test|pre[-\s]?intervention)",
        re.IGNORECASE,
    )
    _SE_MARKER = re.compile(r"\b(SE|SEM|standard error)\b", re.IGNORECASE)

    @staticmethod
    def _number_in_text(value, text: str) -> bool:
        """True if `value` appears in `text` as a standalone number."""
        s = str(value).strip()
        try:
            f = float(s)
        except (TypeError, ValueError):
            return s in (text or "")

        candidates = [s]
        if f == int(f):
            candidates.append(str(int(f)))

        for candidate in candidates:
            core = re.escape(candidate).replace("\\.", "[.,]")
            if "." in candidate:
                pattern = rf"(?<![\d.,]){core}0*(?!\d)"
            else:
                pattern = rf"(?<![\d.,]){core}(?:[.,]0+)?(?!\d)(?!\.\d)"
            if re.search(pattern, text or ""):
                return True
        return False


    def _flag_suspect_source_quotes(self, result: dict,
                                    source_text: str = None) -> dict:
        """Deterministic tripwire for Known Issue #48."""
        if not isinstance(result, dict):
            return result
        primary = result.get("primary_outcome")
        primary = primary if isinstance(primary, dict) else result

        warnings_found = []
        for arm in ("intervention", "control"):
            mean = primary.get(f"mean_{arm}")
            sd = primary.get(f"sd_{arm}")
            if mean is None and sd is None:
                continue
            quote = self._clean_group_label(primary.get(f"source_quote_{arm}"))
            if not quote:
                warnings_found.append(
                    f"no source quote provided for the {arm} values - the "
                    f"numbers cannot be audited against the source text")
                continue
            quote = str(quote)

            for label, value in (("mean", mean), ("SD", sd)):
                if value is not None and not self._number_in_text(value, quote):
                    warnings_found.append(
                        f"{arm} {label} ({value}) does not appear in its own "
                        f"source quote - the quote does not support this number")

            if sd is not None and self._SE_MARKER.search(quote):
                warnings_found.append(
                    f"{arm} SD ({sd}) was quoted from text containing "
                    f"'SE'/'SEM'/'standard error' - verify this is really an "
                    f"SD, not a standard error (Known Issue #9)")

            timepoints = {m.group(0).lower()
                          for m in self._TIMEPOINT_VOCAB_PATTERN.finditer(quote)}
            if len(timepoints) >= 2:
                warnings_found.append(
                    f"{arm} source quote references multiple timepoints "
                    f"({', '.join(sorted(timepoints))}) - these values may be "
                    f"a within-subject pre/post contrast, not a between-group "
                    f"comparison")
            elif self._WITHIN_SUBJECT_PHRASES.search(quote):
                warnings_found.append(
                    f"{arm} source quote uses within-subject comparison "
                    f"phrasing ({self._WITHIN_SUBJECT_PHRASES.search(quote).group(0)!r}) "
                    f"- these values may not be a between-group comparison")
            else:
                # Tabular multi-timepoint pattern (#64): a quote like
                # "CBT-P 7.58 (1.75) 7.35 (2.08) 7.21 (1.79)" carries three
                # mean(SD) cells for the same arm - almost certainly three
                # timepoints, even though no timepoint word appears. The
                # extractor picks one cell; the reviewer needs to know a
                # choice was made.
                cells = re.findall(
                    r"(?<![\w.])[-+]?\d+(?:\.\d+)?\s*\(\s*[-+]?\d+(?:\.\d+)?\s*\)",
                    quote,
                )
                if len(cells) >= 3:
                    warnings_found.append(
                        f"{arm} source quote contains {len(cells)} mean(SD) "
                        f"cells on one row - these are almost certainly "
                        f"successive timepoints (e.g. baseline / post / "
                        f"follow-up). Verify the extracted values come "
                        f"from the intended timepoint (#64)")


            if source_text:
                norm = lambda t: re.sub(r"\s+", " ", t).strip().lower()
                if norm(quote) not in norm(source_text):
                    warnings_found.append(
                        f"{arm} source quote was not found verbatim in the "
                        f"extracted source text - it may be paraphrased or "
                        f"fabricated")

        result["source_quote_warning"] = (
            " | ".join(warnings_found) if warnings_found else None)
        if warnings_found:
            logger.warning(
                "[SOURCE QUOTE CHECK] %s: %s",
                result.get("filename", "?"), result["source_quote_warning"],
            )
        return result

    def _derive_missing_sample_sizes_from_text(self, result: dict, extracted_text: str) -> dict:
        """Fill missing Ns from extracted table text when the model omits them."""
        if not isinstance(result, dict):
            return result

        candidate = result.get("best_meta_analysis_candidate")
        if not isinstance(candidate, dict):
            candidate = {}

        primary = result.get("primary_outcome")
        if not isinstance(primary, dict):
            primary = {}

        sources = [result, candidate, primary]
        timepoint = self._first_from_sources(
            sources,
            ["timepoint", "assessment_timepoint", "selected_timepoint"],
        )

        for side, canonical_n, candidate_n, group_keys in [
            ("intervention", "n_intervention", "intervention_n", ["intervention_group", "treatment_group", "experimental_group"]),
            ("control", "n_control", "control_n", ["control_group", "comparator_group"]),
        ]:
            existing_n = self._first_from_sources(sources, [canonical_n, candidate_n])
            if self._coerce_int(existing_n) is not None:
                continue

            group = self._first_from_sources(sources, group_keys)
            side_timepoint = timepoint

            if not group or not side_timepoint:
                if side == "intervention":
                    mean_keys = ["mean_intervention", "intervention_mean", "treatment_mean", "experimental_mean"]
                    sd_keys = ["sd_intervention", "intervention_sd", "treatment_sd", "experimental_sd"]
                else:
                    mean_keys = ["mean_control", "control_mean", "comparator_mean"]
                    sd_keys = ["sd_control", "control_sd", "comparator_sd"]

                mean_value = self._first_from_sources(sources, mean_keys)
                sd_value = self._first_from_sources(sources, sd_keys)

                candidate_groups = self._collect_candidate_group_names(result)
                inferred_group, inferred_timepoint = self._infer_group_timepoint_from_text(
                    extracted_text,
                    mean_value,
                    sd_value,
                    candidate_groups=candidate_groups,
                )
                group = group or inferred_group
                side_timepoint = side_timepoint or inferred_timepoint

            n_value = self._sample_size_from_text_for_group(
                extracted_text,
                group,
                side_timepoint,
            )

            if n_value is not None:
                result[canonical_n] = n_value
                if isinstance(candidate, dict):
                    candidate[candidate_n] = n_value

        return result

    @staticmethod
    def _missing_like_value(v) -> bool:
        if v is None:
            return True
        if isinstance(v, bool):
            return False
        try:
            import math
            if isinstance(v, float) and math.isnan(v):
                return True
        except Exception:
            pass
        if isinstance(v, str):
            return v.strip().lower() in {"", "none", "null", "nan", "na", "n/a", "not reported"}
        return False

    @staticmethod
    def _as_float_or_none(v):
        if v is None or isinstance(v, bool):
            return None
        try:
            if isinstance(v, str):
                v = v.strip().replace(",", "")
                if v == "":
                    return None
            return float(v)
        except Exception:
            return None

    @classmethod
    def _near(cls, v, target: float, tol: float = 0.035) -> bool:
        x = cls._as_float_or_none(v)
        return x is not None and abs(x - target) <= tol

    def _mirror_study_metadata(self, result: dict) -> None:
        """Copy resolved first_author/year into the nested study_metadata block."""
        if not isinstance(result, dict):
            return

        sm = result.get("study_metadata")
        if not isinstance(sm, dict):
            sm = {}
            result["study_metadata"] = sm

        for field in ("first_author", "year"):
            if self._missing_like_value(sm.get(field)) and not self._missing_like_value(result.get(field)):
                sm[field] = result[field]

    @property
    def _study_overrides(self):
        """Reviewer-maintained per-study corrections, loaded once."""
        cached = getattr(self, "_study_overrides_cache", None)
        if cached is None:
            from .study_overrides import StudyOverrides
            import os

            path = os.environ.get(
                "SR_STUDY_OVERRIDES",
                os.path.join("input", "sr", "study_overrides.yaml"),
            )
            cached = StudyOverrides(path)
            self._study_overrides_cache = cached
        return cached

    def _apply_known_pdf_corrections(self, result: dict, filename: str = "",
                                     pdf_path: str = "") -> dict:
        """Resolve study metadata and apply reviewer overrides."""
        if not isinstance(result, dict):
            return result

        paper = result.get("paper") if isinstance(result.get("paper"), dict) else {}

        if self._missing_like_value(result.get("first_author")):
            for key in ("first_author", "firstAuthor", "author"):
                if not self._missing_like_value(paper.get(key)):
                    result["first_author"] = paper.get(key)
                    break

        if self._missing_like_value(result.get("year")):
            for key in ("year", "publication_year", "publicationYear"):
                if not self._missing_like_value(paper.get(key)):
                    result["year"] = paper.get(key)
                    break

        needs_meta = (
            self._missing_like_value(result.get("first_author"))
            or self._missing_like_value(result.get("year"))
        )
        if needs_meta and pdf_path:
            try:
                from .study_overrides import resolve_pdf_metadata

                derived = resolve_pdf_metadata(pdf_path)
                for field in ("first_author", "year", "doi"):
                    if field in derived and self._missing_like_value(result.get(field)):
                        result[field] = derived[field]
                        result["metadata_source"] = "pdf_auto (verify)"
                        logger.info(
                            "Derived %s=%r from PDF for %s",
                            field, derived[field], filename,
                        )
            except Exception as exc:
                logger.warning("PDF metadata resolution failed for %s: %s", filename, exc)

        try:
            self._study_overrides.apply(result, filename or result.get("filename") or "")
        except Exception as exc:
            logger.warning("Study override application failed for %s: %s", filename, exc)

        self._mirror_study_metadata(result)
        return result

    def _compact_pdf_text_lines(self, raw_text: str) -> list:
        """Normalize extracted PDF text into non-empty compact lines."""
        import re

        compacted = []
        for line in (raw_text or "").splitlines():
            line = re.sub(r"\s+", " ", line.replace("\xa0", " ")).strip()
            if line:
                compacted.append(line)
        return compacted

    def _score_text_page_for_extraction(self, text: str) -> int:
        """Score a text page for likely continuous-outcome table content."""
        import re

        lower = text.lower()
        score = 0

        weighted_terms = {
            "table": 2,
            "m (sd)": 8,
            "mean": 3,
            "sd": 3,
            "pre-treatment": 4,
            "post-treatment": 4,
            "follow-up": 4,
            "follow up": 4,
            "control": 2,
            "usual medical care": 3,
            "cbt": 2,
            "intervention": 2,
            "outcome": 2,
        }

        for term, weight in weighted_terms.items():
            if term in lower:
                score += weight

        score += min(
            36,
            6 * len(re.findall(r"\b\d+(?:\.\d+)?\s*\(\s*\d+(?:\.\d+)?\s*\)", text)),
        )

        score += min(15, 3 * len(re.findall(r"\bn\s*=\s*\d+", lower)))

        return score

    def _extract_candidate_table_text(
        self,
        pdf_path: str,
        max_pages: int = 6,
        max_chars: int = 24000,
    ) -> str:
        """Extract high-signal text pages for a text fallback."""
        import fitz

        scored_pages = []
        doc = fitz.open(str(pdf_path))

        try:
            for page_index, page in enumerate(doc):
                try:
                    raw = page.get_text("text", sort=True) or ""
                except TypeError:
                    raw = page.get_text("text") or ""

                lines = self._compact_pdf_text_lines(raw)
                if not lines:
                    continue

                page_text = "\n".join(lines)
                score = self._score_text_page_for_extraction(page_text)
                if score > 0:
                    scored_pages.append((score, page_index, lines))
        finally:
            doc.close()

        if not scored_pages:
            return ""

        selected = sorted(scored_pages, key=lambda item: (-item[0], item[1]))[:max_pages]
        selected = sorted(selected, key=lambda item: item[1])

        chunks = []
        total_chars = 0

        for score, page_index, lines in selected:
            body = "\n".join(f"{line_no:04d}: {line}" for line_no, line in enumerate(lines))
            chunk = f"===== PDF PAGE {page_index + 1} | text_score={score} =====\n{body}"

            if total_chars + len(chunk) > max_chars and chunks:
                continue

            if len(chunk) > max_chars:
                chunk = chunk[:max_chars]

            chunks.append(chunk)
            total_chars += len(chunk)

            if total_chars >= max_chars:
                break

        return "\n\n".join(chunks).strip()

    def _text_extraction_prompt(self, extracted_text: str, filename: str = "") -> str:
        """Build a text-only fallback prompt while preserving the original extraction task."""
        original_prompt = self._prompt()

        return (
            "You are performing a TEXT FALLBACK extraction for a systematic-review "
            "continuous-outcome meta-analysis. Use only the extracted PDF text below. "
            "Do not infer or fabricate missing values.\n\n"
            "Follow the original extraction task and JSON schema as closely as possible. "
            "Return JSON only. No markdown.\n\n"
            "Canonical fields accepted by the pipeline include:\n"
            "{\n"
            '  "outcome_match": null,\n'
            '  "outcome_name": null,\n'
            '  "outcome_selected": null,\n'
            '  "timepoint": null,\n'
            '  "timepoint_selected": null,\n'
            '  "intervention_group": null,\n'
            '  "control_group": null,\n'
            '  "n_intervention": null,\n'
            '  "mean_intervention": null,\n'
            '  "sd_intervention": null,\n'
            '  "n_control": null,\n'
            '  "mean_control": null,\n'
            '  "sd_control": null,\n'
            '  "raw_fragment": null,\n'
            '  "source_quote_intervention": null,\n'
            '  "source_quote_control": null,\n'
            '  "warnings": []\n'
            "}\n\n"
            "When visible, also include sample-size evidence in this optional shape:\n"
            "{\n"
            '  "groups_n_by_timepoint": [\n'
            '    {"group": "group name", "pre_n": null, "post_n": null, "follow_up_n": null}\n'
            "  ],\n"
            '  "best_meta_analysis_candidate": {\n'
            '    "intervention_n": null, "control_n": null,\n'
            '    "intervention_mean": null, "intervention_sd": null,\n'
            '    "control_mean": null, "control_sd": null\n'
            "  }\n"
            "}\n\n"
            "Rules:\n"
            "- Prefer direct group mean (SD) data for intervention versus control.\n"
            "- Parenthesized values immediately after means are SDs.\n"
            "- Do not use t statistics, F statistics, p values, effect sizes, eta-squared, "
            "confidence intervals, or standard errors as SDs.\n"
            "- If multiple timepoints are available, prefer the timepoint requested by the "
            "original prompt; otherwise prefer the latest follow-up with usable data.\n"
            "- Include a raw_fragment so the extracted values can be audited.\n"
            "- source_quote_intervention / source_quote_control: VERBATIM copy of the "
            "sentence or table row each arm's mean/SD was read from, including any "
            "SD/SE label and timepoint words around the numbers. Never paraphrase; "
            "null if unsure.\n"
            "- outcome_selected / timepoint_selected: exact name of the outcome measure "
            "and timepoint your numbers come from - documents which row of the paper's "
            "results was chosen (#63).\n\n"
            f"FILENAME: {filename}\n\n"
            "ORIGINAL EXTRACTION PROMPT:\n"
            f"{original_prompt}\n\n"
            "EXTRACTED PDF TEXT:\n"
            f"{extracted_text}\n"
        )

    GROUP_LABEL_FOLLOWUP_TEMPLATE = '''You previously extracted these outcome values from this paper:
  Intervention/treatment arm: mean={mean_intervention}, SD={sd_intervention}, N={n_intervention}
  Control/comparator arm: mean={mean_control}, SD={sd_control}, N={n_control}

I need the actual NAMES of these two arms/groups, as the paper itself calls
them (e.g. "CBT", "Usual Medical Care", "Metformin 500mg", "Placebo").

Do NOT answer with a role description like "intervention" or "control" -
I already know which is which, I need what the paper actually calls them.

Do NOT answer with a timepoint (baseline, pre-treatment, post-treatment,
follow-up, Week 12, T1/T2/T3, etc.) - a timepoint is not a group name. If
the only difference you can find between these two rows of numbers is a
timepoint rather than a treatment arm, that is important - say so by
setting both fields to null rather than guessing.

Return ONLY valid JSON, no markdown:
{{"intervention_group": "<arm name exactly as the paper prints it>",
  "control_group": "<arm name exactly as the paper prints it>"}}
If you cannot find a real arm name for a field, use unquoted JSON null
for that field - NOT the quoted string "null".
'''

    def _needs_group_labels(self, result: dict) -> bool:
        """True if the result has usable outcome data but no group labels."""
        if not isinstance(result, dict):
            return False
        candidate = result.get("best_meta_analysis_candidate")
        candidate = candidate if isinstance(candidate, dict) else {}
        primary = result.get("primary_outcome")
        primary = primary if isinstance(primary, dict) else {}
        sources = [result, candidate, primary]
        intervention_group = self._clean_group_label(self._first_from_sources(
            sources, ["intervention_group", "treatment_group", "experimental_group"]))
        control_group = self._clean_group_label(self._first_from_sources(
            sources, ["control_group", "comparator_group"]))
        return not (intervention_group and control_group)

    def _build_group_label_followup_prompt(self, result: dict) -> str:
        candidate = result.get("best_meta_analysis_candidate")
        candidate = candidate if isinstance(candidate, dict) else {}
        primary = result.get("primary_outcome")
        primary = primary if isinstance(primary, dict) else {}
        sources = [result, candidate, primary]

        def get(keys):
            v = self._first_from_sources(sources, keys)
            return v if v is not None else "(not recorded)"

        return self.GROUP_LABEL_FOLLOWUP_TEMPLATE.format(
            mean_intervention=get(["mean_intervention", "intervention_mean", "treatment_mean"]),
            sd_intervention=get(["sd_intervention", "intervention_sd", "treatment_sd"]),
            n_intervention=get(["n_intervention", "intervention_n"]),
            mean_control=get(["mean_control", "control_mean", "comparator_mean"]),
            sd_control=get(["sd_control", "control_sd", "comparator_sd"]),
            n_control=get(["n_control", "control_n"]),
        )

    def _call_chat_api_with_prompt(self, prompt: str, max_tokens: int = 256) -> str:
        """Send an arbitrary text-only prompt via the OpenAI-compatible client."""
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0,
        )
        return (resp.choices[0].message.content or "").strip()

    def _fetch_group_labels_if_missing(self, result: dict, filename: str,
                                        base64_images: list = None,
                                        extracted_text: str = None) -> dict:
        """Follow-up call for missing group labels."""
        if self.provider == "anthropic":
            return result
        if not self._needs_group_labels(result):
            return result
        if not base64_images and not extracted_text:
            return result

        result.setdefault("filename", filename)

        prompt = self._build_group_label_followup_prompt(result)

        try:
            if base64_images:
                raw = self._call_vision_api(base64_images, prompt)
            else:
                raw = self._call_chat_api_with_prompt(prompt)

            from ..utils.json_utils import extract_json
            labels = extract_json(raw)
            if not isinstance(labels, dict):
                return result

            for key in ("intervention_group", "control_group"):
                value = self._clean_group_label(labels.get(key))
                if self._value_present(value):
                    result[key] = value

            logger.info(
                "[GROUP LABELS] Follow-up for %s: intervention_group=%r, control_group=%r",
                filename, result.get("intervention_group"), result.get("control_group"),
            )

        except Exception as exc:
            logger.warning(f"[GROUP LABELS] Follow-up request failed for {filename}: {exc}")

        self._flag_group_timepoint_confusion(result)
        return result

    def _call_text_api(self, extracted_text: str, filename: str = "") -> str:
        """Send extracted PDF text to the chat-completions client as a fallback."""
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": self._text_extraction_prompt(extracted_text, filename),
                }
            ],
            max_tokens=4096,
            temperature=0,
        )

        return (resp.choices[0].message.content or "").strip()

    def _call_vision_api(self, base64_images: list, prompt: str) -> str:
        """Send images to vision API."""
        if self.provider not in ["qwen", "openai", "anthropic", "groq"]:
            raise RuntimeError(
                f" - Provider '{self.provider}' does NOT support vision API.\n"
                "Please use --provider qwen (recommended), openai, anthropic, or groq."
            )

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
            temperature=0.1,
        )

        return resp.choices[0].message.content.strip()

    def extract_by_pdf_path(self, pdf_path: str, filename="") -> dict:
        """Extract data using vision API with fallback page selection"""
        try:
            logger.info(f"[VISION] Extracting from {filename}")

            strategies = [
                ("smart", self._get_page_images_smart),
                ("expanded", self._get_page_images_expanded),
                ("results", self._get_page_images_results),
                ("full", self._get_page_images_full),
            ]

            result = None
            raw_response = None
            text_payload = None

            for strategy_name, strategy_func in strategies:
                logger.info(f"[VISION] Trying {strategy_name} strategy for {filename}")

                base64_images = strategy_func(pdf_path, filename)

                if not base64_images:
                    logger.warning(f"[VISION] No images from {strategy_name} strategy")
                    continue

                raw = self._call_vision_api(base64_images, self._prompt())
                raw_response = raw

                from ..utils.json_utils import extract_json
                r = self._coerce_extraction_result(extract_json(raw))

                if r and isinstance(r, dict):
                    if self._has_usable_extraction_result(r):
                        logger.info(f"[VISION] {strategy_name} strategy found data for {filename}")
                        r = self._fetch_group_labels_if_missing(
                            r, filename, base64_images=base64_images)
                        r.setdefault("extraction_method", f"vision_{strategy_name}")
                        result = r
                        break
                    else:
                        logger.info(f"[VISION] {strategy_name} strategy found no data, trying next")
                else:
                    logger.info(f"[VISION] {strategy_name} strategy returned invalid result")

            if not result:
                try:
                    text_payload = self._extract_candidate_table_text(pdf_path)
                    if text_payload:
                        logger.info(
                            f"[TEXT] Trying text fallback for {filename} "
                            f"({len(text_payload)} chars)"
                        )

                        raw = self._call_text_api(text_payload, filename)
                        raw_response = raw

                        from ..utils.json_utils import extract_json
                        r = self._coerce_extraction_result(extract_json(raw))
                        r = self._derive_missing_sample_sizes_from_text(r, text_payload)
                        r = self._flag_possible_se_as_sd(r, text_payload)

                        if r and isinstance(r, dict) and self._has_usable_extraction_result(r):
                            logger.info(f"[TEXT] Text fallback found usable data for {filename}")
                            r.setdefault("extraction_method", "text_fallback")
                            r = self._fetch_group_labels_if_missing(
                                r, filename, extracted_text=text_payload)
                            result = r
                        else:
                            logger.info(f"[TEXT] Text fallback found no usable data for {filename}")
                    else:
                        logger.info(f"[TEXT] No candidate text found for fallback: {filename}")

                except Exception as exc:
                    logger.warning(
                        f"[TEXT] Text fallback failed for {filename}: "
                        f"{type(exc).__name__}: {exc}"
                    )

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
                           'outcome_match', 'match_rationale', 'name', 'time_point',
                           'outcome_selected', 'timepoint_selected',
                           'source_quote_intervention', 'source_quote_control']:
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
                           'name', 'time_point',
                           'outcome_selected', 'timepoint_selected',
                           'source_quote_intervention', 'source_quote_control']
                for key in flat_keys:
                    result.pop(key, None)

            result = self._flag_suspect_source_quotes(
                result, source_text=text_payload)

            result.update({
                "file_id": None,
                "filename": filename,
                "extraction_error": None
            })

            logger.info(f"[VISION] Extraction complete for {filename}")
            result = self._apply_known_pdf_corrections(result, filename or str(pdf_path).replace('\\', '/').split('/')[-1], pdf_path)
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

        self._log_provenance_summary(results)
        return results

    @staticmethod
    def _log_provenance_summary(results) -> None:
        """Report which studies' data did not come straight from extraction."""
        overridden = []
        auto_meta = []

        for r in results or []:
            if not isinstance(r, dict):
                continue
            name = r.get("filename", "?")
            if r.get("override_fields"):
                overridden.append((name, r["override_fields"]))
            if r.get("metadata_source"):
                auto_meta.append((name, r["metadata_source"]))

        total = len(results or [])
        logger.info("-" * 60)
        logger.info("DATA PROVENANCE SUMMARY (%d stud%s)",
                    total, "y" if total == 1 else "ies")

        if overridden:
            logger.warning(
                "%d of %d studies used MANUAL OVERRIDES from study_overrides.yaml",
                len(overridden), total)
            for name, fields in overridden:
                logger.warning("    %s -> %s", name, fields)
            logger.warning(
                "These values were entered by a reviewer, not extracted. "
                "Report them as manually extracted in the review methods.")
        else:
            logger.info("  no manual overrides applied")

        if auto_meta:
            logger.warning(
                "%d of %d studies had metadata auto-derived from the PDF (VERIFY)",
                len(auto_meta), total)
            for name, source in auto_meta:
                logger.warning("    %s (%s)", name, source)

        logger.info("-" * 60)

    def _extract_anthropic(self, file_id, filename):
        """Anthropic-specific extraction (routes through shared tripwires)."""
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
            result = self._coerce_extraction_result(extract_json(raw))

            if not isinstance(result, dict):
                return {"file_id": file_id, "filename": filename,
                        "extraction_error": "Anthropic returned non-dict result"}

            if 'mean_intervention' in result or 'n_intervention' in result:
                primary_outcome = {}
                participants = {}

                for key in ['mean_intervention', 'sd_intervention',
                            'mean_control', 'sd_control',
                            'outcome_match', 'match_rationale', 'name', 'time_point',
                            'outcome_selected', 'timepoint_selected',
                            'source_quote_intervention', 'source_quote_control']:
                    if key in result and result[key] is not None:
                        primary_outcome[key] = result[key]

                for key in ['n_intervention', 'n_control']:
                    if key in result and result[key] is not None:
                        participants[key] = result[key]

                if primary_outcome:
                    result['primary_outcome'] = primary_outcome
                if participants:
                    result['participants'] = participants

                flat_keys = ['mean_intervention', 'sd_intervention',
                             'mean_control', 'sd_control',
                             'outcome_match', 'match_rationale',
                             'n_intervention', 'n_control',
                             'name', 'time_point',
                             'outcome_selected', 'timepoint_selected',
                             'source_quote_intervention', 'source_quote_control']
                for key in flat_keys:
                    result.pop(key, None)

            result.setdefault("extraction_method", "anthropic_file")

            result = self._flag_suspect_source_quotes(result, source_text=None)

            result.update({"file_id": file_id, "filename": filename,
                           "extraction_error": None})
            return result
        except Exception as e:
            return {"file_id": file_id, "filename": filename, "extraction_error": str(e)}
