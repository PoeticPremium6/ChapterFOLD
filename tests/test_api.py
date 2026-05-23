from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_settings_defaults_endpoint():
    response = client.get("/settings/defaults")
    assert response.status_code == 200
    data = response.json()
    assert data["signature_size"] == 16
    assert data["generate_clean_pdf"] is True


def test_validate_job_accepts_settings_json():
    response = client.post(
        "/jobs/validate",
        data={"settings_json": json.dumps({"variant": "standard", "export_markdown": True})},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["settings"]["export_markdown"] is True


def test_upload_rejects_non_epub():
    response = client.post(
        "/jobs",
        files={"epub": ("book.txt", b"not an epub", "text/plain")},
        data={"dry_run": "true"},
    )
    assert response.status_code == 400
    assert ".epub" in response.json()["detail"]


def test_upload_dry_run_accepts_epub_extension():
    response = client.post(
        "/jobs",
        files={"epub": ("sample.epub", b"synthetic placeholder", "application/epub+zip")},
        data={"dry_run": "true"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["dry_run"] is True
    assert data["input_filename"] == "sample.epub"
