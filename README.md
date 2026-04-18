# VandyGuessr

VandyGuessr is built for Vanderbilt students who want a fast, competitive way to explore campus. Each game runs through a handful of rounds using 3D images captured around campus (indoors or outdoors), and players drop a pin on a map to guess the location. Scores roll up into a round recap, and player accounts track campus rank, games played, points, and locations discovered over time.

## Architecture

See the tech stack and storage decisions in `docs/ARCHITECTURE.md`.

## Prerequisites

- [Python 3.12+](https://www.python.org/downloads/)
- [UV](https://docs.astral.sh/uv/getting-started/installation/)
- [Node.js 20+](https://nodejs.org/)
- [pnpm](https://pnpm.io/installation)
- [Docker](https://www.docker.com/get-started) (optional, for containerized development)
- [pre-commit](https://pre-commit.com/#install)

## Getting Started

### 1. Clone and Setup Environment

```bash
# Clone the repository
git clone <repository-url>
cd VandyGuessr

# Copy environment files
cp apps/api/.env.example apps/api/.env
cp apps/web/.env.example apps/web/.env
# Edit .env files with your Microsoft/Google OAuth credentials
```

### 2. Install Dependencies

```bash
# Backend
cd apps/api
uv sync
cd ..

# Frontend
cd apps/web
pnpm install
cd ..

# Pre-commit hooks
pre-commit install
```

### 3. Start Development Services

```bash
# Terminal 1: Start MongoDB and Redis via Docker
docker-compose up

# Terminal 2: Start backend
cd apps/api
uv run uvicorn app.main:app --reload --port 8000

# Terminal 3: Start image submission worker
cd apps/api
uv run python -m app.workers.image_submission_worker

# Terminal 4: Start frontend
cd apps/web
pnpm dev
```

If you are not testing uploads, the worker can be skipped. Both the authenticated upload flow and the secret-code upload flow enqueue background jobs.

### 4. Access the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Project Structure

```
VandyGuessr/
├── apps/
│   ├── api/
│   │   ├── app/
│   │   │   ├── core/            # Auth, database, redis
│   │   │   ├── domains/         # Routers, services, repositories, entities, models
│   │   │   ├── shared/          # Cross-domain helpers (EXIF, S3, scoring)
│   │   │   ├── workers/         # Background workers (queued image processing)
│   │   │   ├── config.py        # Settings
│   │   │   ├── container.py     # Lagom DI container
│   │   │   └── main.py          # FastAPI app
│   │   ├── pyproject.toml
│   │   └── Dockerfile
│   └── web/
│       ├── src/
│       │   ├── lib/
│       │   │   ├── domains/     # Games, multiplayer, leaderboard, images, users
│       │   │   ├── pages/       # Routed page components
│       │   │   └── shared/      # Auth, API client, shared UI
│       │   ├── App.svelte
│       │   └── main.ts
│       ├── package.json
│       └── Dockerfile
├── docs/
│   ├── ARCHITECTURE.md
│   ├── AUTH_SETUP.md
│   ├── MULTIPLAYER.md
│   └── PRD.md
├── docker-compose.yml
├── AGENTS.md
└── README.md
```

## Development

### Code Quality

```bash
# Backend - Run linter
cd apps/api
uv run ruff check .
uv run ruff format .

# Frontend - Run linter
cd apps/web
pnpm lint
pnpm format
```

### Pre-commit Hooks

Pre-commit hooks automatically run on `git commit`:
- Trailing whitespace removal
- End of file fixes
- YAML/JSON validation
- Ruff (Python linting/formatting)
- Biome (JS/TS linting/formatting)

## Image Upload

VandyGuessr requires 360-degree campus photos with GPS EXIF data.

### Logged-in contributors (reviewed)

Students signed in through the web app can upload from **Upload** in the nav or the home page card. Submissions are stored as **pending** until someone on the `REVIEWER_EMAIL_ALLOWLIST` approves them in the **Review** UI. Set that env var to a comma-separated list of `@vanderbilt.edu` addresses (see `apps/api/.env.example`). The API also exposes `can_review_submissions` on `GET /v1/users/me` for the frontend.

Uploads are queued and processed asynchronously. In local development, run `uv run python -m app.workers.image_submission_worker` from `apps/api/` if you want crowd uploads or operator uploads to complete. The worker uses lease-based job recovery, so stale `processing` jobs can be reclaimed after crashes instead of remaining stuck forever.

### Operator upload URLs (secret code)

Share these links with trusted bulk contributors (replace `YOUR_SECRET_CODE` with the configured `UPLOAD_SECRET_CODE`). These uploads are stored as **approved** immediately.

- **Outdoor photos**: `https://your-api-domain/v1/images/upload?code=YOUR_SECRET_CODE&environment=outdoor`
- **Indoor photos**: `https://your-api-domain/v1/images/upload?code=YOUR_SECRET_CODE&environment=indoor`

### Requirements

- Images must have GPS location data (EXIF). Most iPhone/Android camera photos include this automatically.
- Supported formats: JPEG, PNG, HEIC
- Maximum file size: 50MB (configurable via `UPLOAD_MAX_BYTES`)

### How It Works

1. Open the upload link on your phone
2. Select one or more photos (or take a new photo)
3. Tap "Upload Photos"
4. View per-photo queue and processing status until each panorama is completed or failed

Images are stored in DigitalOcean Spaces (S3-compatible) and metadata is persisted to MongoDB for use in games. A panorama is not inserted into the playable image pool until tiling, thumbnail generation, compression, location resolution, and final metadata persistence all succeed.

Each upload also generates a tiled panorama pyramid (base image + progressive tiles) so gameplay can load quickly and stream detail as players pan/zoom. Tiling preserves source panorama geometry (including wide iPhone panoramas) using stored pano crop/full metadata. Existing images can be backfilled with:

```bash
cd apps/api
python -m scripts.backfill_image_tiles --dry-run
```

Stored fallback originals are also compressed server-side (with EXIF GPS preserved) to reduce storage and egress costs. Existing images can be backfilled with:

```bash
cd apps/api
python -m scripts.backfill_image_compression --dry-run
```

## OAuth Setup

See `docs/AUTH_SETUP.md` for Microsoft and Google OAuth configuration, including the Vanderbilt-restriction feature flag.
