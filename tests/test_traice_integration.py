"""Tests for traice_integration.py ??pipeline tracing and auto-disclosure."""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "SOURCE_CODE"))
from traice_integration import (
    CallRecord,
    PipelineTracer,
    STEP_MAP,
    get_tracer,
    trace_pipeline,
)
from prisma_traice import OversightLevel, PipelineStep


class TestCallRecord:
    """Tests for CallRecord dataclass."""

    def test_create_record(self):
        rec = CallRecord(
            step="extract",
            provider="DeepSeek",
            model="deepseek-chat",
            model_version="v3",
            prompt_length=500,
            response_length=1200,
            temperature=0.0,
            max_tokens=4096,
            duration_ms=1500.0,
        )
        assert rec.step == "extract"
        assert rec.duration_ms == 1500.0
        assert rec.fallback_used is False

    def test_timestamp_auto_set(self):
        rec = CallRecord(
            step="search", provider="X", model="Y",
            model_version="1", prompt_length=0,
            response_length=0, temperature=0.0,
            max_tokens=0, duration_ms=0.0,
        )
        assert "T" in rec.timestamp


class TestStepMap:
    """Tests for step name mapping."""

    def test_known_steps_mapped(self):
        assert STEP_MAP["extract"] == PipelineStep.DATA_EXTRACTION
        assert STEP_MAP["screen_titles"] == PipelineStep.SCREENING_TITLE
        assert STEP_MAP["meta_analysis"] == PipelineStep.META_ANALYSIS
        assert STEP_MAP["rob"] == PipelineStep.QUALITY_ASSESSMENT

    def test_unknown_step_not_in_map(self):
        assert "unknown_step" not in STEP_MAP


class TestPipelineTracer:
    """Tests for PipelineTracer."""

    def test_context_manager_activates(self):
        with PipelineTracer(auto_save=False) as tracer:
            assert tracer._active is True
            assert get_tracer() is tracer
        assert get_tracer() is None

    def test_record_call(self):
        with PipelineTracer(auto_save=False) as tracer:
            tracer.record_call(
                step="extract",
                provider="DeepSeek",
                model="deepseek-chat",
                model_version="v3",
                prompt_length=500,
                response_length=1200,
                duration_ms=1500.0,
            )
        assert len(tracer.calls) == 1
        assert tracer.calls[0].step == "extract"

    def test_record_call_inactive_ignored(self):
        tracer = PipelineTracer(auto_save=False)
        tracer.record_call(
            step="extract", provider="X", model="Y",
            model_version="1", duration_ms=0.0,
        )
        assert len(tracer.calls) == 0  # not active

    def test_build_disclosure(self):
        with PipelineTracer(
            review_title="Test Review",
            authors=["Author A"],
            auto_save=False,
        ) as tracer:
            tracer.record_call(
                step="extract", provider="DeepSeek",
                model="deepseek-chat", model_version="v3",
                prompt_length=500, response_length=1200,
                temperature=0.0, max_tokens=4096, duration_ms=1500.0,
            )
            tracer.record_call(
                step="screen_titles", provider="Ollama",
                model="qwen3.6", model_version="latest",
                prompt_length=300, response_length=50,
                temperature=0.0, max_tokens=2048, duration_ms=800.0,
            )

        disclosure = tracer.build_disclosure()
        assert len(disclosure.records) == 2
        assert disclosure.review_title == "Test Review"

    def test_build_disclosure_groups_calls(self):
        with PipelineTracer(auto_save=False) as tracer:
            for i in range(5):
                tracer.record_call(
                    step="extract", provider="DeepSeek",
                    model="deepseek-chat", model_version="v3",
                    prompt_length=100, response_length=200,
                    duration_ms=500.0,
                )

        disclosure = tracer.build_disclosure()
        # 5 calls to same step = 1 record
        assert len(disclosure.records) == 1
        assert "5 AI call(s)" in disclosure.records[0].notes

    def test_save_disclosure(self):
        with tempfile.TemporaryDirectory() as tmp:
            with PipelineTracer(
                review_title="Save Test",
                authors=["B"],
                output_dir=Path(tmp),
                auto_save=False,
            ) as tracer:
                tracer.record_call(
                    step="extract", provider="DeepSeek",
                    model="deepseek-chat", model_version="v3",
                    prompt_length=100, response_length=200,
                    duration_ms=500.0,
                )

            output = tracer.save_disclosure()
            assert output.exists()
            content = json.loads(output.read_text(encoding="utf-8"))
            assert content["review_title"] == "Save Test"

            # Check methods paragraph file exists
            txt_files = list(Path(tmp).glob("methods_paragraph_*.txt"))
            assert len(txt_files) == 1

            # Check sovereignty notice file exists
            sov_files = list(Path(tmp).glob("sovereignty_notice_*.txt"))
            assert len(sov_files) == 1

    def test_auto_save_on_exit(self):
        with tempfile.TemporaryDirectory() as tmp:
            with PipelineTracer(
                review_title="Auto Save",
                authors=["C"],
                output_dir=Path(tmp),
                auto_save=True,
            ) as tracer:
                tracer.record_call(
                    step="search", provider="OpenAI",
                    model="gpt-4o", model_version="2024-05",
                    prompt_length=200, response_length=500,
                    duration_ms=2000.0,
                )

            # Should have auto-saved
            json_files = list(Path(tmp).glob("prisma_traice_*.json"))
            assert len(json_files) == 1

    def test_no_auto_save_on_exception(self):
        with tempfile.TemporaryDirectory() as tmp:
            try:
                with PipelineTracer(
                    output_dir=Path(tmp), auto_save=True,
                ) as tracer:
                    tracer.record_call(
                        step="search", provider="X", model="Y",
                        model_version="1", duration_ms=0.0,
                    )
                    raise ValueError("Simulated failure")
            except ValueError:
                pass

            json_files = list(Path(tmp).glob("prisma_traice_*.json"))
            assert len(json_files) == 0  # not saved due to exception

    def test_no_auto_save_when_no_calls(self):
        with tempfile.TemporaryDirectory() as tmp:
            with PipelineTracer(
                output_dir=Path(tmp), auto_save=True,
            ) as tracer:
                pass  # no calls made

            json_files = list(Path(tmp).glob("prisma_traice_*.json"))
            assert len(json_files) == 0

    def test_get_summary_empty(self):
        tracer = PipelineTracer(auto_save=False)
        summary = tracer.get_summary()
        assert summary["total_calls"] == 0

    def test_get_summary_with_calls(self):
        with PipelineTracer(auto_save=False) as tracer:
            tracer.record_call(
                step="extract", provider="DeepSeek",
                model="deepseek-chat", model_version="v3",
                prompt_length=100, response_length=200,
                duration_ms=1000.0, fallback_used=True,
            )
            tracer.record_call(
                step="search", provider="OpenAI",
                model="gpt-4o", model_version="2024",
                prompt_length=50, response_length=100,
                duration_ms=500.0,
            )

        summary = tracer.get_summary()
        assert summary["total_calls"] == 2
        assert "extract" in summary["steps"]
        assert summary["fallbacks_used"] == 1
        assert summary["duration_ms"] == 1500.0


