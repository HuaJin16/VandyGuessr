# syntax=docker/dockerfile:1

# ================================
# Base stage
# ================================
FROM python:3.12-slim AS base

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# ================================
# Development stage
# ================================
FROM base AS development

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies
RUN uv sync --frozen --no-install-project

# Copy application code
COPY . .

# Install the project
RUN uv sync --frozen

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ================================
# Production stage
# ================================
FROM base AS production

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies only (no dev)
RUN uv sync --frozen --no-install-project --no-dev

# Copy application code
COPY . .

# Install the project
RUN uv sync --frozen --no-dev

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
