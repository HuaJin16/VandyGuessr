# Architecture

## Tech Stack

- **Backend**: FastAPI (Python 3.12) with UV package manager
- **Frontend**: Svelte + Vite + TypeScript + Tailwind CSS
- **Database**: MongoDB
- **Cache**: Redis
- **Authentication**: Guided dual OAuth (Microsoft for Vanderbilt students, Google for any Google account)
- **Containerization**: Docker + Docker Compose

### Additional Libraries

| Layer    | Library                  | Purpose                           |
| -------- | ------------------------ | --------------------------------- |
| Backend  | `lagom`                  | Dependency injection container    |
| Backend  | `structlog`              | Structured JSON logging           |
| Frontend | `axios`                  | HTTP client                       |
| Frontend | `@tanstack/svelte-query` | Server state management & caching |
| Frontend | `svelte-routing`         | History-mode client-side routing  |
| Frontend | `bits-ui`                | Headless component primitives     |
| Frontend | `tailwind-variants`      | Variant-based component styling   |

---

## Backend Architecture

### Domain-Driven Design (DDD) Structure

The backend follows a DDD-inspired architecture organized by business domains:

```
apps/api/app/
├── main.py                          # FastAPI entry point
├── config.py                        # Pydantic Settings
├── container.py                     # Lagom DI container
├── core/                            # Shared infrastructure
│   ├── db/
│   │   ├── mongo.py                 # MongoDB client provider
│   │   └── redis.py                 # Redis client provider
│   ├── http/
│   │   ├── responses.py             # HTTP response helpers
│   │   └── exceptions.py            # Custom HTTP exceptions
│   └── auth/
│       ├── microsoft.py             # Microsoft OAuth/JWT verification
│       ├── google.py                # Google OAuth/JWT verification
│       └── provider.py              # Provider selector + shared CurrentUser dependency
├── domains/                         # Business domains (bounded contexts)
│   ├── users/
│   │   ├── __init__.py
│   │   ├── router.py                # HTTP endpoints (controller)
│   │   ├── service.py               # Business logic
│   │   ├── repository.py            # Data access + Protocol interface
│   │   ├── entities.py              # MongoDB document schemas
│   │   ├── models.py                # API request/response schemas
│   │   └── exceptions.py            # Domain-specific errors
│   ├── images/
│   │   ├── router.py                # Secret-code HTML upload flow
│   │   ├── json_router.py           # Crowd uploads + moderation APIs
│   │   ├── service.py               # Upload orchestration
│   │   ├── moderation_service.py    # Approve/reject pending submissions
│   │   └── submission_job_service.py # Queue-backed background processing
│   ├── locations/
│   │   ├── __init__.py
│   │   ├── repository.py            # Geospatial queries (2dsphere index)
│   │   ├── entities.py              # LocationEntity document schema
│   │   └── service.py               # Location resolution (no router — internal only)
│   ├── games/
│   │   └── ...
│   └── multiplayer/
│       └── ...
├── shared/                          # Cross-cutting utilities
│   ├── exif.py                      # EXIF metadata extraction
│   └── s3.py                        # S3/Spaces upload utilities
└── workers/
    └── image_submission_worker.py   # Queue consumer for image processing
```

### Request Flow

```
Request → Router → Service → Repository → MongoDB
            ↓          ↓
         Models    Entities
```

### Layer Responsibilities

| Layer            | Location                  | Responsibility                                            |
| ---------------- | ------------------------- | --------------------------------------------------------- |
| **Routers**      | `domains/*/router.py`     | HTTP request/response handling, routing, input validation |
| **Models**       | `domains/*/models.py`     | Pydantic schemas for API request/response contracts       |
| **Services**     | `domains/*/service.py`    | Business logic and orchestration                          |
| **Repositories** | `domains/*/repository.py` | Database CRUD operations                                  |
| **Entities**     | `domains/*/entities.py`   | MongoDB document schemas                                  |

### Dependency Injection with Lagom

We use **lagom** for container-based dependency injection:

