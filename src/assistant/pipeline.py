import logging
from dataclasses import dataclass

from assistant.analyzer import ScreenshotAnalyzer
from assistant.errors import DomainError
from assistant.mapper import TaskMapper
from assistant.screenshots import ScreenshotSource
from assistant.vikunja import VikunjaClient

_log = logging.getLogger(__name__)


@dataclass(slots=True)
class PipelineResult:
    processed: int = 0
    failed: int = 0
    tasks_created: int = 0


class Pipeline:
    def __init__(
        self,
        source: ScreenshotSource,
        analyzer: ScreenshotAnalyzer,
        mapper: TaskMapper,
        vikunja: VikunjaClient,
    ) -> None:
        self._source = source
        self._analyzer = analyzer
        self._mapper = mapper
        self._vikunja = vikunja

    def run(self, *, dry_run: bool = False) -> PipelineResult:
        result = PipelineResult()
        screenshots = self._source.list()
        _log.info("Found %d screenshot(s)", len(screenshots))
        for shot in screenshots:
            try:
                extraction = self._analyzer.analyze(shot)
                requests = [self._mapper.to_request(t) for t in extraction.tasks]
                for req in requests:
                    if dry_run:
                        _log.info("[dry-run] Would create task: %s", req.title)
                    else:
                        self._vikunja.create_task(req)
                        result.tasks_created += 1
                if not dry_run:
                    self._source.mark_processed(shot)
                result.processed += 1
            except DomainError:
                _log.exception("Failed processing %s", shot.path.name)
                result.failed += 1
        _log.info(
            "Done: processed=%d failed=%d tasks_created=%d",
            result.processed, result.failed, result.tasks_created,
        )
        return result
