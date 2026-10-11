from functools import cached_property

from assistant.analyzer import GeminiScreenshotAnalyzer, MockScreenshotAnalyzer, ScreenshotAnalyzer
from assistant.config import Settings
from assistant.errors import ConfigurationError
from assistant.mapper import TaskMapper
from assistant.pipeline import Pipeline
from assistant.screenshots import FolderScreenshotSource, ScreenshotSource
from assistant.vikunja import HttpVikunjaClient, VikunjaClient


class Container:
    """Lazily wires dependencies so partial stages only need their own config."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    @cached_property
    def source(self) -> ScreenshotSource:
        s = self._settings
        return FolderScreenshotSource(s.screenshots_dir, s.effective_processed_dir)

    @cached_property
    def analyzer(self) -> ScreenshotAnalyzer:
        s = self._settings
        if s.mock_mode:
            return MockScreenshotAnalyzer(s.mock_responses_dir)
        if s.gemini_api_key is None:
            raise ConfigurationError("GEMINI_API_KEY is required when MOCK_MODE is off")
        return GeminiScreenshotAnalyzer(s.gemini_api_key.get_secret_value(), s.gemini_model)

    @cached_property
    def mapper(self) -> TaskMapper:
        return TaskMapper(self._settings.vikunja_project_id)

    @cached_property
    def vikunja(self) -> VikunjaClient:
        s = self._settings
        if s.vikunja_api_token is None:
            raise ConfigurationError("VIKUNJA_API_TOKEN is required")
        return HttpVikunjaClient(s.vikunja_base_url, s.vikunja_api_token.get_secret_value())

    @cached_property
    def pipeline(self) -> Pipeline:
        return Pipeline(self.source, self.analyzer, self.mapper, self.vikunja)
