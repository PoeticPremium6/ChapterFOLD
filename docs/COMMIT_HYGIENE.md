# ChapterFOLD Commit Hygiene

Before committing, run:

```bash
python scripts/check_git_hygiene.py
python scripts/preflight_check.py
python scripts/check_project.py
```

## Do commit

These are normal project files:

```text
.github/
api/
chapterfold_app/
core/
docs/
scripts/
tests/
requirements.txt
pyproject.toml
README.md
.gitignore
```

## Do not commit

These are local/generated files and should stay out of Git:

```text
ChapterFOLD/
.venv/
venv/
env/
.patch_backups/
patch_notes/
__pycache__/
.pytest_cache/
*.bak
*.bak_*
tests/fixtures/epubs/generated/
tests/fixtures/epubs/*.epub
build/
dist/
outputs/
```

## Why this matters

The `ChapterFOLD/` directory is a local Python virtual environment. It contains
installed packages such as PySide6 and Qt libraries. These can be hundreds of
megabytes and GitHub will reject files over 100 MB.

Patch backup folders are useful locally, but they should not be committed.

Generated EPUB fixtures are reproducible via:

```bash
python scripts/build_sample_epubs.py
```

So the generated `.epub` files do not need to live in Git.

## Safe commit flow

```bash
git status --short
python scripts/check_git_hygiene.py
python scripts/preflight_check.py
python scripts/check_project.py

git add .gitignore .github api chapterfold_app core docs scripts tests requirements.txt pyproject.toml README.md
git status --short
git commit -m "Your commit message"
```

## If you accidentally staged the virtual environment

This removes it from Git's staged/tracked list but keeps your local files:

```bash
git rm -r --cached ChapterFOLD .patch_backups patch_notes || true
git rm --cached '*.bak' '*.bak_*' || true
```

Then check again:

```bash
git status --short
python scripts/check_git_hygiene.py
```
