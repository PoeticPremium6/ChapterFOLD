from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UserFacingError:
    code: str
    message: str
    detail: str | None = None
    retryable: bool = False


def friendly_error_from_exception(exc: BaseException) -> UserFacingError:
    """Convert internal exceptions into UI-safe user-facing errors."""

    text = str(exc)
    lower = text.lower()

    if isinstance(exc, FileNotFoundError):
        return UserFacingError(
            code="input_not_found",
            message="The selected input file could not be found.",
            detail=text,
            retryable=False,
        )

    if isinstance(exc, PermissionError):
        return UserFacingError(
            code="permission_denied",
            message="ChapterFOLD could not read or write one of the selected files or folders.",
            detail="Check that the file is not open elsewhere and that the output folder is writable.",
            retryable=True,
        )

    if "unsupported input file type" in lower or "unsupported input type" in lower:
        return UserFacingError(
            code="unsupported_file_type",
            message="This file type is not supported yet.",
            detail=text,
            retryable=False,
        )

    if "too large" in lower or "maximum allowed size" in lower:
        return UserFacingError(
            code="file_too_large",
            message="The input file is larger than the current limit.",
            detail=text,
            retryable=False,
        )

    if "encrypted" in lower or "password" in lower:
        return UserFacingError(
            code="encrypted_or_password_protected",
            message="This file appears to be encrypted or password protected.",
            detail="Please try an unlocked EPUB/PDF file.",
            retryable=False,
        )

    if "no pages" in lower:
        return UserFacingError(
            code="empty_document",
            message="The input document does not appear to contain any pages.",
            detail=text,
            retryable=False,
        )

    if "binding direction" in lower:
        return UserFacingError(
            code="invalid_binding_direction",
            message="The selected binding direction is invalid.",
            detail="Choose left-to-right or right-to-left binding.",
            retryable=False,
        )

    if "signature" in lower and ("multiple of 4" in lower or "divisible by 4" in lower):
        return UserFacingError(
            code="invalid_signature_size",
            message="The signature size must be a positive multiple of 4.",
            detail=text,
            retryable=False,
        )

    return UserFacingError(
        code="conversion_failed",
        message="The conversion failed. Please try another file or different settings.",
        detail=text or exc.__class__.__name__,
        retryable=True,
    )
