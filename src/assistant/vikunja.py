import logging
from abc import ABC, abstractmethod
from typing import override

import httpx

from assistant.errors import VikunjaError
from assistant.models import CreatedTask, VikunjaTaskRequest

_log = logging.getLogger(__name__)


class VikunjaClient(ABC):
    @abstractmethod
    def create_task(self, request: VikunjaTaskRequest) -> CreatedTask: ...


class HttpVikunjaClient(VikunjaClient):
    def __init__(self, base_url: str, token: str) -> None:
        self._http = httpx.Client(
            base_url=f"{base_url.rstrip('/')}/api/v1",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30.0,
        )

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
