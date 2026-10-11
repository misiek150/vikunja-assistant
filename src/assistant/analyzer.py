import base64
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import override

from google import genai
from pydantic import ValidationError

from assistant.errors import AnalysisError
from assistant.models import ExtractedTask, Screenshot, ScreenshotExtraction

_log = logging.getLogger(__name__)

_PROMPT = (
    "Extract actionable tasks from this screenshot. "
    "Return only tasks that are clearly present; return an empty list if there are none."
)


class ScreenshotAnalyzer(ABC):
    @abstractmethod
    def analyze(self, screenshot: Screenshot) -> ScreenshotExtraction: ...


class GeminiScreenshotAnalyzer(ScreenshotAnalyzer):
    def __init__(self, api_key: str, model: str) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model

    @override
    def analyze(self, screenshot: Screenshot) -> ScreenshotExtraction:
        data = base64.b64encode(screenshot.path.read_bytes()).decode("ascii")
        try:
            interaction = self._client.interactions.create(
                model=self._model,
                input=[
                    {"type": "text", "text": _PROMPT},
                    {"type": "image", "data": data, "mime_type": screenshot.mime_type},
                ],
                response_format={
                    "type": "text",
                    "mime_type": "application/json",
                    "schema": ScreenshotExtraction.model_json_schema(),
                },
            )
            return ScreenshotExtraction.model_validate_json(interaction.output_text or "")
        except ValidationError as exc:
            raise AnalysisError(f"Invalid Gemini response for {screenshot.path.name}") from exc
        except Exception as exc:
            raise AnalysisError(f"Gemini request failed for {screenshot.path.name}") from exc


class MockScreenshotAnalyzer(ScreenshotAnalyzer):
    """Returns `<image stem>.json` from the mock dir if present, else a canned response."""

    def __init__(self, responses_dir: Path | None) -> None:
        self._dir = responses_dir

    @override
    def analyze(self, screenshot: Screenshot) -> ScreenshotExtraction:
        if self._dir:
            candidate = self._dir / f"{screenshot.path.stem}.json"
            if candidate.is_file():
                _log.debug("Using mock response %s", candidate)
                return ScreenshotExtraction.model_validate_json(candidate.read_text())
        return ScreenshotExtraction(
            tasks=[
                ExtractedTask(
                    title=f"Mock task from {screenshot.path.name}",
                    description="Generated in mock mode.",
                    priority=3,
                )
            ]
        )
