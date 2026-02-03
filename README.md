# VandyGuessr

A GeoGuessr-style game for Vanderbilt students that uses 3D campus imagery to test how well you know campus.

## Product Overview

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
# Edit .env files with your Microsoft OAuth credentials
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

#### Option A: Using Docker (Databases Only)

```bash
# Start MongoDB + Redis
docker-compose up mongodb redis
```

#### Option B: Run Locally

```bash
# Terminal 1: Start MongoDB and Redis via Docker
docker-compose up mongodb redis

# Terminal 2: Start backend
cd apps/api
uv run uvicorn app.main:app --reload --port 8000

# Terminal 3: Start frontend
cd apps/web
pnpm dev
```

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
│   │   │   ├── api/v1/          # API routes
│   │   │   ├── core/            # Auth, database, redis
│   │   │   ├── models/          # Pydantic models
│   │   │   ├── services/        # Business logic
│   │   │   ├── config.py        # Settings
│   │   │   └── main.py          # FastAPI app
│   │   ├── pyproject.toml
│   │   └── Dockerfile
│   └── web/
│       ├── src/
│       │   ├── lib/             # Shared components
│       │   ├── routes/          # Page components
│       │   ├── App.svelte
│       │   └── main.ts
│       ├── package.json
│       └── Dockerfile
├── docs/
│   └── ARCHITECTURE.md
├── docker-compose.yml
├── docker-compose.dev.yml
└── .env.example
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

## Microsoft OAuth Setup

See `docs/AZURE_AUTH_SETUP.md` for the full Azure app registration flow.

## License

MIT
