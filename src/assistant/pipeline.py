import logging
from dataclasses import dataclass

from assistant.analyzer import ScreenshotAnalyzer
from assistant.errors import DomainError
from assistant.mapper import TaskMapper
from assistant.screenshots import ScreenshotSource
from assistant.vikunja import VikunjaClient

_log = logging.getLogger(__name__)

_FALLBACK_LABEL = "???"


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

                # Retrieve Vikunja label IDs upfront without caching across runs
                label_map = self._get_label_map()

                requests = [self._mapper.to_request(t) for t in extraction.tasks]
                for req in requests:
                    resolved_label_ids = self._resolve_label_ids(req.labels, label_map)
                    if dry_run:
                        _log.info(
                            "[dry-run] Would create task: %s (due=%s, start=%s, end=%s, labels=%s, label_ids=%s)",
                            req.title,
                            req.due_date,
                            req.start_date,
                            req.end_date,
                            req.labels,
                            resolved_label_ids,
                        )
                    else:
                        created = self._vikunja.create_task(req)
                        result.tasks_created += 1
                        if resolved_label_ids:
                            self._vikunja.add_labels_to_task(created.id, resolved_label_ids)
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

    def _get_label_map(self) -> dict[str, int]:
        """Fetch labels from Vikunja and build a title->id mapping (case-insensitive fallback)."""
        labels = self._vikunja.get_labels()
        mapping: dict[str, int] = {}
        for lbl in labels:
            mapping[lbl.title] = lbl.id
            mapping.setdefault(lbl.title.lower(), lbl.id)
        return mapping

    def _resolve_label_ids(self, label_names: list[str], label_map: dict[str, int]) -> list[int]:
        """Resolve label names to IDs. Unmatched labels map to the fallback '???' label ID."""
        fallback_id = label_map.get(_FALLBACK_LABEL)
        resolved_ids: list[int] = []

        for name in label_names:
            lid = label_map.get(name) or label_map.get(name.lower())
            if lid is not None:
                if lid not in resolved_ids:
                    resolved_ids.append(lid)
            else:
                _log.warning("Label '%s' not found in Vikunja, falling back to '%s'", name, _FALLBACK_LABEL)
                if fallback_id is not None and fallback_id not in resolved_ids:
                    resolved_ids.append(fallback_id)

        return resolved_ids
