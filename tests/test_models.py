from datetime import datetime, timezone

from assistant.models import (
    CreatedTask,
    ExtractedTask,
    ScreenshotExtraction,
    VikunjaLabel,
    VikunjaTaskRequest,
)


def test_extracted_task_schema_excludes_priority():
    schema = ScreenshotExtraction.model_json_schema()
    props = schema["$defs"]["ExtractedTask"]["properties"]
    assert "priority" not in props
    assert "start_date" in props
    assert "end_date" in props
    assert "due_date" in props
    assert "labels" in props


def test_extracted_task_defaults():
    task = ExtractedTask(title="💸️ Opłata")
    assert task.title == "💸️ Opłata"
    assert task.description is None
    assert task.due_date is None
    assert task.start_date is None
    assert task.end_date is None
    assert task.labels == []


def test_vikunja_task_request_serialization_excludes_internal_fields():
    now = datetime(2026, 10, 15, 8, 0, 0, tzinfo=timezone.utc)
    req = VikunjaTaskRequest(
        project_id=42,
        title="🎒 Przynieść kalosze",
        description="Rozmiar 28",
        due_date=now,
        start_date=now,
        end_date=now,
        labels=["Lizbona", "wyprawka"],
    )

    dumped = req.model_dump(mode="json", exclude_none=True)

    # project_id and labels must be excluded from the PUT body
    assert "project_id" not in dumped
    assert "labels" not in dumped
    assert "priority" not in dumped

    # Direct Vikunja task fields must be present
    assert dumped["title"] == "🎒 Przynieść kalosze"
    assert dumped["description"] == "Rozmiar 28"
    assert dumped["due_date"] == "2026-10-15T08:00:00Z"
    assert dumped["start_date"] == "2026-10-15T08:00:00Z"
    assert dumped["end_date"] == "2026-10-15T08:00:00Z"


def test_created_task_and_label_parsing():
    task = CreatedTask.model_validate({"id": 101, "title": "Test", "extra_prop": "ignored"})
    assert task.id == 101
    assert task.title == "Test"

    lbl = VikunjaLabel.model_validate({"id": 7, "title": "Lizbona", "color": "#ffffff"})
    assert lbl.id == 7
    assert lbl.title == "Lizbona"
