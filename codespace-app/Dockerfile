# syntax=docker/dockerfile:1
FROM node:20-slim

WORKDIR /app

# Copy shared package first
COPY packages/shared /app/packages/shared

# Copy app package files
COPY codespace-app/package*.json ./codespace-app/

# Install dependencies with workspace link
WORKDIR /app/codespace-app
RUN --mount=type=cache,target=/root/.npm \
    npm install --install-links

# Copy rest of the source
COPY codespace-app/ ./

EXPOSE 3002

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3002"]
