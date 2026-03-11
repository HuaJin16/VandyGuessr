# Architecture

## Tech Stack

- **Backend**: FastAPI (Python 3.12) with uv package manager
- **Frontend**: Svelte 4 + Vite + TypeScript + Tailwind CSS
- **Database**: MongoDB
- **Cache**: Redis
- **Authentication**: Microsoft OAuth (Azure AD)
- **Containerization**: Docker + Docker Compose

### Additional Libraries

| Layer    | Library                     | Purpose                             |
| -------- | --------------------------- | ----------------------------------- |
| Backend  | `lagom`                     | Dependency injection container      |
| Backend  | `structlog`                 | Structured JSON logging             |
| Frontend | `axios`                     | HTTP client                         |
| Frontend | `@tanstack/svelte-query`    | Server-state management and caching |
| Frontend | `svelte-routing`            | History-mode client-side routing    |
| Frontend | `tailwind-variants`         | Variant-based component styling     |
| Frontend | `@photo-sphere-viewer/core` | Panorama viewer for game rounds     |
| Frontend | `leaflet`                   | Interactive map rendering           |
| Frontend | `svelte-sonner`             | Toast notifications                 |

---

## Design Decisions

| Decision                                 | Why we chose it                                                                                                                                                                                                                               |
| ---------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Svelte 4 SPA over React**              | The team already had React experience and wanted to build this project with a lighter framework and different developer experience.                                                                                                           |
| **FastAPI for backend APIs**             | FastAPI gave us async support, strong typing, and rapid API iteration for a small team.                                                                                                                                                       |
| **DDD-style domain organization**        | We preferred organizing the codebase by feature domain rather than a traditional layer-first or MVC-style structure, so routes, business logic, and persistence for each feature stay close together and are easier to understand and evolve. |
| **MongoDB as primary datastore**         | Core gameplay data, such as games with embedded rounds, maps naturally to document-shaped storage, and MongoDB’s geospatial query support also fits our location-matching workflow for campus images and landmarks.                           |
| **Redis for leaderboard caching**        | Leaderboard queries require aggregation over many completed games, so Redis caches page-level results to reduce repeated database work and improve response times for frequently requested views.                                             |
| **DigitalOcean Spaces for image assets** | S3-compatible object storage is a better fit for large image assets than the primary database, and it allows uploads and delivery to scale without routing image traffic through the backend.                                                 |
| **lagom for dependency injection**       | Centralized dependency wiring keeps route handlers lightweight and improves modularity and testability across domains.                                                                                                                        |
| **Svelte Query for server state**        | Svelte Query centralizes async server-state fetching, caching, and revalidation, which reduces custom fetch/store boilerplate and keeps server data concerns separate from client-only UI state.                                              |
| **Demo mode support**                    | Reviewers can run the project without Vanderbilt OAuth setup or external object storage access.                                                                                                                                               |

---

## Backend Architecture

### Domain-Driven Design (DDD) Structure

The backend is organized by business domain so each feature keeps routing, logic, and persistence close together.
Each domain typically contains `router.py`, `service.py`, `repository.py`, `entities.py`, and `models.py`.

```text
apps/api/app/
|- main.py                          # FastAPI entry point and app wiring
|- config.py                        # Pydantic settings
|- container.py                     # Lagom DI container + deps helper
|- core/                            # Shared infrastructure
|  |- db/                           # MongoDB/Redis client provider
|  |- http/                         # HTTP response helpers and exceptions
|  |- auth/                         # OAuth/JWT verification
|- domains/                         # Business domains
|  |- users/
|  |- games/
|  |- images/
|  |- locations/
|  |- leaderboard/
|  |- multiplayer/
\- shared/                          # Cross-cutting utilities
   |- exif.py                       # EXIF metadata extraction
   |- s3.py                         # S3/Spaces upload helpers
   \- scoring.py                    # Distance and score calculations
```

### Backend Domain Explanations

