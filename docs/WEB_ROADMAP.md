# ChapterFOLD Web Roadmap

ChapterFOLD should evolve from a useful desktop tool into a reliable engine that
can power a polished full-stack web workflow.

## Strategic split

- Public desktop repo: trust, portfolio value, community feedback, open tooling.
- Private production web repo: hosted workflow, auth, storage, payments, analytics,
  admin tools, and premium UX.

## Patch roadmap

### Patch 001: Foundation

- Shared settings schema.
- UI-independent job input/result contract.
- Basic regression tests.
- Local project health check.
- Linux/Windows CI scaffold.

### Patch 002: Diagnostics

- Add a user-facing diagnostic report.
- Include app version, OS, settings, stage, and traceback.
- Make bug reports actionable.

### Patch 003: CLI runner

- Add a command-line conversion entry point.
- Enable batch tests and release smoke tests.
- Make Linux development easier while Windows remains the release target.

### Patch 004: EPUB regression suite

- Add sample/fixture strategy.
- Cover scene breaks, dialogue, metadata, malformed EPUBs, and imposition outputs.
- Prevent old bugs from returning.

### Patch 005: FastAPI prototype

- Wrap the engine in a minimal API.
- Prepare for Render backend + Next.js frontend.
- Define upload, job status, and download endpoints.

## Target architecture

```text
Next.js / Vercel
- Landing page
- Upload flow
- Settings wizard
- Preview/status/download pages

Python / Render
- EPUB parsing
- Cleanup
- PDF/DOCX/Markdown generation
- Imposition
- Job worker

Supabase
- Auth
- Database
- File metadata
- User projects
- Generated file records
```

## Product principle

The paid web version should not merely convert files. It should reduce anxiety
for hobby bookbinders by giving them a guided, reliable, previewable workflow.
