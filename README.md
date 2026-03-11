# VandyGuessr

VandyGuessr is a GeoGuessr-style game scoped to Vanderbilt University’s campus. It gives Vanderbilt students a fast, competitive way to explore campus while creating a shared experience within the community. Each game runs through several rounds using 240-degree images captured around campus, both indoors and outdoors. Players drop a pin on the map to guess the location, and their scores roll up into a round recap and persistent player profile that tracks campus rank, games played, points, and locations discovered over time.

## Architecture

VandyGuessr is a monorepo with a FastAPI backend (`apps/api`) and a Svelte 4 SPA frontend (`apps/web`), backed by MongoDB and Redis.

For the full tech stack, architecture decisions, and storage decisions, see `docs/ARCHITECTURE.md`.

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
# Edit .env files based on your mode (standard or demo)
```

### 2. Install Dependencies

```bash
# Backend
cd apps/api
uv sync
cd ../..

# Frontend
cd apps/web
pnpm install
cd ..

# Pre-commit hooks
pre-commit install
```

### 3. Demo Mode (Reviewer-Friendly)

Demo mode exists so reviewers can run and evaluate the app without Vanderbilt-specific infrastructure.

#### Why we included demo mode

- Microsoft OAuth in normal mode requires a real Azure app registration and a valid `@vanderbilt.edu` account.
- Game images in normal mode are stored in DigitalOcean Spaces (S3-compatible), which reviewers typically do not have access to.
- Demo mode removes both blockers by using a mock authenticated user and serving images from local disk.

#### Demo setup steps

1. Enable demo flags in env files:

```bash
# apps/api/.env
DEMO_MODE=true

# apps/web/.env
VITE_DEMO_MODE=true
```

2. Seed required data (from `apps/api/`):

```bash
uv run python -m scripts.seed_locations
uv run python -m scripts.seed_demo
```

### 4. Start Development Services

```bash
# Terminal 1: Start MongoDB and Redis via Docker
docker-compose up

# Terminal 2: Start backend
cd apps/api
uv run uvicorn app.main:app --reload --port 8000

# Terminal 3: Start frontend
cd apps/web
pnpm dev
```

### 5. Access the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Project Structure

```
VandyGuessr/
├── apps/
│   ├── api/                      # FastAPI backend
│   │   ├── app/
│   │   │   ├── core/            # Auth, DB, Redis, HTTP utilities
│   │   │   ├── domains/         # Feature modules
│   │   │   ├── shared/          # Cross-cutting helpers
│   │   │   ├── config.py
│   │   │   ├── container.py
│   │   │   └── main.py
│   │   ├── data/                # Demo assets and seed data
│   │   └── scripts/             # Seed and utility scripts
│   └── web/                     # Svelte SPA frontend
│       └── src/
│           ├── lib/
│           │   ├── domains/     # Feature modules
│           │   ├── pages/       # Top-level pages
│           │   └── shared/      # Shared API/auth/UI utilities
│           ├── App.svelte
│           └── main.ts
├── docs/                        # Architecture and product docs
├── docker-compose.yml           # Local MongoDB + Redis
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

VandyGuessr requires 360-degree campus photos with GPS EXIF data. Contributors can upload images via a mobile-friendly HTML form.

### Upload URLs

Share these links with photo contributors (replace `YOUR_SECRET_CODE` with the configured `UPLOAD_SECRET_CODE`):

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
4. View results showing which uploads succeeded and their GPS coordinates

Images are stored in DigitalOcean Spaces (S3-compatible) and metadata is persisted to MongoDB for use in games.

## Microsoft OAuth Setup

See `docs/AZURE_AUTH_SETUP.md` for the full Azure app registration flow.
