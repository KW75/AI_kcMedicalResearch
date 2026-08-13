"""
table_extractor.py — Hybrid multi-page table extraction for SR pipeline.

Addresses the "Lami Table 4" bug where tables spanning pages 12-13
fail to extract because vision models receive pages as separate images.

Strategy order:
  A. PyMuPDF structured table extraction (fast, no API cost)
  B. Text-concatenation + LLM parsing (handles page breaks)
  C. Vision-based extraction with adjacent-page grouping (existing fallback)

Usage:
    from extraction.table_extractor import HybridTableExtractor
    extractor = HybridTableExtractor(pico_criteria=pico, provider="qwen", model="qwen-vl-plus")
    result = extractor.extract(pdf_path, filename)
"""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Strategy A: PyMuPDF structured table extraction
# ---------------------------------------------------------------------------
def extract_tables_pymupdf(pdf_path: str, target_columns: int = 0) -> list[dict]:
    """
    Extract tables from a PDF using PyMuPDF's built-in table finder.
    Returns list of dicts: {page, headers, rows, col_count, row_count}
    
    Handles multi-page tables by merging tables on consecutive pages
    that have the same column count and compatible headers.
    """
    doc = fitz.open(pdf_path)
    raw_tables = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        try:
            tables = page.find_tables()
            for table in tables:
                extracted = table.extract()
                if not extracted or len(extracted) < 2:
                    continue
                headers = [str(h).strip() if h else "" for h in extracted[0]]
                rows = []
                for row in extracted[1:]:
                    rows.append([str(cell).strip() if cell else "" for cell in row])
                raw_tables.append({
                    "page": page_num,
                    "headers": headers,
                    "rows": rows,
                    "col_count": len(headers),
                    "row_count": len(rows),
                })
        except Exception as e:
            logger.debug(f"[TABLE] Page {page_num} table extraction failed: {e}")
            continue

    doc.close()

    if not raw_tables:
        return []

    # Merge consecutive tables with matching column structure (multi-page tables)
    merged = [raw_tables[0]]
    for t in raw_tables[1:]:
        prev = merged[-1]
        # Same column count and consecutive pages = likely continuation
        if (t["col_count"] == prev["col_count"]
                and t["page"] == prev["page"] + 1
                and _headers_compatible(prev["headers"], t["headers"])):
            # Merge rows (skip header row of continuation)
            prev["rows"].extend(t["rows"])
            prev["row_count"] = len(prev["rows"])
            prev["page"] = t["page"]  # update to show span
            logger.info(f"[TABLE] Merged table spanning pages {prev['page']}-{t['page']}")
        else:
            merged.append(t)

    # Filter by target column count if specified
    if target_columns > 0:
        merged = [t for t in merged if t["col_count"] >= target_columns]

    return merged


def _headers_compatible(h1: list[str], h2: list[str]) -> bool:
    """Check if two header rows are compatible (same or h2 is empty/repeat)."""
    if not h2 or all(not cell for cell in h2):
        return True  # Empty header row = continuation
    # If h2 matches h1, it's a repeated header on new page
    if h1 == h2:
        return True
    # If h2 looks like data (has numbers), it's a continuation without header
    numeric_cells = sum(1 for cell in h2 if re.search(r'\d', cell))
    if numeric_cells >= len(h2) // 2:
        return True
    return False


def table_to_markdown(table: dict) -> str:
    """Convert a table dict to markdown format for LLM consumption."""
    lines = []
    lines.append("| " + " | ".join(table["headers"]) + " |")
    lines.append("| " + " | ".join(["---"] * table["col_count"]) + " |")
    for row in table["rows"]:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Strategy B: Text concatenation from adjacent pages