| Domain        | Purpose                                                                              | What the domain contains                                                                                                                           |
| ------------- | ------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| `users`       | Manages user identity/profile records and profile stats.                             | `router.py` for `/v1/users`, `service.py` for create-or-get logic, `repository.py` for user collection access, plus `entities.py` and `models.py`. |
| `games`       | Runs single-player game lifecycle, round submission, and score distribution metrics. | Endpoints, business rules, repository methods, document schemas, response models, and deterministic daily challenge helpers in `daily.py`.         |
| `images`      | Handles photo ingestion pipeline used to build playable rounds.                      | Upload endpoint/form, file validation, EXIF parsing, object-storage upload, metadata persistence, and upload response models.                      |
| `locations`   | Resolves lat/lng to campus location names via geospatial matching.                   | Internal-only service/repository/entity (no public router); used by games and images domains.                                                      |
| `leaderboard` | Produces leaderboard pages and user rank context with caching.                       | Router, timeframe/caching service logic, aggregation-heavy repository, and API response models.                                                    |
| `multiplayer` | Supports multiplayer lobby flow, real-time game state, and WebSocket events.         | HTTP + WebSocket routes, multiplayer service logic, persistence, socket managers, event constants, entities, and models.                           |

### Request Flow

```text
Request -> router.py -> service.py -> repository.py -> MongoDB/Redis
            |            |
          models.py   entities.py
```

### Backend Layer Responsibilities

| Layer            | Location                  | Responsibility                                            |
| ---------------- | ------------------------- | --------------------------------------------------------- |
| **Routers**      | `domains/*/router.py`     | HTTP request/response handling, routing, input validation |
| **Models**       | `domains/*/models.py`     | Pydantic schemas for API request/response contracts       |
| **Services**     | `domains/*/service.py`    | Business logic and orchestration                          |
| **Repositories** | `domains/*/repository.py` | Database CRUD and aggregation operations                  |
| **Entities**     | `domains/*/entities.py`   | MongoDB document schemas                                  |

### Dependency Injection with Lagom

Dependency wiring is centralized in `container.py`. Repositories and services are resolved through the container, and routers request dependencies with a single helper.

```python
container[IUserRepository] = UserRepository
container[UserService] = UserService
container[IGameRepository] = GameRepository
container[GameService] = GameService

def deps[T](cls: type[T]) -> T:
    return Depends(lambda: container.resolve(cls))
```

This keeps route handlers thin while making domain wiring explicit.

### Logging with Structlog

The API uses `structlog` for structured JSON logs so service and router events are emitted as key-value fields instead of free-form strings. This makes logs easier to filter by event name, user ID, endpoint, and error context.

### Health Endpoint

The API exposes `/health` and returns service status plus runtime metadata (`VERSION`, `GIT_SHA`, `GIT_BRANCH`) when available.

### Backend Guidelines

- **Routers** stay thin: no business logic and no direct database access
- **Services** own business rules and orchestration
- **Repositories** are the only layer that talks to MongoDB/Redis
- **Models** define the API contract (client input/output)
- **Entities** define the storage contract (database shape)
- **Dependencies** are registered in `container.py`

---

## Frontend Architecture

### Domain-Driven Design (DDD) Structure

The frontend follows the same domain-first structure under `src/lib`, with pages as thin route-level orchestrators.
Each domain typically contains `api/`, `queries/`, `components/`, `types.ts`, and optionally `stores/` for client-side state.

```text
apps/web/src/
|- main.ts                          # Application entry
|- App.svelte                       # Root shell, providers, routes
|- app.css                          # Global styles
\- lib/
   |- pages/                        # Route-level pages (thin orchestrators)
   |- domains/                      # Business domains
   |  |- users/
   |  |- games/
   |  |- leaderboard/
   |  |- multiplayer/
   \- shared/                       # Cross-domain infrastructure
      |- api/                        # Axios client, interceptors, and query config
      |- auth/                       # MSAL configuration and auth state
      |- components/                 # Shared layout and common app components
      \- ui/                         # Reusable styled primitives
```

