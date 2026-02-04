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
│   │   │   ├── api/v1/          # Controllers (HTTP layer)
│   │   │   ├── core/            # Auth, database, redis
│   │   │   ├── entities/        # MongoDB document schemas
│   │   │   ├── models/          # API request/response schemas
│   │   │   ├── repositories/    # Database access layer
│   │   │   ├── services/        # Business logic
│   │   │   ├── config.py        # Settings
│   │   │   └── main.py          # FastAPI app
│   │   ├── pyproject.toml
│   │   └── Dockerfile
│   └── web/
│       ├── src/
│       │   ├── lib/
│       │   │   ├── auth/        # MSAL configuration
│       │   │   ├── components/  # Svelte components
│       │   │   └── stores/      # Svelte stores
│       │   ├── App.svelte
│       │   └── main.ts
│       ├── package.json
│       └── Dockerfile
├── docs/
│   ├── ARCHITECTURE.md
│   ├── AZURE_AUTH_SETUP.md
│   └── PRD.md
├── docker-compose.yml
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

## License

MIT
