# Trivia Forge

Self-hosted multimedia trivia engine for text, image and audio recognition. This is the first working scaffold: schema, API, media storage, game generation, grading, starter UI and an hourly worker process.

## What works now

- PostgreSQL-backed schema for categories, knowledge items, questions, multi-part answers, media, sources, games, attempts and audit events.
- Text, image, audio and video media are first-class assets.
- Questions can have multiple answer slots, so an audio question can award separate points for `artist` and `title`.
- Practice game generation balances text/image/audio targets and Canadian weighting as closely as the available bank allows.
- Answers are normalized for case, accents, punctuation and leading English articles.
- Browser UI can start a practice session, display images/play audio, accept answers and show canonical answers after grading.
- Browser Library can create questions, upload images, upload full audio tracks, automatically cut normalized 10–15 second-style clips with FFmpeg, and attach media to questions.
- Media upload and question attachment APIs are ready.
- Independent worker container already runs every hour; external ingestion providers are the next milestone.
- Starter seed bank contains 12 top-level categories and 10 representative questions.

## Run with Docker Compose

```bash
docker compose up --build -d
```

Open:

```text
http://YOUR-SERVER:8080
```

API docs:

```text
http://YOUR-SERVER:8080/docs
```

## Local backend development

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080
```

The backend defaults to SQLite when `TRIVIA_DATABASE_URL` is not supplied.

## Local frontend development

```bash
cd frontend
npm install
npm run dev
```

Vite proxies `/api` and `/media` to the backend on port 8080.

## Useful API calls

Create a question:

```json
POST /api/questions
{
  "primary_category_id": 4,
  "question_type": "audio_artist_title",
  "prompt": "Name the artist and song.",
  "difficulty": 7,
  "obscurity": 6,
  "canadian_relevance": 0,
  "answers": [
    {"answer_key": "artist", "answer_text": "Massive Attack", "points": 1},
    {"answer_key": "title", "answer_text": "Teardrop", "points": 1}
  ]
}
```

Upload media:

```text
POST /api/media   multipart/form-data: file=<file>
```

Create a normalized 12-second audio clip from an uploaded track:

```json
POST /api/media/{media_id}/clip
{"start_seconds": 42, "duration_seconds": 12, "normalize": true, "fade": true}
```

Attach uploaded or derived media to a question:

```text
POST /api/media/{media_id}/attach/{question_id}
```

## Filesystem layout

The Docker deployment persists:

```text
./postgres-data   PostgreSQL
./media           uploaded/generated media
```

Inside the app, media is served at `/media/<relative path>`.

## Next milestone

The next build should implement the actual ingestion engine:

1. topic/category coverage analysis,
2. Wikidata/Wikipedia candidate facts,
3. MusicBrainz track metadata,
4. image acquisition and perceptual duplicate detection,
5. local audio ingestion + FFmpeg 10/12/15-second clipping,
6. question generation/verification adapters,
7. review queue and admin editor,
8. embeddings for semantic duplicate detection.

The worker topology is already in place so these additions do not require redesigning deployment.
