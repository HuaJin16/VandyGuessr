# syntax=docker/dockerfile:1

# ================================
# Base stage
# ================================
FROM node:20-slim AS base

WORKDIR /app

# Enable pnpm
RUN corepack enable && corepack prepare pnpm@latest --activate

# ================================
# Development stage
# ================================
FROM base AS development

# Copy package files
COPY package.json pnpm-lock.yaml* ./

# Install dependencies
RUN pnpm install

# Copy application code
COPY . .

EXPOSE 5173

CMD ["pnpm", "dev", "--host"]

# ================================
# Build stage
# ================================
FROM base AS build

# Copy package files
COPY package.json pnpm-lock.yaml* ./

# Install dependencies
RUN pnpm install --frozen-lockfile

# Copy application code
COPY . .

# Build the application
RUN pnpm build
