"""
traice_integration.py — Integrates PRISMA-trAIce disclosure into pipeline runs.

Provides:
- PipelineTracer: context manager that records AI calls during a pipeline run
- auto_generate_disclosure(): called at pipeline completion to write the report
- get_tracer(): module-level access to the active tracer instance
"""
from __future__ import annotations

import os
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Generator

from prisma_traice import (
    AIUsageRecord,
    DataSovereigntyInfo,
    OversightLevel,
    PipelineStep,
    PRISMAtrAIceDisclosure,
)


# Module-level active tracer
_active_tracer: Optional["PipelineTracer"] = None


def get_tracer() -> Optional["PipelineTracer"]:
    """Get the currently active pipeline tracer."""
    return _active_tracer


@dataclass
class CallRecord:
    """Raw record of a single AI call."""
    step: str
    provider: str
    model: str
    model_version: str
    prompt_length: int
    response_length: int
    temperature: float
    max_tokens: int
    duration_ms: float
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    stream: bool = False
    fallback_used: bool = False
    error: str = ""


# Mapping from internal step names to PipelineStep enum
STEP_MAP = {
    "search": PipelineStep.SEARCH,
    "search_strategy": PipelineStep.SEARCH,
    "screen_titles": PipelineStep.SCREENING_TITLE,
    "title_abstract_screening": PipelineStep.SCREENING_TITLE,
    "screen_fulltext": PipelineStep.SCREENING_FULLTEXT,
    "full_text_screening": PipelineStep.SCREENING_FULLTEXT,
    "extract": PipelineStep.DATA_EXTRACTION,
    "data_extraction": PipelineStep.DATA_EXTRACTION,
    "quality": PipelineStep.QUALITY_ASSESSMENT,
    "quality_assessment": PipelineStep.QUALITY_ASSESSMENT,
    "rob": PipelineStep.QUALITY_ASSESSMENT,
    "synthesize": PipelineStep.SYNTHESIS,
    "synthesis": PipelineStep.SYNTHESIS,
    "narrative_synthesis": PipelineStep.SYNTHESIS,
    "meta_analysis": PipelineStep.META_ANALYSIS,
    "report": PipelineStep.REPORTING,
    "reporting": PipelineStep.REPORTING,
}


