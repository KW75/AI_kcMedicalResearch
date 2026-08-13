"""
prisma_traice.py — PRISMA-trAIce AI Transparency Disclosure Generator

Generates structured transparency statements documenting:
- Which AI models were used at each pipeline step
- Parameters and configurations applied
- Human oversight measures
- Data handling and sovereignty information

References:
- Page et al. (2021) PRISMA 2020 statement
- Cochrane AI methods guidance (2024)
- trAIce framework for AI transparency in evidence synthesis
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional


class PipelineStep(Enum):
    """Standard systematic review pipeline steps."""
    SEARCH = "search_strategy"
    SCREENING_TITLE = "title_abstract_screening"
    SCREENING_FULLTEXT = "full_text_screening"
    DATA_EXTRACTION = "data_extraction"
    QUALITY_ASSESSMENT = "quality_assessment"
    SYNTHESIS = "narrative_synthesis"
    META_ANALYSIS = "meta_analysis"
    REPORTING = "report_generation"


class OversightLevel(Enum):
    """Level of human oversight applied."""
    FULL_HUMAN = "full_human_review"
    HUMAN_VERIFIED = "ai_assisted_human_verified"
    SPOT_CHECKED = "ai_generated_spot_checked"
    AI_ONLY = "ai_only_no_human_review"


@dataclass
class AIUsageRecord:
    """Record of AI usage at a single pipeline step."""
    step: PipelineStep
    model_name: str
    model_version: str
    provider: str
    task_description: str
    prompt_strategy: str = ""
    temperature: float = 0.0
    max_tokens: int = 4096
    oversight: OversightLevel = OversightLevel.HUMAN_VERIFIED
    human_reviewer_count: int = 1
    disagreement_resolution: str = "consensus discussion"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    notes: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["step"] = self.step.value
        d["oversight"] = self.oversight.value
        return d


@dataclass
class DataSovereigntyInfo:
    """Data sovereignty and privacy disclosure."""
    data_residency: str = "local_only"
    cloud_providers_used: list[str] = field(default_factory=list)
    data_sent_overseas: bool = False
    countries_involved: list[str] = field(default_factory=list)
    encryption_in_transit: bool = True
    encryption_at_rest: bool = True
    pii_handling: str = "no_pii_transmitted"
    data_retention_policy: str = "no_cloud_retention"
    local_model_used: bool = False
    local_model_name: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


class PRISMAtrAIceDisclosure:
    """Generates PRISMA-trAIce transparency disclosures."""

    def __init__(
        self,
        review_title: str,
        authors: list[str],
        date: Optional[str] = None,
    ):
        self.review_title = review_title
        self.authors = authors
        self.date = date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        self.records: list[AIUsageRecord] = []
        self.sovereignty: Optional[DataSovereigntyInfo] = None
        self._version = "1.0.0"

    def add_usage(self, record: AIUsageRecord) -> None:
        """Add an AI usage record for a pipeline step."""
        self.records.append(record)

    def set_sovereignty(self, info: DataSovereigntyInfo) -> None:
        """Set data sovereignty information."""
        self.sovereignty = info

    def generate_methods_paragraph(self) -> str:
        """Generate a ready-to-paste Methods section paragraph."""
        if not self.records:
            return "No AI tools were used in this systematic review."

        models_used = set()
        steps_with_ai = []

        for rec in self.records:
            models_used.add(f"{rec.model_name} ({rec.provider})")
            step_label = rec.step.value.replace("_", " ")
            steps_with_ai.append(step_label)

        models_str = ", ".join(sorted(models_used))
        steps_str = ", ".join(steps_with_ai)

        oversight_counts = {}
        for rec in self.records:
            level = rec.oversight.value.replace("_", " ")
            oversight_counts[level] = oversight_counts.get(level, 0) + 1

        oversight_str = "; ".join(
            f"{v} step(s) with {k}" for k, v in oversight_counts.items()
        )

        paragraph = (
            f"Artificial intelligence tools were used to assist with the following "
            f"systematic review steps: {steps_str}. "
            f"The AI models employed were: {models_str}. "
            f"Human oversight was applied as follows: {oversight_str}. "
        )

        if self.sovereignty:
            sov = self.sovereignty
            if sov.local_model_used:
                paragraph += (
                    f"A local AI model ({sov.local_model_name}) was used to ensure "
                    f"data remained within the local computing environment. "
                )
            if sov.data_sent_overseas:
                countries = ", ".join(sov.countries_involved)
                paragraph += (
                    f"Some data was transmitted to cloud providers in: {countries}. "
                )
            else:
                paragraph += (
                    "No participant data or sensitive information was transmitted "
                    "to external cloud services. "
                )
            paragraph += f"Data retention policy: {sov.data_retention_policy}. "

        paragraph += (
            "This disclosure follows the PRISMA 2020 guidelines and the trAIce "
            "framework for transparent reporting of AI in evidence synthesis "
            "(Page et al., 2021)."
        )

        return paragraph

    def generate_structured_table(self) -> list[dict]:
        """Generate structured data for a disclosure table."""
        rows = []
        for rec in self.records:
            rows.append({
                "Pipeline Step": rec.step.value.replace("_", " ").title(),
                "AI Model": f"{rec.model_name} v{rec.model_version}",
                "Provider": rec.provider,
                "Task": rec.task_description,
                "Temperature": rec.temperature,
                "Oversight": rec.oversight.value.replace("_", " ").title(),
                "Reviewers": rec.human_reviewer_count,
                "Disagreement Resolution": rec.disagreement_resolution,
                "Notes": rec.notes,
            })
        return rows

    def generate_json_report(self) -> str:
        """Generate a full JSON disclosure report."""
        report = {
            "prisma_traice_version": self._version,
            "review_title": self.review_title,
            "authors": self.authors,
            "disclosure_date": self.date,
            "ai_usage_records": [r.to_dict() for r in self.records],
            "data_sovereignty": self.sovereignty.to_dict() if self.sovereignty else None,
            "methods_paragraph": self.generate_methods_paragraph(),
            "total_steps_with_ai": len(self.records),
            "models_used": list(set(r.model_name for r in self.records)),
        }
        return json.dumps(report, indent=2, ensure_ascii=False)

    def save_report(self, output_path: Path) -> Path:
        """Save the full disclosure report to a JSON file."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(self.generate_json_report(), encoding="utf-8")
        return output_path

    def generate_data_sovereignty_notice(self) -> str:
        """Generate a standalone data sovereignty notice."""
        if not self.sovereignty:
            return "No data sovereignty information has been configured."

        sov = self.sovereignty
        lines = []
        lines.append("DATA SOVEREIGNTY & PRIVACY NOTICE")
        lines.append("=" * 40)
        lines.append("")
        lines.append(f"Data Residency: {sov.data_residency}")
        lines.append(f"Local Model Used: {'Yes — ' + sov.local_model_name if sov.local_model_used else 'No'}")
        lines.append(f"Data Sent Overseas: {'Yes' if sov.data_sent_overseas else 'No'}")

        if sov.countries_involved:
            lines.append(f"Countries Involved: {', '.join(sov.countries_involved)}")

        if sov.cloud_providers_used:
            lines.append(f"Cloud Providers: {', '.join(sov.cloud_providers_used)}")

        lines.append(f"Encryption in Transit: {'Yes' if sov.encryption_in_transit else 'No'}")
        lines.append(f"Encryption at Rest: {'Yes' if sov.encryption_at_rest else 'No'}")
        lines.append(f"PII Handling: {sov.pii_handling}")
        lines.append(f"Data Retention: {sov.data_retention_policy}")
        lines.append("")

        if sov.data_sent_overseas:
            lines.append(
                "WARNING: Data was transmitted to servers outside the local jurisdiction. "
                "Ensure compliance with applicable data protection regulations "
                "(e.g., GDPR, HIPAA, Australian Privacy Act 1988)."
            )
        else:
            lines.append(
                "All data processing occurred within the local computing environment. "
                "No sensitive data was transmitted to external services."
            )

        return "\n".join(lines)


