from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class Screenshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    path: Path
    mime_type: str


class ExtractedTask(BaseModel):
    """A task found in a screenshot (Gemini structured output)."""

    title: str = Field(description="Short actionable task title.")
    description: str | None = Field(default=None, description="Extra details or context.")
    due_date: datetime | None = Field(
        default=None, description="Due date/time in ISO 8601, if visible."
    )
    priority: int | None = Field(
        default=None, ge=1, le=5, description="1 (low) to 5 (urgent), if it can be inferred."
    )


class ScreenshotExtraction(BaseModel):
    tasks: list[ExtractedTask] = Field(default_factory=list)


class VikunjaTaskRequest(BaseModel):
    """Body of `PUT /projects/{id}/tasks`."""

    project_id: int = Field(exclude=True)
    title: str
    description: str | None = None
    due_date: datetime | None = None
    priority: int | None = None


class CreatedTask(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    title: str