# ---------------------------------------------------------------------------
def extract_text_around_table(
    pdf_path: str,
    table_keywords: list[str] | None = None,
    context_pages: int = 2,
) -> list[dict]:
    """
    Find pages mentioning table keywords and extract text from those pages
    plus surrounding context. Returns page groups with concatenated text.
    """
    if table_keywords is None:
        table_keywords = ["table", "mean", "sd", "intervention", "control",
                          "baseline", "outcome", "results"]

    doc = fitz.open(pdf_path)
    total_pages = len(doc)

    # Score pages by keyword density
    page_scores = []
    for i in range(total_pages):
        text = doc[i].get_text().lower()
        score = sum(text.count(kw) for kw in table_keywords)
        # Bonus for numeric density (tables have lots of numbers)
        numbers = len(re.findall(r'\b\d+\.?\d*\b', text))
        score += min(numbers // 5, 10)
        page_scores.append((i, score))

    page_scores.sort(key=lambda x: x[1], reverse=True)

    # Get top 3 scoring pages and their context
    groups = []
    used_pages = set()
    for page_num, score in page_scores[:3]:
        if score < 5 or page_num in used_pages:
            continue
        start = max(0, page_num - context_pages)
        end = min(total_pages, page_num + context_pages + 1)
        page_range = list(range(start, end))
        used_pages.update(page_range)

        combined_text = ""
        for p in page_range:
            combined_text += f"\n--- Page {p + 1} ---\n"
            combined_text += doc[p].get_text()

        groups.append({
            "pages": page_range,
            "center_page": page_num,
            "score": score,
            "text": combined_text,
        })

    doc.close()
    return groups


# ---------------------------------------------------------------------------
# Strategy C: Adjacent-page image grouping for vision
# ---------------------------------------------------------------------------
def get_adjacent_page_images(
    pdf_path: str,
    center_pages: list[int],
    context: int = 1,
    max_images: int = 8,
) -> list[tuple[int, str]]:
    """
    For each center page, include adjacent pages as images.
    Returns list of (page_num, base64_image) tuples.
    """
    import base64
    import io
    from PIL import Image

    doc = fitz.open(pdf_path)
    total_pages = len(doc)

    selected = set()
    for cp in center_pages:
        for offset in range(-context, context + 1):
            p = cp + offset
            if 0 <= p < total_pages:
                selected.add(p)

    selected = sorted(selected)[:max_images]

    results = []
    for page_num in selected:
        pix = doc[page_num].get_pixmap(matrix=fitz.Matrix(2, 2))
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()
        results.append((page_num, img_base64))

    doc.close()
    return results


# ---------------------------------------------------------------------------
# Hybrid extractor class
# ---------------------------------------------------------------------------
EXTRACTION_PROMPT_TABLE = """You are a clinical data extractor for a systematic review.

THE REVIEW'S SPECIFIED PRIMARY OUTCOME IS: {outcome}

PICO CONTEXT:
  Population:   {population}
  Intervention: {intervention}
  Comparator:   {comparator}

IMPORTANT: The table data below may span MULTIPLE PAGES. Rows that appear
at the top of a new page are continuations of the table from the previous page.
Look for the complete table structure across all pages.

TABLE DATA (extracted from PDF):
{table_data}

Extract the primary outcome data. Return JSON:
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

DO NOT fabricate values. Return null if not found.
"""


class HybridTableExtractor:
    """
    Multi-strategy table extractor that handles page-spanning tables.
    
    Tries in order:
      A. PyMuPDF structured extraction + LLM interpretation
      B. Text concatenation + LLM parsing
      C. Falls back to existing DataExtractor vision approach
    """

    def __init__(
        self,
        pico_criteria: dict | None = None,
        pico_outcome: str | None = None,
        provider: str = "qwen",
        model: str = "qwen-vl-plus",
        call_llm_fn=None,
        api_key: str | None = None,
    ):
        self.pico = pico_criteria or {}
        self.outcome = pico_outcome or self.pico.get("outcome", "")
        self.provider = provider
        self.model = model
        self.call_llm_fn = call_llm_fn
        self.api_key = api_key

    def _make_prompt(self, table_data: str) -> str:
        return EXTRACTION_PROMPT_TABLE.format(
            outcome=self.outcome or "(not specified)",
            population=self.pico.get("population", "(not specified)"),
            intervention=self.pico.get("intervention", "(not specified)"),
            comparator=self.pico.get("comparator", "(not specified)"),
            table_data=table_data,
        )

    def _call_llm(self, prompt: str) -> str:
        """Call LLM using provided function or fall back to providers module."""
        if self.call_llm_fn:
            return self.call_llm_fn("", prompt)

        # Fall back to providers.call_ai
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent))
        from providers import call_ai
        return call_ai(prompt=prompt, provider=self.provider, model=self.model)

    def extract(self, pdf_path: str, filename: str = "") -> dict:
        """
        Run hybrid extraction. Returns dict with extraction results.
        """
        logger.info(f"[HYBRID] Starting extraction for {filename}")

        # --- Strategy A: PyMuPDF table extraction ---
        result = self._try_pymupdf(pdf_path, filename)
        if result:
            logger.info(f"[HYBRID] Strategy A (PyMuPDF tables) succeeded for {filename}")
            return result

        # --- Strategy B: Text concatenation ---
        result = self._try_text_concat(pdf_path, filename)
        if result:
            logger.info(f"[HYBRID] Strategy B (text concat) succeeded for {filename}")
            return result

        # --- Strategy C: Fall back to existing DataExtractor ---
        logger.info(f"[HYBRID] Falling back to Strategy C (vision) for {filename}")
        return self._try_vision_fallback(pdf_path, filename)

    def _try_pymupdf(self, pdf_path: str, filename: str) -> dict | None:
        """Strategy A: Extract tables structurally, send to LLM for interpretation."""
        try:
            tables = extract_tables_pymupdf(pdf_path)
            if not tables:
                logger.info(f"[HYBRID-A] No tables found by PyMuPDF in {filename}")
                return None

            # Convert all tables to markdown and let LLM pick the right one
            all_tables_md = []
            for i, t in enumerate(tables):
                if t["row_count"] >= 2:  # Skip tiny tables
                    md = table_to_markdown(t)
                    all_tables_md.append(f"### Table {i+1} (page {t['page']+1}, {t['row_count']} rows)\n{md}")

            if not all_tables_md:
                return None

            table_data = "\n\n".join(all_tables_md[:5])  # Max 5 tables
            prompt = self._make_prompt(table_data)
            raw_response = self._call_llm(prompt)

            from ..utils.json_utils import extract_json
            result = extract_json(raw_response)

            if self._has_outcome_data(result):
                result.update({"file_id": None, "filename": filename,
                              "extraction_error": None, "strategy": "pymupdf_table"})
                return result

            logger.info(f"[HYBRID-A] PyMuPDF tables found but no outcome data in {filename}")
            return None

        except Exception as e:
            logger.debug(f"[HYBRID-A] Failed for {filename}: {e}")
            return None

    def _try_text_concat(self, pdf_path: str, filename: str) -> dict | None:
        """Strategy B: Concatenate text from high-scoring pages, send to LLM."""
        try:
            groups = extract_text_around_table(pdf_path)
            if not groups:
                return None

            # Use the highest-scoring group
            best_group = groups[0]
            prompt = self._make_prompt(best_group["text"][:12000])  # Limit context
            raw_response = self._call_llm(prompt)

            from ..utils.json_utils import extract_json
            result = extract_json(raw_response)

            if self._has_outcome_data(result):
                result.update({"file_id": None, "filename": filename,
                              "extraction_error": None, "strategy": "text_concat"})
                return result

            return None

        except Exception as e:
            logger.debug(f"[HYBRID-B] Failed for {filename}: {e}")
            return None

    def _try_vision_fallback(self, pdf_path: str, filename: str) -> dict:
        """Strategy C: Delegate to existing DataExtractor (vision-based)."""
        try:
            from .data_extractor import DataExtractor
            de = DataExtractor(
                pico_criteria=self.pico,
                pico_outcome=self.outcome,
                model=self.model,
                provider=self.provider,
                api_key=self.api_key,
            )
            return de.extract_by_pdf_path(pdf_path, filename)
        except Exception as e:
            logger.error(f"[HYBRID-C] Vision fallback failed for {filename}: {e}")
            return {
                "file_id": None,
                "filename": filename,
                "extraction_error": str(e),
                "primary_outcome": {},
                "participants": {},
            }

    @staticmethod
    def _has_outcome_data(result: dict) -> bool:
        """Check if extraction result contains meaningful outcome data."""
        if not result or not isinstance(result, dict):
            return False
        po = result.get("primary_outcome", {})
        if isinstance(po, dict):
            if po.get("mean_intervention") is not None:
                return True
            if po.get("outcome_match") is True:
                return True
        # Flat structure
        if result.get("mean_intervention") is not None:
            return True
        return False
