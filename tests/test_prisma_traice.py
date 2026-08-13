"""Tests for prisma_traice.py — PRISMA-trAIce disclosure generator."""
import json
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "SOURCE_CODE"))
from prisma_traice import (
    AIUsageRecord,
    DataSovereigntyInfo,
    OversightLevel,
    PipelineStep,
    PRISMAtrAIceDisclosure,
    create_disclosure_from_session_log,
)


class TestAIUsageRecord:
    """Tests for AIUsageRecord dataclass."""

    def test_create_record(self):
        rec = AIUsageRecord(
            step=PipelineStep.DATA_EXTRACTION,
            model_name="deepseek-chat",
            model_version="v3",
            provider="DeepSeek",
            task_description="Extract outcome data from RCTs",
        )
        assert rec.step == PipelineStep.DATA_EXTRACTION
        assert rec.model_name == "deepseek-chat"
        assert rec.oversight == OversightLevel.HUMAN_VERIFIED

    def test_to_dict(self):
        rec = AIUsageRecord(
            step=PipelineStep.SCREENING_TITLE,
            model_name="qwen-72b",
            model_version="2.5",
            provider="Ollama",
            task_description="Screen titles and abstracts",
            oversight=OversightLevel.SPOT_CHECKED,
        )
        d = rec.to_dict()
        assert d["step"] == "title_abstract_screening"
        assert d["oversight"] == "ai_generated_spot_checked"
        assert d["model_name"] == "qwen-72b"

    def test_default_timestamp_set(self):
        rec = AIUsageRecord(
            step=PipelineStep.SEARCH,
            model_name="gpt-4o",
            model_version="2024-05",
            provider="OpenAI",
            task_description="Generate search strategy",
        )
        assert rec.timestamp  # not empty
        assert "T" in rec.timestamp  # ISO format


class TestDataSovereigntyInfo:
    """Tests for DataSovereigntyInfo dataclass."""

    def test_defaults_local_only(self):
        sov = DataSovereigntyInfo()
        assert sov.data_residency == "local_only"
        assert sov.data_sent_overseas is False
        assert sov.encryption_in_transit is True

    def test_cloud_config(self):
        sov = DataSovereigntyInfo(
            data_residency="cloud",
            cloud_providers_used=["OpenAI", "Anthropic"],
            data_sent_overseas=True,
            countries_involved=["United States"],
        )
        d = sov.to_dict()
        assert d["data_sent_overseas"] is True
        assert "United States" in d["countries_involved"]

    def test_local_model_config(self):
        sov = DataSovereigntyInfo(
            local_model_used=True,
            local_model_name="qwen3.6:latest",
        )
        assert sov.local_model_used is True
        assert sov.local_model_name == "qwen3.6:latest"


