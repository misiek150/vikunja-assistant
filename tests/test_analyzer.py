import json
from pathlib import Path

import pytest

from assistant.analyzer import MockScreenshotAnalyzer, load_system_prompt
from assistant.models import Screenshot


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
