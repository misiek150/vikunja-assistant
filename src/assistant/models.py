from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class Screenshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    path: Path
    mime_type: str


class ExtractedTask(BaseModel):
    """A task found in a screenshot (Gemini structured output)."""

    title: str = Field(
        description="Concise, actionable task title in Polish, starting with an appropriate emoji (e.g. 💸️ for payments)."
    )
    description: str | None = Field(
        default=None,
        description="Relevant contextual details (e.g., exact PLN amount, instructions, items to bring).",
    )
    due_date: datetime | None = Field(
        default=None,
        description="Absolute deadline in ISO 8601 format resolved against reference date (default 08:00:00 if no time given).",
    )
    start_date: datetime | None = Field(
        default=None,
        description="Start date/time in ISO 8601 format for activities starting on a specific date.",
    )
    end_date: datetime | None = Field(
        default=None,
        description="End date/time in ISO 8601 format for activities ending on a specific date.",
    )
    labels: list[str] = Field(
        default_factory=list,
        description="Labels including group ('Lizbona', 'Ateny', 'Cała szkoła', '???') and 'Przypięte' for pinned notices.",
    )


class ScreenshotExtraction(BaseModel):
    tasks: list[ExtractedTask] = Field(
        default_factory=list,
        description="List of actionable tasks found in the screenshot. Empty if purely informational.",
    )


class VikunjaTaskRequest(BaseModel):
    """Body of `PUT /projects/{id}/tasks`."""

    project_id: int = Field(exclude=True)
    title: str
    description: str | None = None
    due_date: datetime | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    labels: list[str] = Field(default_factory=list, exclude=True)


class CreatedTask(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    title: str


class VikunjaLabel(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    title: str
