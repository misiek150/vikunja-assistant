import logging
import logging.handlers
import queue
import sys
from datetime import UTC, datetime
from typing import Any, override

import httpx

from assistant.config import LogMode, Settings

_STANDARD_ATTRS = frozenset(
    logging.LogRecord("", 0, "", 0, "", None, None).__dict__
) | {"message", "asctime", "taskName"}

_CLEF_LEVELS = {
    logging.DEBUG: "Debug",
    logging.INFO: "Information",
    logging.WARNING: "Warning",
    logging.ERROR: "Error",
    logging.CRITICAL: "Fatal",
}


class SeqHandler(logging.Handler):
    """Posts records to Seq using the CLEF raw ingestion endpoint."""

    def __init__(self, url: str, api_key: str | None) -> None:
        super().__init__()
        headers = {"Content-Type": "application/vnd.serilog.clef"}
        if api_key:
            headers["X-Seq-ApiKey"] = api_key
        self._client = httpx.Client(
            base_url=url.rstrip("/"), headers=headers, timeout=5.0
        )

    @override
    def emit(self, record: logging.LogRecord) -> None:
        event: dict[str, Any] = {
            "@t": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "@m": record.getMessage(),
            "@l": _CLEF_LEVELS.get(record.levelno, "Information"),
            "SourceContext": record.name,
        }
        if record.exc_info:
            event["@x"] = logging.Formatter().formatException(record.exc_info)
        for key, value in record.__dict__.items():
            if key not in _STANDARD_ATTRS:
                event[key] = value
        try:
            import json

            self._client.post(
                "/api/events/raw?clef", content=json.dumps(event, default=str)
            ).raise_for_status()
        except Exception:  # noqa: BLE001 - logging must never raise
            self.handleError(record)

    @override
    def close(self) -> None:
        self._client.close()
        super().close()


def configure_logging(settings: Settings) -> None:
    root = logging.getLogger()
    root.setLevel(settings.log_level.upper())
    root.handlers.clear()

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)-8s %(name)s: %(message)s")
    )
    root.addHandler(console)

    if settings.log_mode is LogMode.SEQ:
        assert settings.seq_url is not None
        api_key = settings.seq_api_key.get_secret_value() if settings.seq_api_key else None
        log_queue: queue.Queue[logging.LogRecord] = queue.Queue()
        listener = logging.handlers.QueueListener(
            log_queue, SeqHandler(settings.seq_url, api_key), respect_handler_level=True
        )
        listener.start()
        root.addHandler(logging.handlers.QueueHandler(log_queue))
        import atexit

        atexit.register(listener.stop)

    logging.getLogger("httpx").setLevel(logging.WARNING)
