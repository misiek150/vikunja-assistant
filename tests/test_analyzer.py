import json
import logging
from pathlib import Path
from types import SimpleNamespace

import pytest

from assistant.analyzer import GeminiScreenshotAnalyzer, MockScreenshotAnalyzer, load_system_prompt
from assistant.models import Screenshot


def test_gemini_analyzer_logs_progress(monkeypatch, caplog, tmp_path: Path):
    request_options: dict[str, object] = {}

    class FakeInteractions:
        def create(self, **kwargs):
            request_options.update(kwargs)
            return SimpleNamespace(output_text='{"tasks": []}')

    class FakeClient:
        def __init__(self, api_key: str):
            self.interactions = FakeInteractions()

    monkeypatch.setattr("assistant.analyzer.genai.Client", FakeClient)
    caplog.set_level(logging.INFO, logger="assistant.analyzer")

    image_path = tmp_path / "notice.png"
    image_path.write_bytes(b"dummy")
    analyzer = GeminiScreenshotAnalyzer(api_key="test-key", model="test-model")

    result = analyzer.analyze(Screenshot(path=image_path, mime_type="image/png"))

    assert result.tasks == []
    assert caplog.messages == [
        "Preparing screenshot notice.png for Gemini",
        "Sending screenshot notice.png to Gemini model test-model (timeout 120 seconds)",
        "Gemini response received for notice.png; extracting tasks",
        "Extracted 0 task(s) from notice.png",
    ]
    assert request_options["timeout"] == 120.0


def test_load_system_prompt_from_default_file():
    prompt = load_system_prompt()
    assert "Inso School App Screenshot Extractor" in prompt
    assert "Lizbona" in prompt
    assert "Ateny" in prompt
    assert "Przypięte" in prompt


def test_load_system_prompt_missing_fallback(tmp_path: Path):
    missing_file = tmp_path / "nonexistent.md"
    prompt = load_system_prompt(missing_file)
    assert "You are an assistant that analyzes screenshots" in prompt


def test_mock_screenshot_analyzer_fallback(tmp_path: Path):
    img_path = tmp_path / "notice.png"
    img_path.write_bytes(b"dummy")

    analyzer = MockScreenshotAnalyzer(responses_dir=None)
    result = analyzer.analyze(Screenshot(path=img_path, mime_type="image/png"))

    assert len(result.tasks) == 1
    task = result.tasks[0]
    assert "🎒 Mock task from notice.png" in task.title
    assert task.labels == ["Lizbona", "wyprawka"]


def test_mock_screenshot_analyzer_from_file(tmp_path: Path):
    img_path = tmp_path / "kindergarten.png"
    img_path.write_bytes(b"dummy")

    mock_json_dir = tmp_path / "mock_json"
    mock_json_dir.mkdir()
    canned_file = mock_json_dir / "kindergarten.json"
    canned_payload = {
        "tasks": [
            {
                "title": "💸️ Wpłata na radę rodziców",
                "description": "Kwota: 100 zł",
                "due_date": "2026-10-31T20:00:00Z",
                "start_date": None,
                "end_date": None,
                "labels": ["Lizbona", "opłaty"],
            }
        ]
    }
    canned_file.write_text(json.dumps(canned_payload))

    analyzer = MockScreenshotAnalyzer(responses_dir=mock_json_dir)
    result = analyzer.analyze(Screenshot(path=img_path, mime_type="image/png"))

    assert len(result.tasks) == 1
    assert result.tasks[0].title == "💸️ Wpłata na radę rodziców"
    assert result.tasks[0].labels == ["Lizbona", "opłaty"]
