from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from core.job import run_chapterfold_job
from core.schemas import ChapterfoldJobInput, ChapterfoldSettings

app = FastAPI(
    title="ChapterFOLD API Prototype",
    version="0.1.0",
    description="Prototype API wrapper around the ChapterFOLD processing engine.",
)


def _settings_from_json(settings_json: str | None) -> ChapterfoldSettings:
    if not settings_json:
        return ChapterfoldSettings()
    try:
        data = json.loads(settings_json)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid settings_json: {exc}") from exc
    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail="settings_json must be a JSON object.")
    try:
        return ChapterfoldSettings.from_dict(data)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _result_to_dict(result: Any) -> dict[str, Any]:
    if hasattr(result, "to_dict"):
        return result.to_dict()
    if hasattr(result, "__dict__"):
        data = dict(result.__dict__)
        if "output_files" in data:
            data["output_files"] = [str(p) for p in data["output_files"]]
        return data
    return {"success": False, "error": "Unsupported result object returned by core runner."}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "chapterfold-api"}


@app.get("/settings/defaults")
def settings_defaults() -> dict[str, Any]:
    return ChapterfoldSettings().to_dict()


@app.post("/jobs/validate")
def validate_job(settings_json: str | None = Form(default=None)) -> dict[str, Any]:
    """Validate settings without requiring an EPUB upload."""
    settings = _settings_from_json(settings_json)
    settings.validate()
    return {"success": True, "settings": settings.to_dict()}


@app.post("/jobs")
async def create_job(
    epub: UploadFile = File(...),
    settings_json: str | None = Form(default=None),
    dry_run: bool = Form(default=False),
) -> JSONResponse:
    """Run a single EPUB conversion job.

    This is intentionally simple for now. It writes the uploaded EPUB to a temp
    directory, delegates to the UI-independent core runner, and returns a JSON
    result. A later production version should replace this with persistent
    storage, auth, background jobs, and signed download URLs.
    """

    if not epub.filename or not epub.filename.lower().endswith(".epub"):
        raise HTTPException(status_code=400, detail="Uploaded file must end with .epub")

    settings = _settings_from_json(settings_json)
    settings.validate()

    with tempfile.TemporaryDirectory(prefix="chapterfold_api_") as temp_dir_raw:
        temp_dir = Path(temp_dir_raw)
        input_path = temp_dir / Path(epub.filename).name
        output_dir = temp_dir / "output"
        input_path.write_bytes(await epub.read())

        job = ChapterfoldJobInput(input_epub=input_path, output_dir=output_dir, settings=settings)

        if dry_run:
            # Validate the upload and settings but do not call conversion.
            job.validate()
            return JSONResponse(
                {
                    "success": True,
                    "dry_run": True,
                    "input_filename": input_path.name,
                    "settings": settings.to_dict(),
                }
            )

        result = run_chapterfold_job(job)
        payload = _result_to_dict(result)
        # The prototype temp directory is deleted after response, so do not claim
        # these output paths are persistent download URLs yet.
        payload["prototype_note"] = (
            "Outputs are generated in temporary storage in this prototype. "
            "Add persistent storage/background jobs before production use."
        )
        status_code = 200 if payload.get("success") else 500
        return JSONResponse(payload, status_code=status_code)
