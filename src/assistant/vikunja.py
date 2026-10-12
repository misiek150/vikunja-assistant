import logging
from abc import ABC, abstractmethod
from typing import override

import httpx

from assistant.errors import VikunjaError
from assistant.models import CreatedTask, VikunjaLabel, VikunjaTaskRequest

_log = logging.getLogger(__name__)


class VikunjaClient(ABC):
    @abstractmethod
    def get_labels(self) -> list[VikunjaLabel]: ...

    @abstractmethod
    def create_task(self, request: VikunjaTaskRequest) -> CreatedTask: ...

    @abstractmethod
    def add_labels_to_task(self, task_id: int, label_ids: list[int]) -> None: ...


class HttpVikunjaClient(VikunjaClient):
    def __init__(self, base_url: str, token: str) -> None:
        self._http = httpx.Client(
            base_url=f"{base_url.rstrip('/')}/api/v1",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30.0,
        )

    @override
    def get_labels(self) -> list[VikunjaLabel]:
        try:
            response = self._http.get("/labels", params={"per_page": 500})
            response.raise_for_status()
            return [VikunjaLabel.model_validate(item) for item in response.json()]
        except httpx.HTTPStatusError as exc:
            raise VikunjaError(
                f"Vikunja get_labels returned {exc.response.status_code}: {exc.response.text}"
            ) from exc
        except httpx.HTTPError as exc:
            raise VikunjaError(f"Vikunja get_labels request failed: {exc}") from exc

    @override
    def create_task(self, request: VikunjaTaskRequest) -> CreatedTask:
        # Vikunja uses PUT for create.
        try:
            response = self._http.put(
                f"/projects/{request.project_id}/tasks",
                json=request.model_dump(mode="json", exclude_none=True),
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise VikunjaError(
                f"Vikunja returned {exc.response.status_code}: {exc.response.text}"
            ) from exc
        except httpx.HTTPError as exc:
            raise VikunjaError(f"Vikunja request failed: {exc}") from exc
        created = CreatedTask.model_validate(response.json())
        _log.info("Created Vikunja task %s", created.id, extra={"TaskId": created.id})
        return created

    @override
    def add_labels_to_task(self, task_id: int, label_ids: list[int]) -> None:
        if not label_ids:
            return
        try:
            response = self._http.post(
                f"/tasks/{task_id}/labels/bulk",
                json={"labels": [{"id": lid} for lid in label_ids]},
            )
            response.raise_for_status()
            _log.info("Assigned label IDs %s to task %s", label_ids, task_id)
        except httpx.HTTPStatusError as exc:
            raise VikunjaError(
                f"Vikunja add_labels_to_task returned {exc.response.status_code}: {exc.response.text}"
            ) from exc
        except httpx.HTTPError as exc:
            raise VikunjaError(f"Vikunja add_labels_to_task failed: {exc}") from exc