### Frontend Domain Explanations

| Domain        | Purpose                                                            | What the domain contains                                                                                      |
| ------------- | ------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------- |
| `users`       | Current-user profile data and profile display components.          | User API calls, user query definitions, user types, and reusable `UserProfile` UI.                            |
| `games`       | Single-player gameplay UI and client-side round interaction state. | Game API/query definitions, gameplay components, and `game.store.ts` for local game UI state.                 |
| `leaderboard` | Leaderboard filter state, pagination, and display components.      | Leaderboard API/query files, view state store, responsive helpers, and leaderboard-specific components/types. |
| `multiplayer` | Multiplayer lobby/game views and realtime socket client.           | Multiplayer API/query files, websocket transport, multiplayer stores, components, and types.                  |
| `shared`      | App-wide infra and reusable primitives.                            | API client/interceptors, auth setup/store, shared layout components, UI primitives, and utilities.            |
| `pages`       | Route-level composition and page orchestration.                    | Thin pages that compose domain components and wire route params/query hooks.                                  |

### Frontend Layer Responsibilities

| Layer        | Location                         | Responsibility                                             |
| ------------ | -------------------------------- | ---------------------------------------------------------- |
| API Services | `domains/*/api/*.service.ts`     | Typed HTTP methods wrapping the shared Axios client        |
| Queries      | `domains/*/queries/*.queries.ts` | Svelte Query factory definitions (keys, fetch, stale time) |
| Components   | `domains/*/components/`          | Domain-specific UI components                              |
| Stores       | `domains/*/stores/`              | Client-only state (gameplay, view, and filter state)       |
| Types        | `domains/*/types.ts`             | TypeScript interfaces and type definitions                 |
| Pages        | `lib/pages/*.svelte`             | Route-level orchestrators wiring domain components         |

### HTTP Service Pattern

All domain services call a shared Axios client (`lib/shared/api/client.ts`) so auth and error behavior are consistent across the app.

```typescript
export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
});

apiClient.interceptors.request.use(authInterceptor);
apiClient.interceptors.response.use((response) => response, errorInterceptor);
```

The request interceptor attaches a Bearer token from MSAL in standard mode and becomes a no-op in demo mode (`VITE_DEMO_MODE=true`). Domain service files then expose typed API methods.

```typescript
export const usersService = {
  getMe: () => apiClient.get<User>("/v1/users/me").then((r) => r.data),
  getById: (id: string) =>
    apiClient.get<User>(`/v1/users/${id}`).then((r) => r.data),
};
```

### Svelte Query Integration

Each domain defines query factories so key structure, stale time, and fetch logic are shared in one place.

```typescript
export const userQueries = {
  me: () => ({
    queryKey: ["users", "me"] as const,
    queryFn: () => usersService.getMe(),
    staleTime: 5 * 60 * 1000,
  }),
};
```

Pages consume these factories and gate requests on auth initialization.

```svelte
$: meQuery = createQuery({ ...userQueries.me(), enabled: $auth.isInitialized });
```

### Mutation and Cache Update Pattern

After successful mutations, pages update Svelte Query cache directly:

```typescript
const updated = await gamesService.submitGuess(game.id, roundNumber, guess);
gameStore.showResults(updated, $gameStore.currentRoundIndex);
queryClient.setQueryData(["games", id], updated);
```

This keeps UI state synchronized immediately after server-confirmed mutations.

### Error Handling Pattern

Response errors are normalized in a shared interceptor into `ApiRequestError` so pages and components can handle a consistent error shape. The same interceptor also logs out an authenticated user on `401` responses, which centralizes session-expiration behavior.

### Routing with svelte-routing

Routes are declared in `apps/web/src/App.svelte` and multiplayer routes are conditionally enabled by feature flag:

