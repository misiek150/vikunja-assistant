from datetime import datetime, timezone

from assistant.mapper import TaskMapper
from assistant.models import ExtractedTask


def test_task_mapper_maps_all_fields():
    mapper = TaskMapper(project_id=12)
    due = datetime(2026, 10, 20, 8, 0, tzinfo=timezone.utc)
    start = datetime(2026, 10, 19, 8, 0, tzinfo=timezone.utc)
    end = datetime(2026, 10, 21, 15, 0, tzinfo=timezone.utc)

    extracted = ExtractedTask(
        title="  💸️ Zapłacić za wycieczkę  ",
        description="Wpłata 50 zł na konto",
        due_date=due,
        start_date=start,
        end_date=end,
        labels=["Lizbona", "opłaty"],
    )

    req = mapper.to_request(extracted)

    assert req.project_id == 12
    assert req.title == "💸️ Zapłacić za wycieczkę"  # trimmed
    assert req.description == "Wpłata 50 zł na konto"
    assert req.due_date == due
    assert req.start_date == start
    assert req.end_date == end
    assert req.labels == ["Lizbona", "opłaty"]
