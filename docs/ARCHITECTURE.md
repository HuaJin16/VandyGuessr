# Architecture

## Tech Stack

- **Backend**: FastAPI (Python 3.12) with UV package manager
- **Frontend**: Svelte + Vite + TypeScript + Tailwind CSS
- **Database**: MongoDB
- **Cache**: Redis
- **Authentication**: Microsoft OAuth (Azure AD)
- **Containerization**: Docker + Docker Compose

## Storage Decisions

### Image Storage (S3-Compatible via DigitalOcean Spaces)

- **What we store**: Campus photo assets used for game rounds, uploaded by admins.
- **Why S3-compatible storage**: Simple, cost-effective object storage that scales with image volume and integrates cleanly with CDN or public delivery later.
- **Current scope**: Keep it simple; only original uploads are stored for now.

### Upload Pipeline and Metadata

- **Admin upload endpoint**: The API includes an admin-only upload endpoint that accepts images from iPhones.
- **EXIF extraction**: GPS metadata is extracted from EXIF and used to seed location data into MongoDB.
- **S3 object keys**: Images are stored under an `images/` prefix with unique IDs.
