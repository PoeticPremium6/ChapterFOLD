# ChapterFOLD Full-Stack Readiness Notes

## Purpose

This document records what is currently ready for a future hosted ChapterFOLD Studio deployment.

Target architecture:
- Vercel: frontend, landing page, dashboard, upload flow, settings UI, result pages
- Supabase: auth, users, projects, jobs, outputs, beta invites, feedback, storage metadata
- Render: Python API or worker running the ChapterFOLD engine
- ChapterFOLD core: conversion, rendering, imposition, reports, and manifests

## Current Readiness Summary

ChapterFOLD is ready for full-stack planning because the conversion layer now has a worker-safe boundary separate from the desktop GUI.

Ready components:
- Engine API
- Worker CLI
- Web-safe settings catalog
- Input validation
- Safe job workspaces
- Job manifests
- Normalized job stages
- User-facing errors
- Cleanup utilities
- PDF worker smoke coverage
- EPUB engine API smoke coverage
- GUI dependency checks
- RTL/LTR imposition regression tests
- Packaged diagnostics behavior

## Engine API

The main hosted integration point is core.engine_api.run_engine_job.

Expected hosted usage:
result = run_engine_job(
    input_path=local_uploaded_file,
    workspace_root=local_jobs_root,
    job_id=external_job_id,
    settings=web_form_settings,
    validate_settings=True,
)

The result includes success status, job stage, input type, output files, warnings, errors, user-facing errors, report paths, and manifest paths.

## Worker CLI

The worker-safe CLI is scripts/run_engine_job.py.

Example:
python scripts/run_engine_job.py INPUT_PATH --workspace-root jobs --job-id demo123 --settings-json settings.json --validate-settings

This can be called by a future Render worker or background job process.

## Settings Catalog

Web-safe settings are available through core.settings_catalog.

Important functions:
- settings_catalog()
- settings_defaults()
- validate_web_settings()

The future frontend should use this catalog for labels, defaults, allowed choices, beginner settings, and advanced settings.

## Validation

The hosted workflow should validate file existence, file type, file size, supported input format, safe settings, and job workspace path safety.

The frontend should not send arbitrary unvalidated settings directly to the engine.

## Job Workspaces

Hosted jobs can use isolated folders:
jobs/
  project-or-book-job-id/
    input/
    output/
    reports/
      job_result.json
      job_manifest.json

This supports safe processing, cleanup, debugging, and later storage upload.

## Job Manifests

Job manifests record job ID, status, stage, input type, settings, output files, warnings, errors, user-facing errors, created timestamp, and updated timestamp.

These can map directly to a future Supabase conversion_jobs table.

## Job Stages

Current stages include:
- created
- queued
- validating
- preparing_workspace
- extracting
- cleaning
- rendering
- imposing
- saving_outputs
- complete
- failed

The frontend can use these stages to show job progress.

## User-Facing Errors

core.engine_errors converts internal failures into safer user-facing error objects.
The web UI should show friendly messages and avoid raw tracebacks.

## Cleanup

core.job_cleanup supports removing old job folders.

Suggested beta retention:
- failed jobs: delete after 24 hours
- incomplete jobs: delete after 72 hours
- completed jobs: retain by quota or explicit user deletion

## What Is Ready

Ready for web planning:
- worker-safe engine boundary
- CLI worker execution
- safe settings validation
- structured results
- manifests
- cleanup
- user-facing errors
- GUI-independent engine path

## What Is Not Ready Yet

Still needed before full-stack implementation:
- Supabase schema
- storage policy
- auth flow
- beta invite flow
- frontend route plan
- upload/download security
- hosted job queue design
- admin monitoring
- privacy/deletion policy
- final UI design

## Recommended V3 Private Preview Flow

login -> dashboard -> upload file -> choose simple settings -> generate -> download -> feedback

Avoid payments, public sharing, comments, marketplace features, and social features until private beta proves the core workflow.
