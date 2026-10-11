import logging
import mimetypes
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import override

from assistant.models import Screenshot

_log = logging.getLogger(__name__)

_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


class ScreenshotSource(ABC):
    @abstractmethod
    def list(self) -> list[Screenshot]: ...

    @abstractmethod
    def mark_processed(self, screenshot: Screenshot) -> None: ...


class FolderScreenshotSource(ScreenshotSource):
    def __init__(self, directory: Path, processed_directory: Path) -> None:
        self._directory = directory
        self._processed = processed_directory

    @override
    def list(self) -> list[Screenshot]:
        if not self._directory.is_dir():
            _log.warning("Screenshots directory %s does not exist", self._directory)
            return []
        files = sorted(
            p for p in self._directory.iterdir()
            if p.is_file() and p.suffix.lower() in _IMAGE_SUFFIXES
        )
        return [
            Screenshot(path=p, mime_type=mimetypes.guess_type(p)[0] or "image/png")
            for p in files
        ]

    @override
    def mark_processed(self, screenshot: Screenshot) -> None:
        self._processed.mkdir(parents=True, exist_ok=True)
        target = self._processed / screenshot.path.name
        shutil.move(screenshot.path, target)
        _log.info("Moved %s to %s", screenshot.path.name, target)