class PipelineTracer:
    """Records AI usage throughout a pipeline run for PRISMA-trAIce disclosure.

    Usage:
        with PipelineTracer(review_title="...", authors=["..."]) as tracer:
            # ... run pipeline steps ...
            tracer.record_call(step="extract", provider="DeepSeek", ...)
        # Disclosure auto-generated on exit
    """

    def __init__(
        self,
        review_title: str = "Untitled Review",
        authors: Optional[list[str]] = None,
        output_dir: Optional[Path] = None,
        oversight_default: OversightLevel = OversightLevel.HUMAN_VERIFIED,
        auto_save: bool = True,
    ):
        self.review_title = review_title
        self.authors = authors or ["Not specified"]
        self.output_dir = Path(output_dir) if output_dir else Path("output/disclosures")
        self.oversight_default = oversight_default
        self.auto_save = auto_save
        self.calls: list[CallRecord] = []
        self.sovereignty: Optional[DataSovereigntyInfo] = None
        self._start_time: Optional[float] = None
        self._active = False

    def __enter__(self) -> "PipelineTracer":
        global _active_tracer
        _active_tracer = self
        self._active = True
        self._start_time = time.time()
        self._detect_sovereignty()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        global _active_tracer
        self._active = False
        _active_tracer = None
        if self.auto_save and self.calls and exc_type is None:
            self.save_disclosure()

    def _detect_sovereignty(self) -> None:
        """Auto-detect data sovereignty settings from environment."""
        provider = os.environ.get("DEFAULT_PROVIDER", "").lower()
        ollama_host = os.environ.get("OLLAMA_HOST", "")

        local_providers = {"ollama", "local", "llamacpp"}
        cloud_providers_map = {
            "openai": ("OpenAI", "United States"),
            "anthropic": ("Anthropic", "United States"),
            "deepseek": ("DeepSeek", "China"),
            "groq": ("Groq", "United States"),
            "qwen": ("Alibaba Cloud", "China"),
        }

        is_local = provider in local_providers
        cloud_list = []
        countries = []

        if not is_local and provider in cloud_providers_map:
            name, country = cloud_providers_map[provider]
            cloud_list.append(name)
            countries.append(country)

        # Check fallback providers too
        fallback = os.environ.get("FALLBACK_PROVIDERS", "")
        for fb in fallback.split(","):
            fb = fb.strip().lower()
            if fb in cloud_providers_map:
                name, country = cloud_providers_map[fb]
                if name not in cloud_list:
                    cloud_list.append(name)
                if country not in countries:
                    countries.append(country)

        local_model = ""
        if is_local:
            local_model = os.environ.get("OLLAMA_MODEL", "unknown")

        self.sovereignty = DataSovereigntyInfo(
            data_residency="local_only" if is_local else "cloud",
            cloud_providers_used=cloud_list,
            data_sent_overseas=len(countries) > 0,
            countries_involved=countries,
            local_model_used=is_local,
            local_model_name=local_model,
            pii_handling="no_pii_transmitted" if is_local else "api_calls_may_include_text",
        )

    def record_call(
        self,
        step: str,
        provider: str,
        model: str,
        model_version: str = "unknown",
        prompt_length: int = 0,
        response_length: int = 0,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        duration_ms: float = 0.0,
        stream: bool = False,
        fallback_used: bool = False,
        error: str = "",
    ) -> None:
        """Record a single AI call during the pipeline."""
        if not self._active:
            return

        self.calls.append(CallRecord(
            step=step,
            provider=provider,
            model=model,
            model_version=model_version,
            prompt_length=prompt_length,
            response_length=response_length,
            temperature=temperature,
            max_tokens=max_tokens,
            duration_ms=duration_ms,
            stream=stream,
            fallback_used=fallback_used,
            error=error,
        ))

    def build_disclosure(self) -> PRISMAtrAIceDisclosure:
        """Build a PRISMAtrAIceDisclosure from recorded calls."""
        disclosure = PRISMAtrAIceDisclosure(
            review_title=self.review_title,
            authors=self.authors,
        )

        # Group calls by step
        step_groups: dict[str, list[CallRecord]] = {}
        for call in self.calls:
            step_groups.setdefault(call.step, []).append(call)

        for step_name, calls in step_groups.items():
            pipeline_step = STEP_MAP.get(step_name)
            if pipeline_step is None:
                continue

            # Use the most common model for this step
            models = [c.model for c in calls]
            primary_model = max(set(models), key=models.count)
            primary_call = next(c for c in calls if c.model == primary_model)

            total_duration = sum(c.duration_ms for c in calls)
            had_fallback = any(c.fallback_used for c in calls)
            had_errors = any(c.error for c in calls)

            notes_parts = []
            notes_parts.append(f"{len(calls)} AI call(s)")
            notes_parts.append(f"total duration: {total_duration:.0f}ms")
            if had_fallback:
                notes_parts.append("fallback provider used")
            if had_errors:
                notes_parts.append("some calls had errors")

            record = AIUsageRecord(
                step=pipeline_step,
                model_name=primary_model,
                model_version=primary_call.model_version,
                provider=primary_call.provider,
                task_description=f"AI-assisted {step_name.replace('_', ' ')}",
                prompt_strategy="structured",
                temperature=primary_call.temperature,
                max_tokens=primary_call.max_tokens,
                oversight=self.oversight_default,
                notes="; ".join(notes_parts),
            )
            disclosure.add_usage(record)

        if self.sovereignty:
            disclosure.set_sovereignty(self.sovereignty)

        return disclosure

    def save_disclosure(self) -> Path:
        """Build and save the disclosure report."""
        disclosure = self.build_disclosure()
        self.output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"prisma_traice_{timestamp}.json"
        output_path = self.output_dir / filename

        disclosure.save_report(output_path)

        # Also save the methods paragraph as plain text
        para_path = self.output_dir / f"methods_paragraph_{timestamp}.txt"
        para_path.write_text(
            disclosure.generate_methods_paragraph(), encoding="utf-8"
        )

        # Save sovereignty notice
        notice_path = self.output_dir / f"sovereignty_notice_{timestamp}.txt"
        notice_path.write_text(
            disclosure.generate_data_sovereignty_notice(), encoding="utf-8"
        )

        return output_path

    def get_summary(self) -> dict:
        """Get a summary of recorded calls."""
        if not self.calls:
            return {"total_calls": 0, "steps": [], "models": [], "duration_ms": 0}

        return {
            "total_calls": len(self.calls),
            "steps": list(set(c.step for c in self.calls)),
            "models": list(set(c.model for c in self.calls)),
            "providers": list(set(c.provider for c in self.calls)),
            "duration_ms": sum(c.duration_ms for c in self.calls),
            "fallbacks_used": sum(1 for c in self.calls if c.fallback_used),
            "errors": sum(1 for c in self.calls if c.error),
        }


@contextmanager
def trace_pipeline(
    review_title: str = "Untitled Review",
    authors: Optional[list[str]] = None,
    output_dir: Optional[Path] = None,
    oversight: OversightLevel = OversightLevel.HUMAN_VERIFIED,
    auto_save: bool = True,
) -> Generator[PipelineTracer, None, None]:
    """Context manager for tracing a pipeline run.

    Usage:
        with trace_pipeline("My Review", ["Author A"]) as tracer:
            result = call_ai(prompt, provider="deepseek")
            tracer.record_call(step="extract", provider="deepseek", model="deepseek-chat", ...)
    """
    tracer = PipelineTracer(
        review_title=review_title,
        authors=authors,
        output_dir=output_dir,
        oversight_default=oversight,
        auto_save=auto_save,
    )
    with tracer:
        yield tracer
