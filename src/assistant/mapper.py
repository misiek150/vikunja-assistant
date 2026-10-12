from assistant.models import ExtractedTask, VikunjaTaskRequest


class TaskMapper:
    def __init__(self, project_id: int) -> None:
        self._project_id = project_id

    def to_request(self, task: ExtractedTask) -> VikunjaTaskRequest:
        return VikunjaTaskRequest(
            project_id=self._project_id,
            title=task.title.strip(),
            description=task.description,
            due_date=task.due_date,
            start_date=task.start_date,
            end_date=task.end_date,
            labels=task.labels,
        )