```svelte
<QueryClientProvider client={queryClient}>
  <Router>
    <Route path="/" component={Home} />
    <Route path="/game/:id/summary" component={GameSummary} />
    <Route path="/game/:id" component={Game} />
    <Route path="/leaderboard" component={Leaderboard} />
    <Route path="/login" component={Login} />
    {#if multiplayerEnabled}
      <Route path="/multiplayer/:id/lobby" component={MultiplayerLobby} />
      <Route path="/multiplayer/:id" component={MultiplayerGame} />
    {/if}
  </Router>
</QueryClientProvider>
```

### UI Components with Tailwind Variants

Shared UI primitives live in `apps/web/src/lib/shared/ui/`.

```text
apps/web/src/lib/shared/
|- ui/
|  |- index.ts           # Barrel export
|  |- Button.svelte      # Styled button with variants
|  |- Card.svelte        # Container component
|  \- CardContent.svelte # Content wrapper
\- utils.ts              # Class merge helpers
```

UI primitives use `tailwind-variants` for typed variant APIs (such as size and style variants). Class composition uses a shared `cn()` helper (`clsx` + `tailwind-merge`) so consumer overrides and variant classes resolve consistently.

### Frontend Guidelines

- **Domains own their vertical slice**: API service, queries, components, types, and domain-local stores where needed
- **Pages stay thin**: compose domain components and wire route params/state
- **Shared code stays cross-domain**: api client, auth, shared UI, common utilities
- **Svelte Query handles server state** and request caching
- **Svelte stores handle client-only state** (view/filter/interaction state)
- **Routing stays centralized** in `App.svelte`

---

## Infrastructure & Storage

### Deployment Topology

The frontend is deployed as a static Svelte SPA hosted on DigitalOcean Spaces and delivered through a CDN for fast global access. The FastAPI backend runs on DigitalOcean App Platform and handles all application logic and API requests. Persistent data is stored in managed MongoDB, while Redis provides caching for high-frequency queries like leaderboards. Images are stored separately in Spaces so users download them directly via CDN instead of through the backend, reducing server load and improving scalability.

### Image Storage (S3-Compatible via DigitalOcean Spaces)

- **What we store**: Campus photo assets used for game rounds, uploaded by contributors.
- **Why S3-compatible storage**: Simple object storage that scales with image volume.
- **Current scope**: Original uploads are stored in Spaces, while metadata is persisted in MongoDB.

### Upload Pipeline and Metadata

- **Upload endpoint**: Secret-code protected upload endpoint with a mobile-friendly HTML form.
- **EXIF extraction**: GPS metadata is extracted from EXIF and used for location tagging.
- **Object keys**: Images are stored with UUID-based keys under `images/`.
- **MongoDB persistence**: URL, coordinates, environment, and EXIF-derived metadata are stored in `images`.

### Location Resolution

Location data is seeded from OpenStreetMap GeoJSON building and landmark polygons and stored in MongoDB for geospatial lookup. The dataset is imported in an idempotent way so it can be refreshed safely, and geospatial indexes support efficient location matching.

During image ingestion, uploaded photos are automatically matched against this location dataset to attach a human-readable campus location name. The matching process first attempts an exact polygon lookup and then falls back to a nearby-location search when no direct match is found. Existing images can also be backfilled when location names are missing.

Location records store canonical place information such as name, OpenStreetMap identifier, optional building type metadata, and GeoJSON geometry. This keeps location resolution centralized in the backend and allows gameplay, uploads, and summaries to rely on consistent location metadata.

### Gameplay and Leaderboard Persistence

- `games` stores each single-player game as one document with embedded rounds
- Rounds snapshot image URL/coordinates/location name at game creation time
- Leaderboard reads use aggregation pipelines over completed game rounds
- Leaderboard pages are cached in Redis using timeframe/mode/page keys
- Current cache TTLs: daily 300s, weekly 300s, all-time 900s

---

## Runtime Configuration

Key feature flags and mode switches:

- API: `FEATURE_MULTIPLAYER`, `DEMO_MODE`
- Web: `VITE_FEATURE_MULTIPLAYER`, `VITE_DEMO_MODE`

This allows the same codebase to run in standard campus mode or reviewer-friendly demo mode.
