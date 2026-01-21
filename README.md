# VandyGuessr

A GeoGuessr-style game for Vanderbilt University's campus - guess locations from photos taken inside and outside campus buildings.

## Tech Stack

- **Backend**: FastAPI (Python 3.12) with UV package manager
- **Frontend**: Svelte + Vite + TypeScript + Tailwind CSS
- **Database**: MongoDB
- **Cache**: Redis
- **Authentication**: Auth0
- **Containerization**: Docker + Docker Compose

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

# Copy environment file
cp .env.example .env
# Edit .env with your Auth0 credentials
```

### 2. Install Dependencies

```bash
# Backend
cd backend
uv sync
cd ..

# Frontend
cd frontend
pnpm install
cd ..

# Pre-commit hooks
pre-commit install
```

### 3. Start Development Services

#### Option A: Using Docker (Recommended)

```bash
# Start all services (backend, frontend, MongoDB, Redis)
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Or start just the databases
docker-compose up mongodb redis
```

#### Option B: Run Locally

```bash
# Terminal 1: Start MongoDB and Redis via Docker
docker-compose up mongodb redis

# Terminal 2: Start backend
cd backend
uv run uvicorn app.main:app --reload --port 8000

# Terminal 3: Start frontend
cd frontend
pnpm dev
```

### 4. Access the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Project Structure

```
VandyGuessr/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # API routes
│   │   ├── core/            # Auth, database, redis
│   │   ├── models/          # Pydantic models
│   │   ├── services/        # Business logic
│   │   ├── config.py        # Settings
│   │   └── main.py          # FastAPI app
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── lib/             # Shared components
│   │   ├── routes/          # Page components
│   │   ├── App.svelte
│   │   └── main.ts
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── docker-compose.dev.yml
└── .env.example
```

## Development

### Code Quality

```bash
# Backend - Run linter
cd backend
uv run ruff check .
uv run ruff format .

# Frontend - Run linter
cd frontend
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

## Auth0 Setup

1. Create an Auth0 account at https://auth0.com
2. Create a new Application (Single Page Application)
3. Create a new API
4. Configure the following in your `.env`:
   - `AUTH0_DOMAIN`: Your Auth0 domain
   - `AUTH0_API_AUDIENCE`: Your API identifier
   - `VITE_AUTH0_CLIENT_ID`: Your SPA client ID

## License

MIT
