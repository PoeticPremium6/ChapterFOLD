from __future__ import annotations

from core.engine_errors import friendly_error_from_exception


def test_friendly_error_for_missing_file():
    error = friendly_error_from_exception(FileNotFoundError("missing.epub"))

    assert error.code == "input_not_found"
    assert "could not be found" in error.message


def test_friendly_error_for_unsupported_file():
    error = friendly_error_from_exception(ValueError("Unsupported input file type: .exe"))

    assert error.code == "unsupported_file_type"


def test_friendly_error_for_invalid_signature_size():
    error = friendly_error_from_exception(ValueError("Pages per signature must be a positive multiple of 4"))

    assert error.code == "invalid_signature_size"


def test_friendly_error_fallback():
    error = friendly_error_from_exception(RuntimeError("boom"))

    assert error.code == "conversion_failed"
    assert error.retryable is True
