from pathlib import Path

import httpx
import pytest

from assistant.errors import VikunjaError
from assistant.models import VikunjaTaskRequest
from assistant.vikunja import HttpVikunjaClient


def test_get_labels_success():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/api/v1/labels"
        assert request.headers["Authorization"] == "Bearer test-token"
        return httpx.Response(
            200,
            json=[
                {"id": 1, "title": "Lizbona"},
                {"id": 2, "title": "Ateny"},
                {"id": 99, "title": "???"},
            ],
        )

    transport = httpx.MockTransport(handler)
    client = HttpVikunjaClient("http://vikunja.local", "test-token")
    client._http = httpx.Client(
        base_url="http://vikunja.local/api/v1",
        headers={"Authorization": "Bearer test-token"},
        transport=transport,
    )

    labels = client.get_labels()
    assert len(labels) == 3
    assert labels[0].title == "Lizbona"
    assert labels[2].title == "???"


def test_get_labels_http_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"message": "Internal error"})

    transport = httpx.MockTransport(handler)
    client = HttpVikunjaClient("http://vikunja.local", "test-token")
    client._http = httpx.Client(
        base_url="http://vikunja.local/api/v1",
        headers={"Authorization": "Bearer test-token"},
        transport=transport,
    )

    with pytest.raises(VikunjaError, match="Vikunja get_labels returned 500"):
        client.get_labels()


def test_create_task_success():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "PUT"
        assert request.url.path == "/api/v1/projects/5/tasks"
        body = json_from_request(request)
        assert body["title"] == "💸️ Wycieczka"
        assert "labels" not in body
        return httpx.Response(201, json={"id": 456, "title": body["title"]})

    transport = httpx.MockTransport(handler)
    client = HttpVikunjaClient("http://vikunja.local", "test-token")
    client._http = httpx.Client(
        base_url="http://vikunja.local/api/v1",
        headers={"Authorization": "Bearer test-token"},
        transport=transport,
    )

    req = VikunjaTaskRequest(project_id=5, title="💸️ Wycieczka", labels=["Lizbona"])
    created = client.create_task(req)
    assert created.id == 456
    assert created.title == "💸️ Wycieczka"


def test_add_labels_to_task():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/api/v1/tasks/456/labels/bulk"
        body = json_from_request(request)
        calls.append(body)
        return httpx.Response(200, json={"message": "ok"})

    transport = httpx.MockTransport(handler)
    client = HttpVikunjaClient("http://vikunja.local", "test-token")
    client._http = httpx.Client(
        base_url="http://vikunja.local/api/v1",
        headers={"Authorization": "Bearer test-token"},
        transport=transport,
    )

    client.add_labels_to_task(456, [1, 99])
    assert len(calls) == 1
    assert calls[0] == {"labels": [{"id": 1}, {"id": 99}]}


def json_from_request(request: httpx.Request):
    import json
    return json.loads(request.content.decode("utf-8"))