```python
# container.py
from lagom import Container
from app.core.db.mongo import get_database
from app.domains.users.repository import IUserRepository, UserRepository
from app.domains.users.service import UserService

container = Container()

# Register database
container[AsyncIOMotorDatabase] = get_database()

# Register repositories (Protocol → Implementation)
container[IUserRepository] = UserRepository

# Register services
container[UserService] = UserService

# deps.py - FastAPI integration
from typing import TypeVar
from fastapi import Depends

T = TypeVar("T")

def deps(cls: type[T]) -> T:
    """Resolve a dependency from the container."""
    return Depends(lambda: container.resolve(cls))
```

**Usage in routers:**

```python
# domains/users/router.py
from app.container import deps
from app.domains.users.service import UserService

@router.get("/me")
async def get_me(service: UserService = deps(UserService)):
    return await service.get_current_user()
```

**Protocol-based interfaces for testability:**

```python
# domains/users/repository.py
from typing import Protocol

class IUserRepository(Protocol):
    async def find_by_microsoft_oid(self, oid: str) -> dict | None: ...
    async def find_by_username(self, username: str) -> dict | None: ...
    async def create(self, user: UserEntity) -> str: ...

class UserRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.collection = db.users

    async def find_by_microsoft_oid(self, oid: str) -> dict | None:
        return await self.collection.find_one({"microsoft_oid": oid})
```

**Testing with mocks:**

```python
# Override in tests
from app.container import container

container[IUserRepository] = MockUserRepository()
```

### Logging with Structlog

We use **structlog** for structured JSON logging:

```python
import structlog

logger = structlog.get_logger()

# In services/routers
logger.info("user_created", user_id=user_id, email=email)
logger.error("payment_failed", user_id=user_id, error=str(e))
```

**Output format (JSON):**

```json
{
  "event": "user_created",
  "user_id": "123",
  "email": "user@vanderbilt.edu",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Health Check Endpoint

The API exposes a `/health` endpoint for container orchestration:

```python
@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": os.getenv("VERSION", "unknown"),
        "git_sha": os.getenv("GIT_SHA", "unknown"),
        "git_branch": os.getenv("GIT_BRANCH", "unknown"),
    }
```

**Build-time injection via Docker:**

```dockerfile
ARG GIT_SHA
ARG GIT_BRANCH
ARG VERSION
ENV GIT_SHA=$GIT_SHA GIT_BRANCH=$GIT_BRANCH VERSION=$VERSION
```

```bash
docker build \
  --build-arg GIT_SHA=$(git rev-parse HEAD) \
  --build-arg GIT_BRANCH=$(git branch --show-current) \
  --build-arg VERSION=1.0.0 \
  .
```

### Backend Guidelines

- **Routers** should be thin - no business logic or direct database access
- **Services** contain business logic and call repositories for data access
- **Repositories** are the only layer that interacts with the database
- **Models** define the API contract (what clients send/receive)
- **Entities** define the database contract (what gets stored)
- **All dependencies** must be registered in `container.py`
- **Use Protocols** for repository interfaces to enable testing

---

## Frontend Architecture

### Domain-Driven Design (DDD) Structure

The frontend follows a DDD-inspired architecture with route orchestration in `App.svelte` and most product code under `lib/`:

```
apps/web/src/
├── main.ts                          # Application entry
├── App.svelte                       # Root component + route wiring
├── app.css                          # Global styles (Tailwind)
├── lib/
│   ├── shared/                      # Cross-domain infrastructure
│   │   ├── api/
│   │   │   ├── client.ts            # Axios instance + interceptors
│   │   │   ├── queryClient.ts       # TanStack Query client
│   │   │   ├── types.ts             # ApiResponse<T>, ApiError
│   │   │   └── interceptors/
│   │   ├── auth/
│   │   │   ├── auth.store.ts        # MSAL/Google auth state
│   │   │   ├── msalConfig.ts        # MSAL configuration
│   │   │   ├── googleIdentity.ts    # GIS loader + Google ID token helpers
│   │   │   └── token.ts             # Provider-aware token accessor
│   │   ├── components/              # Shared UI components
│   │   └── utils/
│   ├── domains/                     # Business domains
│   │   ├── games/
│   │   ├── leaderboard/
│   │   ├── multiplayer/
│   │   ├── images/
│   │   └── users/
│   └── pages/                       # Route pages (thin orchestrators)
│       ├── Home.svelte
│       ├── Login.svelte
│       ├── Game.svelte
│       ├── Upload.svelte
│       ├── ReviewSubmissions.svelte
│       ├── MultiplayerLobby.svelte
│       └── MultiplayerGame.svelte
```

### HTTP Service Pattern

**Shared Axios Client (`lib/shared/api/client.ts`):**

```typescript
import axios from "axios";
import { authInterceptor } from "./interceptors/auth.interceptor";
import { errorInterceptor } from "./interceptors/error.interceptor";

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  headers: { "Content-Type": "application/json" },
});

