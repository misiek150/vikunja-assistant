from pathlib import Path

from assistant.analyzer import ScreenshotAnalyzer
from assistant.mapper import TaskMapper
from assistant.models import (
    CreatedTask,
    ExtractedTask,
    Screenshot,
    ScreenshotExtraction,
    VikunjaLabel,
    VikunjaTaskRequest,
)
from assistant.pipeline import Pipeline
from assistant.screenshots import ScreenshotSource
from assistant.vikunja import VikunjaClient


class DummySource(ScreenshotSource):
    def __init__(self, count: int = 1):
        self._shots = [
            Screenshot(path=Path(f"test_{i}.png"), mime_type="image/png")
            for i in range(count)
        ]
        self.processed: list[Screenshot] = []

    def list(self) -> list[Screenshot]:
        return list(self._shots)

    def mark_processed(self, screenshot: Screenshot) -> None:
        self.processed.append(screenshot)


class DummyAnalyzer(ScreenshotAnalyzer):
    def __init__(self, tasks: list[ExtractedTask]):
        self._tasks = tasks

    def analyze(self, screenshot: Screenshot) -> ScreenshotExtraction:
        return ScreenshotExtraction(tasks=self._tasks)


class RecordingVikunjaClient(VikunjaClient):
    def __init__(self, labels: list[VikunjaLabel] | None = None):
        self.available_labels = labels or [
            VikunjaLabel(id=1, title="Lizbona"),
            VikunjaLabel(id=2, title="Ateny"),
            VikunjaLabel(id=99, title="???"),
        ]
        self.created_tasks: list[VikunjaTaskRequest] = []
        self.assigned_labels: list[tuple[int, list[int]]] = []
        self._next_id = 100

    def get_labels(self) -> list[VikunjaLabel]:
        return list(self.available_labels)

    def create_task(self, request: VikunjaTaskRequest) -> CreatedTask:
        self.created_tasks.append(request)
        task = CreatedTask(id=self._next_id, title=request.title)
        self._next_id += 1
        return task

    def add_labels_to_task(self, task_id: int, label_ids: list[int]) -> None:
        self.assigned_labels.append((task_id, label_ids))


def test_pipeline_dry_run_does_not_mutate():
    source = DummySource(count=1)
    analyzer = DummyAnalyzer(
        tasks=[ExtractedTask(title="💸️ Wycieczka", labels=["Lizbona"])]
    )
    mapper = TaskMapper(project_id=1)
    vikunja = RecordingVikunjaClient()

    pipeline = Pipeline(source, analyzer, mapper, vikunja)
    result = pipeline.run(dry_run=True)

    assert result.processed == 1
    assert result.failed == 0
    assert result.tasks_created == 0
    assert len(vikunja.created_tasks) == 0
    assert len(vikunja.assigned_labels) == 0
    assert len(source.processed) == 0


def test_pipeline_creates_tasks_and_assigns_resolved_labels():
    source = DummySource(count=1)
    analyzer = DummyAnalyzer(
        tasks=[
            ExtractedTask(title="💸️ Task 1", labels=["Lizbona", "unknown_tag"]),
            ExtractedTask(title="🎒 Task 2", labels=["ateny"]),  # case-insensitive match
        ]
    )
    mapper = TaskMapper(project_id=5)
    vikunja = RecordingVikunjaClient()

    pipeline = Pipeline(source, analyzer, mapper, vikunja)
    result = pipeline.run(dry_run=False)

    assert result.processed == 1
    assert result.failed == 0
    assert result.tasks_created == 2
    assert len(source.processed) == 1

    # Task 1: "Lizbona" -> 1, "unknown_tag" -> 99 (fallback "???")
    assert vikunja.assigned_labels[0] == (100, [1, 99])

    # Task 2: "ateny" -> 2
    assert vikunja.assigned_labels[1] == (101, [2])


def test_pipeline_handles_missing_fallback_label_gracefully():
    # When even "???" doesn't exist in Vikunja
    source = DummySource(count=1)
    analyzer = DummyAnalyzer(
        tasks=[ExtractedTask(title="Task", labels=["non_existing"])]
    )
    mapper = TaskMapper(project_id=1)
    vikunja = RecordingVikunjaClient(labels=[VikunjaLabel(id=1, title="Lizbona")])

    pipeline = Pipeline(source, analyzer, mapper, vikunja)
    result = pipeline.run(dry_run=False)

    assert result.processed == 1
    assert result.tasks_created == 1
    # No labels could be matched, so add_labels_to_task is not called with empty
    assert len(vikunja.assigned_labels) == 0
