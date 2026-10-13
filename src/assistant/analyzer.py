import base64
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import override

from google import genai
from pydantic import ValidationError

from assistant.errors import AnalysisError
from assistant.models import ExtractedTask, Screenshot, ScreenshotExtraction

_log = logging.getLogger(__name__)

_DEFAULT_PROMPT_PATH = Path(__file__).parent / "prompts" / "inso_extractor.md"


def load_system_prompt(prompt_path: Path | None = None) -> str:
    path = prompt_path or _DEFAULT_PROMPT_PATH
    if path.is_file():
        return path.read_text(encoding="utf-8")
    return (
        "You are an assistant that analyzes screenshots from school and kindergarten apps (such as Inso) "
        "to extract actionable tasks."
    )


class ScreenshotAnalyzer(ABC):
    @abstractmethod
    def analyze(self, screenshot: Screenshot) -> ScreenshotExtraction: ...


class GeminiScreenshotAnalyzer(ScreenshotAnalyzer):
    def __init__(
        self,
        api_key: str,
        model: str,
        system_prompt: str | None = None,
        prompt_path: Path | None = None,
    ) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model
        self._system_prompt = system_prompt or load_system_prompt(prompt_path)

    @override
    def analyze(self, screenshot: Screenshot) -> ScreenshotExtraction:
        _log.info("Preparing screenshot %s for Gemini", screenshot.path.name)
        data = base64.b64encode(screenshot.path.read_bytes()).decode("ascii")
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC (%A)")
        user_prompt = (
            f"Analyze this screenshot from the Inso school app.\n"
            f"Reference date (today): {now_str}.\n"
            f"Extract all actionable tasks according to instructions."
        )
        try:
            _log.info("Sending screenshot %s to Gemini model %s", screenshot.path.name, self._model)
            interaction = self._client.interactions.create(
                model=self._model,
                store=False,
                system_instruction=self._system_prompt,
                input=[
                    {"type": "text", "text": user_prompt},
                    {"type": "image", "data": data, "mime_type": screenshot.mime_type},
                ],
                response_format={
                    "type": "text",
                    "mime_type": "application/json",
                    "schema": ScreenshotExtraction.model_json_schema(),
                },
            )
            _log.info("Gemini response received for %s; extracting tasks", screenshot.path.name)
            extraction = ScreenshotExtraction.model_validate_json(interaction.output_text or "")
            _log.info("Extracted %d task(s) from %s", len(extraction.tasks), screenshot.path.name)
            return extraction
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
                    title=f"🎒 Mock task from {screenshot.path.name}",
                    description="Generated in mock mode.",
                    labels=["Lizbona", "wyprawka"],
                )
            ]
        )