def create_disclosure_from_session_log(
    session_log: dict,
    review_title: str,
    authors: list[str],
) -> PRISMAtrAIceDisclosure:
    """Create a disclosure from a pipeline session log.

    The session_log should contain keys like:
      - "provider": str
      - "model": str
      - "model_version": str
      - "steps_completed": list of step dicts
      - "sovereignty": dict (optional)
    """
    disclosure = PRISMAtrAIceDisclosure(
        review_title=review_title,
        authors=authors,
    )

    provider = session_log.get("provider", "unknown")
    model = session_log.get("model", "unknown")
    model_version = session_log.get("model_version", "unknown")

    step_mapping = {
        "search": PipelineStep.SEARCH,
        "screen_titles": PipelineStep.SCREENING_TITLE,
        "screen_fulltext": PipelineStep.SCREENING_FULLTEXT,
        "extract": PipelineStep.DATA_EXTRACTION,
        "quality": PipelineStep.QUALITY_ASSESSMENT,
        "synthesize": PipelineStep.SYNTHESIS,
        "meta_analysis": PipelineStep.META_ANALYSIS,
        "report": PipelineStep.REPORTING,
    }

    for step_info in session_log.get("steps_completed", []):
        step_key = step_info.get("step", "")
        pipeline_step = step_mapping.get(step_key)
        if pipeline_step is None:
            continue

        record = AIUsageRecord(
            step=pipeline_step,
            model_name=step_info.get("model", model),
            model_version=step_info.get("model_version", model_version),
            provider=step_info.get("provider", provider),
            task_description=step_info.get("description", f"AI-assisted {step_key}"),
            prompt_strategy=step_info.get("prompt_strategy", "structured"),
            temperature=step_info.get("temperature", 0.0),
            max_tokens=step_info.get("max_tokens", 4096),
            oversight=OversightLevel(
                step_info.get("oversight", "ai_assisted_human_verified")
            ),
            human_reviewer_count=step_info.get("reviewers", 1),
            disagreement_resolution=step_info.get(
                "disagreement_resolution", "consensus discussion"
            ),
            notes=step_info.get("notes", ""),
        )
        disclosure.add_usage(record)

    if "sovereignty" in session_log:
        sov_data = session_log["sovereignty"]
        disclosure.set_sovereignty(DataSovereigntyInfo(**sov_data))

    return disclosure
