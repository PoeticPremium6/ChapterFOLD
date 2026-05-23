# ChapterFOLD API Prototype

Patch 005 adds a small FastAPI backend prototype around the ChapterFOLD core job layer.

This is not the production hosted product yet. It is a bridge between the desktop app and the future full-stack architecture.

## Run locally

```bash
cd ~/Desktop/BioStudio/Github/ChapterFOLD
source ChapterFOLD/bin/activate
python -m pip install --default-timeout=300 -r requirements.txt
uvicorn api.main:app --reload
```

Then open:

```text
http://127.0.0.1:8000/docs
```

## Endpoints

```text
GET  /health
GET  /settings/defaults
POST /jobs/validate
POST /jobs
```

## Prototype limits

The `/jobs` endpoint currently uses temporary local storage. That is fine for local testing, but not production.

Before paid deployment, add:

- background job queue
- persistent file storage
- auth
- signed download links
- job history
- output cleanup policy
- file size limits
- rate limits
- better conversion progress reporting

## Future target architecture

```text
Next.js frontend -> FastAPI backend -> ChapterFOLD core runner
                 -> Supabase auth/db/storage
                 -> background worker for conversion jobs
```