class TestPRISMAtrAIceDisclosure:
    """Tests for the main disclosure generator."""

    def _make_disclosure(self):
        d = PRISMAtrAIceDisclosure(
            review_title="Effectiveness of X for Y",
            authors=["Smith J", "Jones K"],
        )
        d.add_usage(AIUsageRecord(
            step=PipelineStep.DATA_EXTRACTION,
            model_name="deepseek-chat",
            model_version="v3",
            provider="DeepSeek",
            task_description="Extract outcome data from included RCTs",
            temperature=0.0,
            oversight=OversightLevel.HUMAN_VERIFIED,
            human_reviewer_count=2,
        ))
        d.add_usage(AIUsageRecord(
            step=PipelineStep.SCREENING_TITLE,
            model_name="qwen-72b",
            model_version="2.5",
            provider="Ollama (local)",
            task_description="Screen 2,340 titles and abstracts",
            oversight=OversightLevel.SPOT_CHECKED,
        ))
        return d

    def test_generate_methods_paragraph(self):
        d = self._make_disclosure()
        para = d.generate_methods_paragraph()
        assert "Artificial intelligence tools" in para
        assert "deepseek-chat" in para
        assert "data extraction" in para
        assert "PRISMA 2020" in para

    def test_generate_methods_paragraph_no_records(self):
        d = PRISMAtrAIceDisclosure(
            review_title="Test", authors=["A"]
        )
        para = d.generate_methods_paragraph()
        assert para == "No AI tools were used in this systematic review."

    def test_generate_structured_table(self):
        d = self._make_disclosure()
        table = d.generate_structured_table()
        assert len(table) == 2
        assert table[0]["AI Model"] == "deepseek-chat vv3"
        assert table[1]["Provider"] == "Ollama (local)"
        assert table[0]["Reviewers"] == 2

    def test_generate_json_report(self):
        d = self._make_disclosure()
        report_str = d.generate_json_report()
        report = json.loads(report_str)
        assert report["prisma_traice_version"] == "1.0.0"
        assert report["total_steps_with_ai"] == 2
        assert len(report["ai_usage_records"]) == 2
        assert "methods_paragraph" in report

    def test_save_report(self):
        d = self._make_disclosure()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "disclosure.json"
            result = d.save_report(out)
            assert result.exists()
            content = json.loads(result.read_text(encoding="utf-8"))
            assert content["review_title"] == "Effectiveness of X for Y"

    def test_sovereignty_in_methods(self):
        d = self._make_disclosure()
        d.set_sovereignty(DataSovereigntyInfo(
            local_model_used=True,
            local_model_name="qwen3.6:latest",
            data_sent_overseas=False,
        ))
        para = d.generate_methods_paragraph()
        assert "local AI model" in para
        assert "qwen3.6:latest" in para
        assert "No participant data" in para

    def test_sovereignty_overseas_warning(self):
        d = self._make_disclosure()
        d.set_sovereignty(DataSovereigntyInfo(
            data_sent_overseas=True,
            countries_involved=["United States", "China"],
            cloud_providers_used=["OpenAI", "DeepSeek"],
        ))
        para = d.generate_methods_paragraph()
        assert "United States" in para
        assert "China" in para

    def test_generate_data_sovereignty_notice_no_config(self):
        d = PRISMAtrAIceDisclosure(
            review_title="Test", authors=["A"]
        )
        notice = d.generate_data_sovereignty_notice()
        assert "No data sovereignty information" in notice

    def test_generate_data_sovereignty_notice_local(self):
        d = PRISMAtrAIceDisclosure(
            review_title="Test", authors=["A"]
        )
        d.set_sovereignty(DataSovereigntyInfo(
            local_model_used=True,
            local_model_name="qwen3.6:latest",
        ))
        notice = d.generate_data_sovereignty_notice()
        assert "DATA SOVEREIGNTY" in notice
        assert "qwen3.6:latest" in notice
        assert "All data processing occurred" in notice

    def test_generate_data_sovereignty_notice_overseas(self):
        d = PRISMAtrAIceDisclosure(
            review_title="Test", authors=["A"]
        )
        d.set_sovereignty(DataSovereigntyInfo(
            data_sent_overseas=True,
            countries_involved=["United States"],
            cloud_providers_used=["OpenAI"],
        ))
        notice = d.generate_data_sovereignty_notice()
        assert "WARNING" in notice
        assert "United States" in notice


class TestCreateFromSessionLog:
    """Tests for session log integration."""

    def test_basic_session_log(self):
        log = {
            "provider": "DeepSeek",
            "model": "deepseek-chat",
            "model_version": "v3",
            "steps_completed": [
                {
                    "step": "extract",
                    "description": "Extract data from 15 RCTs",
                    "temperature": 0.0,
                    "oversight": "ai_assisted_human_verified",
                    "reviewers": 2,
                },
                {
                    "step": "screen_titles",
                    "description": "Screen 500 titles",
                    "oversight": "ai_generated_spot_checked",
                },
            ],
        }
        d = create_disclosure_from_session_log(
            log, "Test Review", ["Author A"]
        )
        assert len(d.records) == 2
        assert d.records[0].step == PipelineStep.DATA_EXTRACTION
        assert d.records[1].oversight == OversightLevel.SPOT_CHECKED

    def test_session_log_with_sovereignty(self):
        log = {
            "provider": "Ollama",
            "model": "qwen3.6",
            "model_version": "latest",
            "steps_completed": [
                {"step": "search", "description": "Generate search terms"},
            ],
            "sovereignty": {
                "data_residency": "local_only",
                "local_model_used": True,
                "local_model_name": "qwen3.6:latest",
            },
        }
        d = create_disclosure_from_session_log(
            log, "Local Review", ["B"]
        )
        assert d.sovereignty is not None
        assert d.sovereignty.local_model_used is True

    def test_unknown_steps_skipped(self):
        log = {
            "provider": "Test",
            "model": "test-model",
            "model_version": "1.0",
            "steps_completed": [
                {"step": "unknown_step", "description": "Something"},
                {"step": "extract", "description": "Valid step"},
            ],
        }
        d = create_disclosure_from_session_log(
            log, "Test", ["A"]
        )
        assert len(d.records) == 1  # unknown_step skipped

    def test_empty_session_log(self):
        log = {"provider": "X", "model": "Y", "model_version": "1"}
        d = create_disclosure_from_session_log(log, "Empty", ["A"])
        assert len(d.records) == 0
        assert d.generate_methods_paragraph() == (
            "No AI tools were used in this systematic review."
        )
