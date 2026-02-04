# Architecture

## Tech Stack

- **Backend**: FastAPI (Python 3.12) with UV package manager
- **Frontend**: Svelte + Vite + TypeScript + Tailwind CSS
- **Database**: MongoDB
- **Cache**: Redis
- **Authentication**: Microsoft OAuth (Azure AD)
- **Containerization**: Docker + Docker Compose

## Backend Architecture

The backend follows a layered architecture pattern for separation of concerns:

```
Request → Controller → Service → Repository → MongoDB
              ↓           ↓
           Models     Entities
```

### Layers

| Layer | Location | Responsibility |
|-------|----------|----------------|
| **Controllers** | `app/api/v1/` | HTTP request/response handling, routing, input validation |
| **Models** | `app/models/` | Pydantic schemas for API request/response contracts |
| **Services** | `app/services/` | Business logic and orchestration |
| **Repositories** | `app/repositories/` | Database CRUD operations |
| **Entities** | `app/entities/` | MongoDB document schemas |

### Dependency Injection

We use **Protocol-based dependency injection** for testability:

- Repositories define a `Protocol` interface (e.g., `IUserRepository`)
- Services depend on the Protocol, not the concrete implementation
- Controllers wire up dependencies via FastAPI's `Depends()`

This allows easy mocking in tests without additional DI libraries.

```python
# Example: Repository Protocol
class IUserRepository(Protocol):
    async def find_by_microsoft_oid(self, oid: str) -> dict | None: ...

# Example: Service using Protocol
class UserService:
    def __init__(self, user_repository: IUserRepository) -> None:
        self.user_repository = user_repository
```

### Guidelines

- **Controllers** should be thin - no business logic or direct database access
- **Services** contain business logic and call repositories for data access
- **Repositories** are the only layer that interacts with the database
- **Models** define the API contract (what clients send/receive)
- **Entities** define the database contract (what gets stored)

## Storage Decisions

### Image Storage (S3-Compatible via DigitalOcean Spaces)

- **What we store**: Campus photo assets used for game rounds, uploaded by admins.
- **Why S3-compatible storage**: Simple, cost-effective object storage that scales with image volume and integrates cleanly with CDN or public delivery later.
- **Current scope**: Keep it simple; only original uploads are stored for now.

### Upload Pipeline and Metadata

- **Admin upload endpoint**: The API includes an admin-only upload endpoint that accepts images from iPhones.
- **EXIF extraction**: GPS metadata is extracted from EXIF and used to seed location data into MongoDB.
- **S3 object keys**: Images are stored under an `images/` prefix with unique IDs.