// Attach auth token to all requests
apiClient.interceptors.request.use(authInterceptor);

// Transform errors consistently
apiClient.interceptors.response.use((response) => response, errorInterceptor);
```

**Auth Interceptor (`lib/shared/api/interceptors/auth.interceptor.ts`):**

```typescript
import type { InternalAxiosRequestConfig } from "axios";
import { getAuthToken } from "$lib/shared/auth/token";

export async function authInterceptor(
  config: InternalAxiosRequestConfig,
): Promise<InternalAxiosRequestConfig> {
  const token = await getAuthToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}
```

**Domain HTTP Service (`lib/domains/users/api/users.service.ts`):**

```typescript
import { apiClient } from "$lib/shared/api/client";
import type { User, UpdateProfileDto } from "../types";

export const usersService = {
  getMe: () => apiClient.get<User>("/v1/users/me").then((r) => r.data),

  updateProfile: (data: UpdateProfileDto) =>
    apiClient.patch<User>("/v1/users/me", data).then((r) => r.data),

  getById: (id: string) =>
    apiClient.get<User>(`/v1/users/${id}`).then((r) => r.data),
};
```

### Svelte Query Integration

**Query Definitions (`lib/domains/users/queries/users.queries.ts`):**

```typescript
import { usersService } from "../api/users.service";

