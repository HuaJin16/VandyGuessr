# Architecture

## Tech Stack

- **Backend**: FastAPI (Python 3.12) with UV package manager
- **Frontend**: Svelte + Vite + TypeScript + Tailwind CSS
- **Database**: MongoDB
- **Cache**: Redis
- **Authentication**: Microsoft OAuth (Azure AD)
- **Containerization**: Docker + Docker Compose

### Additional Libraries

| Layer | Library | Purpose |
|-------|---------|---------|
| Backend | `lagom` | Dependency injection container |
| Backend | `structlog` | Structured JSON logging |
| Frontend | `axios` | HTTP client |
| Frontend | `@tanstack/svelte-query` | Server state management & caching |
| Frontend | `svelte-spa-router` | Client-side routing |

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
│       └── microsoft.py             # OAuth/JWT verification
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
│   │   └── ...
│   └── games/
│       └── ...
└── shared/                          # Cross-cutting utilities
    ├── exif.py                      # EXIF metadata extraction
    └── s3.py                        # S3/Spaces upload utilities
```

### Request Flow

```
Request → Router → Service → Repository → MongoDB
            ↓          ↓
         Models    Entities
```

### Layer Responsibilities

| Layer | Location | Responsibility |
|-------|----------|----------------|
| **Routers** | `domains/*/router.py` | HTTP request/response handling, routing, input validation |
| **Models** | `domains/*/models.py` | Pydantic schemas for API request/response contracts |
| **Services** | `domains/*/service.py` | Business logic and orchestration |
| **Repositories** | `domains/*/repository.py` | Database CRUD operations |
| **Entities** | `domains/*/entities.py` | MongoDB document schemas |

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
{"event": "user_created", "user_id": "123", "email": "user@vanderbilt.edu", "timestamp": "2024-01-15T10:30:00Z"}
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

The frontend follows a DDD-inspired architecture with domain ownership:

```
apps/web/src/
├── main.ts                          # Application entry
├── App.svelte                       # Root component
├── routes.ts                        # Route definitions
├── app.css                          # Global styles (Tailwind)
├── shared/                          # Cross-domain infrastructure
│   ├── api/
│   │   ├── client.ts                # Axios instance + interceptors
│   │   ├── types.ts                 # ApiResponse<T>, ApiError
│   │   └── interceptors/
│   │       ├── auth.interceptor.ts  # Attaches Bearer token
│   │       └── error.interceptor.ts # Transforms API errors
│   ├── auth/
│   │   ├── msalConfig.ts            # MSAL configuration
│   │   └── msalInstance.ts          # MSAL singleton
│   ├── components/                  # Shared UI components
│   │   ├── Button.svelte
│   │   ├── Modal.svelte
│   │   ├── Skeleton.svelte
│   │   └── ErrorBoundary.svelte
│   └── utils/
├── domains/                         # Business domains
│   ├── users/
│   │   ├── api/
│   │   │   └── users.service.ts     # HTTP methods
│   │   ├── queries/
│   │   │   └── users.queries.ts     # Svelte Query definitions
│   │   ├── components/
│   │   │   ├── UserProfile.svelte
│   │   │   └── UserAvatar.svelte
│   │   ├── stores/
│   │   │   └── user.store.ts        # Client-only state (if needed)
│   │   └── types.ts                 # TypeScript types
│   ├── games/
│   │   ├── api/
│   │   │   └── games.service.ts
│   │   ├── queries/
│   │   │   └── games.queries.ts
│   │   ├── components/
│   │   │   ├── GameBoard.svelte
│   │   │   └── ScoreCard.svelte
│   │   └── types.ts
│   └── images/
│       └── ...
├── pages/                           # Route pages (thin orchestrators)
│   ├── Home.svelte
│   ├── Login.svelte
│   ├── Game.svelte
│   └── Profile.svelte
└── types/                           # Global TypeScript types
```

### HTTP Service Pattern

**Shared Axios Client (`shared/api/client.ts`):**

```typescript
import axios from 'axios';
import { authInterceptor } from './interceptors/auth.interceptor';
import { errorInterceptor } from './interceptors/error.interceptor';

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  headers: { 'Content-Type': 'application/json' },
});

// Attach auth token to all requests
apiClient.interceptors.request.use(authInterceptor);

// Transform errors consistently
apiClient.interceptors.response.use((response) => response, errorInterceptor);
```

**Auth Interceptor (`shared/api/interceptors/auth.interceptor.ts`):**

```typescript
import type { InternalAxiosRequestConfig } from 'axios';
import { getAccessToken } from '$lib/shared/auth/msalInstance';

export async function authInterceptor(
  config: InternalAxiosRequestConfig
): Promise<InternalAxiosRequestConfig> {
  const token = await getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}
```

**Domain HTTP Service (`domains/users/api/users.service.ts`):**

```typescript
import { apiClient } from '$lib/shared/api/client';
import type { User, UpdateProfileDto } from '../types';

export const usersService = {
  getMe: () =>
    apiClient.get<User>('/v1/users/me').then((r) => r.data),

  updateProfile: (data: UpdateProfileDto) =>
    apiClient.patch<User>('/v1/users/me', data).then((r) => r.data),

  getById: (id: string) =>
    apiClient.get<User>(`/v1/users/${id}`).then((r) => r.data),
};
```

### Svelte Query Integration

**Query Definitions (`domains/users/queries/users.queries.ts`):**

```typescript
import { usersService } from '../api/users.service';

export const userQueries = {
  me: () => ({
    queryKey: ['users', 'me'],
    queryFn: () => usersService.getMe(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  }),

  byId: (id: string) => ({
    queryKey: ['users', id],
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

For mutations that benefit from instant UI feedback:

```typescript
// domains/users/queries/useUpdateProfile.ts
import { createMutation, useQueryClient } from '@tanstack/svelte-query';
import { usersService } from '../api/users.service';
import type { UpdateProfileDto, User } from '../types';

export function createUpdateProfileMutation() {
  const queryClient = useQueryClient();

  return createMutation({
    mutationFn: (data: UpdateProfileDto) => usersService.updateProfile(data),

    // Optimistic update - instant UI feedback
    onMutate: async (newData) => {
      // Cancel outgoing refetches to avoid overwriting optimistic update
      await queryClient.cancelQueries({ queryKey: ['users', 'me'] });

      // Snapshot previous value for rollback
      const previousUser = queryClient.getQueryData<User>(['users', 'me']);

      // Optimistically update cache
      queryClient.setQueryData<User>(['users', 'me'], (old) => ({
        ...old!,
        ...newData,
      }));

      return { previousUser };
    },

    // Rollback on error
    onError: (err, newData, context) => {
      if (context?.previousUser) {
        queryClient.setQueryData(['users', 'me'], context.previousUser);
      }
    },

    // Refetch to ensure consistency
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['users', 'me'] });
    },
  });
}
```

**Usage:**

```svelte
<script lang="ts">
  import { createUpdateProfileMutation } from '$lib/domains/users/queries/useUpdateProfile';

  const updateProfile = createUpdateProfileMutation();

  async function handleSubmit() {
    $updateProfile.mutate({ username: newUsername });
  }
</script>

<button on:click={handleSubmit} disabled={$updateProfile.isPending}>
  {$updateProfile.isPending ? 'Saving...' : 'Save'}
</button>
```

### Error Boundaries

Error boundaries catch unexpected runtime errors and display a fallback UI:

```svelte
<!-- shared/components/ErrorBoundary.svelte -->
<script lang="ts">
  import { onMount } from 'svelte';

  let hasError = false;
  let error: Error | null = null;

  function handleError(e: Error) {
    hasError = true;
    error = e;
    console.error('ErrorBoundary caught:', e);
  }

  function reset() {
    hasError = false;
    error = null;
  }
</script>

<svelte:boundary onError={handleError}>
  {#if hasError}
    <div class="error-fallback">
      <h2>Something went wrong</h2>
      <p>{error?.message}</p>
      <button on:click={reset}>Try again</button>
    </div>
  {:else}
    <slot />
  {/if}
</svelte:boundary>
```

**Usage:**

```svelte
<ErrorBoundary>
  <GameBoard />
</ErrorBoundary>
```

**Note:** Svelte Query handles API errors gracefully via `isError` state. Error boundaries catch unexpected runtime errors (render crashes, etc.).

### Routing with svelte-spa-router

```typescript
// routes.ts
import Home from './pages/Home.svelte';
import Login from './pages/Login.svelte';
import Game from './pages/Game.svelte';
import Profile from './pages/Profile.svelte';

export const routes = {
  '/': Home,
  '/login': Login,
  '/game/:id': Game,
  '/profile': Profile,
};
```

```svelte
<!-- App.svelte -->
<script>
  import Router from 'svelte-spa-router';
  import { routes } from './routes';
  import { QueryClientProvider } from '@tanstack/svelte-query';
  import { queryClient } from '$lib/shared/api/queryClient';
  import ErrorBoundary from '$lib/shared/components/ErrorBoundary.svelte';
</script>

<ErrorBoundary>
  <QueryClientProvider client={queryClient}>
    <Router {routes} />
  </QueryClientProvider>
</ErrorBoundary>
```

### Frontend Guidelines

- **Domains own their vertical slice** - API service, queries, components, types
- **Pages are thin orchestrators** - Compose domain components, handle routing params
- **Shared code** is truly cross-domain (axios client, auth, common UI components)
- **Use Svelte Query** for all server state - avoid duplicating in stores
- **Stores** are for client-only state (UI state, form state, etc.)
- **Optimistic updates** for mutations where instant feedback improves UX
- **Error boundaries** wrap major sections to prevent full-page crashes

---

## Storage Decisions

### Image Storage (S3-Compatible via DigitalOcean Spaces)

- **What we store**: Campus photo assets used for game rounds, uploaded by admins.
- **Why S3-compatible storage**: Simple, cost-effective object storage that scales with image volume and integrates cleanly with CDN or public delivery later.
- **Current scope**: Keep it simple; only original uploads are stored for now.

### Upload Pipeline and Metadata

- **Admin upload endpoint**: The API includes an admin-only upload endpoint that accepts images from iPhones.
- **EXIF extraction**: GPS metadata is extracted from EXIF and used to seed location data into MongoDB.
- **S3 object keys**: Images are stored under an `images/` prefix with unique IDs.
