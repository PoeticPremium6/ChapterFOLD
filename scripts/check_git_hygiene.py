#!/usr/bin/env python3
"""Check for files that should not be committed to the ChapterFOLD repo.

Run from the repository root:

    python scripts/check_git_hygiene.py

The script checks staged and unstaged files reported by Git, plus tracked file
sizes. It is deliberately conservative: it warns about virtual environments,
patch backups, generated EPUBs, and very large files.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


MAX_TRACKED_FILE_SIZE_MB = 50

BAD_PATH_PARTS = {
    "site-packages",
    "__pycache__",
    ".pytest_cache",
    ".patch_backups",
    "patch_notes",
    ".venv",
    "venv",
    "env",
    "ENV",
}

BAD_PREFIXES = (
    "ChapterFOLD/",
    ".venv/",
    "venv/",
    "env/",
    "ENV/",
    ".patch_backups/",
    "patch_notes/",
    "tests/fixtures/epubs/generated/",
)

BAD_SUFFIXES = (
    ".pyc",
    ".pyo",
    ".bak",
    ".backup",
    ".orig",
)

BAD_CONTAINS = (
    ".bak_",
    "/site-packages/",
    "\\site-packages\\",
)


def run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def repo_root() -> Path:
    result = run_git(["rev-parse", "--show-toplevel"])
    if result.returncode != 0:
        print("ERROR: This does not look like a Git repository.", file=sys.stderr)
        sys.exit(2)
    return Path(result.stdout.strip()).resolve()


def parse_porcelain_z(output: str) -> list[str]:
    """Parse `git status --porcelain=v1 -z` and return changed paths."""
    if not output:
        return []

    raw = output.split("\0")
    paths: list[str] = []
    i = 0
    while i < len(raw):
        record = raw[i]
        if not record:
            i += 1
            continue

        status = record[:2]
        path = record[3:] if len(record) > 3 else ""

        if status.startswith("R") or status.startswith("C"):
            if path:
                paths.append(path)
            i += 2
        else:
            if path:
                paths.append(path)
            i += 1

    return paths


def git_status_paths() -> list[str]:
    result = run_git(["status", "--porcelain=v1", "-z"])
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        sys.exit(result.returncode)
    return parse_porcelain_z(result.stdout)


def tracked_files() -> list[str]:
    result = run_git(["ls-files", "-z"])
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        sys.exit(result.returncode)
    return [p for p in result.stdout.split("\0") if p]


def is_bad_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    parts = set(normalized.split("/"))

    if any(normalized.startswith(prefix) for prefix in BAD_PREFIXES):
        return True
    if any(part in parts for part in BAD_PATH_PARTS):
        return True
    if any(normalized.endswith(suffix) for suffix in BAD_SUFFIXES):
        return True
    if any(fragment in normalized for fragment in BAD_CONTAINS):
        return True
    if normalized.startswith("tests/fixtures/epubs/") and normalized.endswith(".epub"):
        return True

    return False


def file_size_mb(root: Path, path: str) -> float:
    full_path = root / path
    try:
        return full_path.stat().st_size / (1024 * 1024)
    except OSError:
        return 0.0


def main() -> int:
    root = repo_root()
    print("ChapterFOLD Git hygiene check")
    print("============================")
    print(f"Root: {root}")
    print()

    changed_paths = git_status_paths()
    tracked = tracked_files()

    bad_changed = sorted({p for p in changed_paths if is_bad_path(p)})

    large_tracked: list[tuple[str, float]] = []
    for path in tracked:
        size_mb = file_size_mb(root, path)
        if size_mb > MAX_TRACKED_FILE_SIZE_MB:
            large_tracked.append((path, size_mb))

    if not bad_changed and not large_tracked:
        print("OK: No obvious virtualenvs, backups, generated EPUBs, or large tracked files found.")
        print()
        print("Safe next commands:")
        print("  git status --short")
        print("  git add .")
        print("  git commit -m \"<message>\"")
        return 0

    print("Potential commit hygiene problems found:")
    print()

    if bad_changed:
        print("Changed files that should usually NOT be committed:")
        for path in bad_changed:
            print(f"  - {path}")
        print()
        print("To unstage but keep local files, use examples like:")
        print("  git rm -r --cached ChapterFOLD .patch_backups patch_notes || true")
        print("  git rm --cached '*.bak' '*.bak_*' || true")
        print()

    if large_tracked:
        print(f"Tracked files larger than {MAX_TRACKED_FILE_SIZE_MB} MB:")
        for path, size_mb in sorted(large_tracked, key=lambda item: item[1], reverse=True):
            print(f"  - {path} ({size_mb:.1f} MB)")
        print()
        print("Large files already tracked by Git may need removal from history before GitHub accepts pushes.")
        print("Ask before rewriting history.")

    print("Recommended review:")
    print("  git status --short")
    print("  git diff --stat")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