export const userQueries = {
  me: () => ({
    queryKey: ["users", "me"],
    queryFn: () => usersService.getMe(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  }),

  byId: (id: string) => ({
    queryKey: ["users", id],
    queryFn: () => usersService.getById(id),
  }),
};
```

**Usage in Components:**

```svelte
<script lang="ts">
  import { createQuery } from '@tanstack/svelte-query';
  import { userQueries } from '$lib/domains/users/queries/users.queries';
  import Skeleton from '$lib/shared/components/Skeleton.svelte';
  import ErrorCard from '$lib/shared/components/ErrorCard.svelte';

  const user = createQuery(userQueries.me());
</script>

{#if $user.isLoading}
  <Skeleton />
{:else if $user.isError}
  <ErrorCard error={$user.error} onRetry={() => $user.refetch()} />
{:else if $user.data}
  <UserProfile user={$user.data} />
{/if}
```

### Optimistic Updates

Mutations currently live close to the page or domain flow that owns them, and they update TanStack Query state directly with `queryClient.setQueryData()` or `invalidateQueries()`.

Current examples:

- `apps/web/src/lib/pages/Game.svelte` updates the active game query immediately after guess submission and end-game actions.
- `apps/web/src/lib/pages/ReviewSubmissions.svelte` invalidates the pending moderation list after approve/reject actions.

### Error Boundaries

The app primarily relies on explicit query-state rendering (`isLoading`, `isError`) plus toast messaging rather than a dedicated shared `ErrorBoundary` component. Pages such as `Game.svelte`, `ReviewSubmissions.svelte`, and multiplayer screens surface failure states inline and recover by refetching or redirecting as needed.

### Routing with svelte-routing

Routes are assembled directly in `App.svelte` rather than a separate `routes.ts` file.

```svelte
<!-- App.svelte -->
<script>
  import { Router, Route } from 'svelte-routing';
  import { QueryClientProvider } from '@tanstack/svelte-query';
  import { queryClient } from '$lib/shared/api/queryClient';
  import Home from '$lib/pages/Home.svelte';
  import Login from '$lib/pages/Login.svelte';
  import Upload from '$lib/pages/Upload.svelte';
</script>

<QueryClientProvider client={queryClient}>
  <Router>
    <Route path="/" component={Home} />
    <Route path="/login" component={Login} />
    <Route path="/upload" component={Upload} />
  </Router>
</QueryClientProvider>
```

### Frontend Guidelines

- **Domains own their vertical slice** - API service, queries, components, types
- **Pages are thin orchestrators** - Compose domain components, handle routing params
- **Shared code** is truly cross-domain (axios client, auth, common UI components)
- **Use Svelte Query** for all server state - avoid duplicating in stores
- **Stores** are for client-only state (UI state, form state, etc.)
- **Optimistic updates** for mutations where instant feedback improves UX
- **Error boundaries** wrap major sections to prevent full-page crashes

### Auth Identity Contract

- Downstream domains continue to treat auth identity as `oid` (string user key) for games, leaderboard, multiplayer, and uploads.
- Microsoft keeps existing `oid` behavior unchanged.
- Google users map to `oid = google:{sub}` so cross-provider identities stay collision-safe without domain-wide refactors.

### UI Components with Bits UI

We use **Bits UI** (headless component library) + **tailwind-variants** for building styled UI primitives:

```
apps/web/src/lib/shared/
├── ui/
│   ├── index.ts           # Barrel export
│   ├── Button.svelte      # Styled button with variants
│   ├── Card.svelte        # Container component
│   └── CardContent.svelte # Card content wrapper
└── utils.ts               # cn() utility for class merging
```

**Class merging utility (`lib/shared/utils.ts`):**

```typescript
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

**Button with variants (`lib/shared/ui/Button.svelte`):**

```svelte
<script lang="ts">
  import { tv, type VariantProps } from "tailwind-variants";
  import { cn } from "$lib/shared/utils";

  const buttonVariants = tv({
    base: "inline-flex items-center justify-center rounded-md text-sm font-medium ...",
    variants: {
      variant: {
        default: "bg-neutral-900 text-white hover:bg-neutral-800",
        outline: "border border-neutral-300 bg-transparent hover:bg-neutral-100",
        ghost: "hover:bg-neutral-100",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 px-3",
        lg: "h-11 px-8",
      },
    },
    defaultVariants: { variant: "default", size: "default" },
  });

  export let variant: VariantProps<typeof buttonVariants>["variant"] = "default";
  export let size: VariantProps<typeof buttonVariants>["size"] = "default";
  let className = "";
  export { className as class };
</script>

<button class={cn(buttonVariants({ variant, size }), className)} on:click {...$$restProps}>
  <slot />
</button>
```

**Usage:**

```svelte
<script>
  import { Button, Card, CardContent } from "$lib/shared/ui";
</script>

<Card>
  <CardContent>
    <Button variant="outline" size="sm">Click me</Button>
  </CardContent>
</Card>
```

---

## Storage Decisions

### Image Storage (S3-Compatible via DigitalOcean Spaces)

- **What we store**: Campus photo assets used for game rounds, uploaded by contributors.
- **Why S3-compatible storage**: Simple, cost-effective object storage that scales with image volume and integrates cleanly with CDN or public delivery later.
- **Current scope**: Store the original upload and a tiled pyramid for progressive panorama loading.

### Upload Pipeline and Metadata

- **Upload endpoints**: Trusted operators use the secret-code HTML upload flow, which now queues each photo as its own background job via `POST /v1/images/upload/jobs`; logged-in students use `POST /v1/images/submissions` (Bearer token, multipart) which stores images as **pending** until a reviewer approves them. Reviewers are configured via `REVIEWER_EMAIL_ALLOWLIST`.
- **EXIF extraction**: GPS metadata is extracted from EXIF and used to seed location data into MongoDB.
- **Tiling**: After EXIF extraction, the backend generates a low-resolution base panorama plus tile levels for progressive streaming in the viewer.
- **Tiling geometry**: Tile generation is aspect-ratio aware and stores pano crop/full geometry (`base_pano_data`) so non-2:1 sources (for example iPhone panoramas) render without stretching.
- **Compression**: The stored fallback original is re-encoded with a configurable JPEG quality policy (EXIF-preserving) to reduce storage and egress while keeping gameplay compatibility.
- **S3 object keys**: Images are stored under an `images/` prefix with unique UUIDs (e.g., `images/{uuid}.jpg`) and tiles under `images/{uuid}/base.jpg`, `images/{uuid}/l{level}/{col}_{row}.jpg`.
- **Queue durability**: `image_submission_jobs` is the durable source of truth for work claims. Redis wakes workers quickly, but workers can reclaim stale `processing` jobs via lease expiry so crashed workers do not strand uploads forever.
- **Playability gate**: Images are inserted into the playable `images` collection only after tiles, thumbnail, compression, location resolution, and final MongoDB persistence succeed.
- **MongoDB persistence**: Image metadata (URL, coordinates, environment, timestamps) is stored in the `images` collection.
- **Backfill path**: Existing images can be tiled with `python -m scripts.backfill_image_tiles`.
- **Compression backfill**: Existing originals can be recompressed and annotated with `python -m scripts.backfill_image_compression`.

### Images Domain Structure

```
apps/api/app/domains/images/
├── __init__.py
├── router.py            # GET (HTML form) + POST/POST jobs — operator / secret code
├── json_router.py       # POST /submissions (crowd) + GET job status + GET/POST moderation
├── moderation_service.py
├── service.py           # Upload orchestration, validation, S3 + MongoDB persistence
├── repository.py        # MongoDB CRUD; gameplay pool excludes pending/rejected
├── submission_job_entities.py
├── submission_job_models.py
├── submission_job_repository.py
├── submission_job_service.py
├── entities.py          # ImageEntity document schema
└── models.py            # API response schemas
```

### Image Entity Schema

```python
{
    "_id": ObjectId,
    "url": str,                    # S3 URL
    "latitude": float,             # GPS latitude from EXIF
    "longitude": float,            # GPS longitude from EXIF
    "altitude": float | None,      # Optional altitude
    "timestamp": datetime | None,  # EXIF timestamp
    "width": int | None,
    "height": int | None,
    "format": str | None,          # jpg, png, etc.
    "environment": "indoor" | "outdoor",
    "original_filename": str | None,
    "file_size": int,
    "location_name": str | None,   # Auto-tagged building/landmark name
    "tiles": {
        "version": int,
        "base_url": str,
        "tile_url_template": str,   # contains {level}, {col}, {row} placeholders
        "level_count": int,
        "original_width": int,
        "original_height": int,
        "aspect_ratio": float,
        "base_pano_data": {
            "full_width": int,
            "full_height": int,
            "cropped_width": int,
            "cropped_height": int,
            "cropped_x": int,
            "cropped_y": int
        },
        "levels": [
            {"level": int, "width": int, "height": int, "cols": int, "rows": int}
        ]
    } | None,
    "compression": {
        "version": int,
        "source_size_bytes": int,
        "stored_size_bytes": int,
        "savings_ratio": float,
        "quality": int,
        "format": str,
        "compressed": bool
    } | None,
    "created_at": datetime,
    "moderation_status": "pending" | "approved" | "rejected",  # default approved; omitted on legacy = playable
    "submitted_by_user_id": str | None,  # Microsoft OID for crowd submissions
    "submitted_at": datetime | None,
    "reviewed_by_user_id": str | None,
    "reviewed_at": datetime | None,
}
```

Random games, daily challenge ID pools, and multiplayer sampling only include documents where `moderation_status` is not `pending` or `rejected` (including documents with no `moderation_status` field).

### Locations Domain & Data Seeding

Location data is seeded from an OpenStreetMap GeoJSON export containing Vanderbilt campus building/landmark polygons.

**Seed script:** `python -m scripts.seed_locations` (run from `apps/api/`)

- Source data: `apps/api/data/campus_buildings.geojson` (277 named features)
- Idempotent: upserts by `osm_id` so re-running is safe
- Creates `2dsphere` index on `geometry` and unique index on `osm_id`
- Backfills existing images that have `location_name: null`

**Auto-tagging on upload:** When an image is uploaded with GPS coordinates, `LocationService.resolve_location_name()` performs a two-step geospatial lookup:

1. `$geoIntersects` — exact polygon match (image point falls inside a building boundary)
2. `$near` with `$maxDistance: 15` — fallback for images taken near but not inside a boundary (15m radius)

**Location Entity Schema:**

```python
{
    "_id": ObjectId,
    "name": str,                   # "Kirkland Hall", "Alumni Lawn", etc.
    "osm_id": str,                 # OpenStreetMap feature ID
    "building_type": str | None,   # "university", "residential", "hospital", etc.
    "geometry": dict,              # GeoJSON geometry (Polygon or Point)
    "created_at": datetime
}
```

**Domain structure:**

```
apps/api/app/domains/locations/
├── __init__.py
├── entities.py      # LocationEntity document schema
├── repository.py    # Geospatial queries (2dsphere index)
└── service.py       # Location name resolution (internal only, no router)
```
