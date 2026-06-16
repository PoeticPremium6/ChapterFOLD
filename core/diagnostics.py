"""Diagnostic report helpers for ChapterFOLD.

The goal is to make user bug reports actionable without collecting book content.
The report intentionally avoids reading or embedding EPUB/PDF/DOCX contents.
"""
from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
import importlib.metadata
import os
from pathlib import Path
import platform
import sys
import traceback
from typing import Any, Mapping


PACKAGE_CHECKS = [
    ("PySide6", "PySide6", "PySide6"),
    ("ebooklib", "ebooklib", "EbookLib"),
    ("weasyprint", "weasyprint", "weasyprint"),
    ("pypdf", "pypdf", "pypdf"),
    ("python-docx", "docx", "python-docx"),
    ("beautifulsoup4", "bs4", "beautifulsoup4"),
    ("lxml", "lxml", "lxml"),
]


def _package_version(import_name: str, distribution_name: str | None = None) -> str:
    """Return useful package status in source and frozen/PyInstaller builds.

    PyInstaller builds may not include distribution metadata even when a module
    is bundled and importable. Prefer importability, then include version
    metadata when available.
    """

    distribution_name = distribution_name or import_name

    try:
        __import__(import_name)
    except Exception as exc:
        return f"not importable ({exc.__class__.__name__}: {exc})"

    try:
        version = importlib.metadata.version(distribution_name)
        return f"OK {version}"
    except importlib.metadata.PackageNotFoundError:
        if getattr(sys, "frozen", False):
            return "OK bundled"
        return "OK importable, version metadata unavailable"
    except Exception as exc:  # pragma: no cover - defensive only
        return f"OK importable, version check failed ({exc.__class__.__name__})"


def get_environment_info() -> dict[str, Any]:
    """Return basic runtime information for support/debugging."""
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "python": sys.version.replace("\n", " "),
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "cwd": str(Path.cwd()),
        "virtual_env": os.environ.get("VIRTUAL_ENV", ""),
        "packages": {label: _package_version(import_name, distribution_name) for label, import_name, distribution_name in PACKAGE_CHECKS},
    }


def sanitize_path(value: str | Path | None) -> str:
    """Return filename-only path info so reports do not leak full user directories."""
    if value is None:
        return ""
    try:
        return Path(value).name
    except Exception:
        return str(value)


def _settings_to_dict(settings: Any) -> dict[str, Any]:
    if settings is None:
        return {}
    if is_dataclass(settings):
        return asdict(settings)
    if isinstance(settings, Mapping):
        return dict(settings)
    if hasattr(settings, "__dict__"):
        return {k: v for k, v in vars(settings).items() if not k.startswith("_")}
    return {"settings_repr": repr(settings)}


def format_exception(exc: BaseException | None = None) -> str:
    """Format an exception or the current exception traceback."""
    if exc is not None:
        return "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    current = sys.exc_info()
    if current[0] is None:
        return ""
    return "".join(traceback.format_exception(*current))


def build_diagnostic_report(
    *,
    app_version: str = "unknown",
    stage: str = "manual",
    input_path: str | Path | None = None,
    output_dir: str | Path | None = None,
    settings: Any = None,
    error: BaseException | str | None = None,
    extra: Mapping[str, Any] | None = None,
) -> str:
    """Build a plain-text diagnostic report suitable for copy/paste bug reports.

    This does not inspect document contents. It only reports filenames, selected
    settings, environment details, and optional tracebacks.
    """
    env = get_environment_info()
    settings_dict = _settings_to_dict(settings)

    lines: list[str] = []
    lines.append("ChapterFOLD Diagnostic Report")
    lines.append("=" * 31)
    lines.append(f"App version: {app_version}")
    lines.append(f"Stage: {stage}")
    lines.append(f"Timestamp UTC: {env['timestamp_utc']}")
    lines.append("")
    lines.append("Document")
    lines.append("--------")
    lines.append(f"Input filename: {sanitize_path(input_path)}")
    lines.append(f"Output folder name: {sanitize_path(output_dir)}")
    lines.append("")
    lines.append("Environment")
    lines.append("-----------")
    lines.append(f"Platform: {env['platform']}")
    lines.append(f"Python: {env['python']}")
    lines.append(f"Python executable: {env['python_executable']}")
    lines.append(f"Virtual environment: {env['virtual_env']}")
    lines.append(f"Working directory: {env['cwd']}")
    lines.append("")
    lines.append("Packages")
    lines.append("--------")
    for name, version in env["packages"].items():
        lines.append(f"{name}: {version}")
    lines.append("")
    lines.append("Settings")
    lines.append("--------")
    if settings_dict:
        for key in sorted(settings_dict):
            value = settings_dict[key]
            if isinstance(value, Path):
                value = sanitize_path(value)
            lines.append(f"{key}: {value}")
    else:
        lines.append("No settings captured.")

    if extra:
        lines.append("")
        lines.append("Extra")
        lines.append("-----")
        for key in sorted(extra):
            lines.append(f"{key}: {extra[key]}")

    if error:
        lines.append("")
        lines.append("Error")
        lines.append("-----")
        if isinstance(error, BaseException):
            lines.append(format_exception(error).strip())
        else:
            lines.append(str(error))

    lines.append("")
    lines.append("Privacy note: this report records filenames/settings/environment only; it does not include book contents.")
    return "\n".join(lines).rstrip() + "\n"

# --- Frozen/package diagnostics compatibility guard ---
# PyInstaller/frozen apps may bundle importable modules without preserving
# importlib.metadata distribution records. Diagnostics should therefore prefer
# module importability over package metadata.

_CHAPTERFOLD_PACKAGE_CHECKS = (
    ("PySide6", "PySide6", "PySide6"),
    ("ebooklib", "ebooklib", "EbookLib"),
    ("weasyprint", "weasyprint", "weasyprint"),
    ("pypdf", "pypdf", "pypdf"),
    ("python-docx", "docx", "python-docx"),
    ("beautifulsoup4", "bs4", "beautifulsoup4"),
    ("lxml", "lxml", "lxml"),
)


def _chapterfold_package_status(import_name: str, distribution_name: str | None = None) -> str:
    import sys as _sys
    from importlib import metadata as _metadata

    try:
        module = __import__(import_name)
    except Exception:
        return "not installed"

    try:
        return _metadata.version(distribution_name or import_name)
    except _metadata.PackageNotFoundError:
        bundled = bool(getattr(_sys, "frozen", False))
        module_version = getattr(module, "__version__", None)

        if module_version:
            return str(module_version)

        if bundled:
            return "OK bundled"

        return "OK importable, version metadata unavailable"
    except Exception:
        return "OK importable, version metadata unavailable"


_chapterfold_legacy_get_environment_info = get_environment_info


def get_environment_info():
    info = _chapterfold_legacy_get_environment_info()

    package_status = {
        label: _chapterfold_package_status(import_name, distribution_name)
        for label, import_name, distribution_name in _CHAPTERFOLD_PACKAGE_CHECKS
    }

    if isinstance(info, dict):
        info["packages"] = package_status
    elif hasattr(info, "packages"):
        setattr(info, "packages", package_status)

    return info