class TestDetectSovereignty:
    """Tests for auto-detection of sovereignty settings."""

    def test_local_provider(self):
        env = {"DEFAULT_PROVIDER": "ollama", "OLLAMA_MODEL": "qwen3.6:latest", "FALLBACK_PROVIDERS": ""}
        with patch.dict(os.environ, env, clear=False):
            with PipelineTracer(auto_save=False) as tracer:
                pass
        assert tracer.sovereignty.local_model_used is True
        assert tracer.sovereignty.data_sent_overseas is False
        assert tracer.sovereignty.local_model_name == "qwen3.6:latest"

    def test_cloud_provider_deepseek(self):
        env = {"DEFAULT_PROVIDER": "deepseek", "FALLBACK_PROVIDERS": ""}
        with patch.dict(os.environ, env, clear=False):
            with PipelineTracer(auto_save=False) as tracer:
                pass
        assert tracer.sovereignty.data_sent_overseas is True
        assert "China" in tracer.sovereignty.countries_involved
        assert "DeepSeek" in tracer.sovereignty.cloud_providers_used

    def test_fallback_providers_detected(self):
        env = {
            "DEFAULT_PROVIDER": "ollama",
            "OLLAMA_MODEL": "qwen3.6",
            "FALLBACK_PROVIDERS": "deepseek,groq",
        }
        with patch.dict(os.environ, env, clear=False):
            with PipelineTracer(auto_save=False) as tracer:
                pass
        # Local primary but cloud fallbacks detected
        assert tracer.sovereignty.local_model_used is True
        assert "China" in tracer.sovereignty.countries_involved
        assert "United States" in tracer.sovereignty.countries_involved


class TestTracePipelineContextManager:
    """Tests for the trace_pipeline convenience function."""

    def test_basic_usage(self):
        with tempfile.TemporaryDirectory() as tmp:
            with trace_pipeline(
                "CM Test", ["D"], output_dir=Path(tmp),
            ) as tracer:
                tracer.record_call(
                    step="report", provider="Anthropic",
                    model="claude-3", model_version="opus",
                    prompt_length=1000, response_length=3000,
                    duration_ms=5000.0,
                )

            json_files = list(Path(tmp).glob("prisma_traice_*.json"))
            assert len(json_files) == 1

    def test_tracer_accessible_during_context(self):
        with trace_pipeline("Access Test", auto_save=False) as tracer:
            assert get_tracer() is tracer
        assert get_tracer() is None
