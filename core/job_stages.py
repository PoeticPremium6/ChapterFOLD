from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class JobStageSpec:
    value: str
    label: str
    terminal: bool = False


JOB_STAGES: tuple[JobStageSpec, ...] = (
    JobStageSpec("created", "Created"),
    JobStageSpec("queued", "Queued"),
    JobStageSpec("validating", "Validating input"),
    JobStageSpec("preparing_workspace", "Preparing workspace"),
    JobStageSpec("extracting", "Extracting document"),
    JobStageSpec("cleaning", "Cleaning text"),
    JobStageSpec("rendering", "Rendering book"),
    JobStageSpec("imposing", "Creating imposed PDF"),
    JobStageSpec("saving_outputs", "Saving outputs"),
    JobStageSpec("complete", "Complete", terminal=True),
    JobStageSpec("failed", "Failed", terminal=True),
)

VALID_JOB_STAGES = {stage.value for stage in JOB_STAGES}
TERMINAL_JOB_STAGES = {stage.value for stage in JOB_STAGES if stage.terminal}


STAGE_ALIASES = {
    "validate": "validating",
    "validation": "validating",
    "run_processing": "rendering",
    "processing": "rendering",
    "done": "complete",
    "success": "complete",
    "error": "failed",
    "failure": "failed",
}


def normalize_job_stage(stage: str | None, *, success: bool | None = None) -> str:
    """Normalize internal/legacy stage names for web job tracking."""

    if success is True:
        return "complete"
    if success is False and not stage:
        return "failed"

    value = (stage or "created").strip().lower().replace(" ", "_").replace("-", "_")
    value = STAGE_ALIASES.get(value, value)

    if value in VALID_JOB_STAGES:
        return value

    return "failed" if success is False else "rendering"


def job_stage_catalog() -> list[dict[str, object]]:
    return [
        {
            "value": stage.value,
            "label": stage.label,
            "terminal": stage.terminal,
        }
        for stage in JOB_STAGES
    ]


def is_terminal_stage(stage: str | None) -> bool:
    return normalize_job_stage(stage) in TERMINAL_JOB_STAGES
