FROM node:20-slim AS build

WORKDIR /app

# Copy shared package
COPY packages/shared ./packages/shared

# Copy frontend package files
COPY frontend/package*.json ./frontend/

WORKDIR /app/frontend
RUN npm install --install-links

# Copy source and build
COPY frontend/ ./
RUN npm run build


# =========================
# Runtime (nginx)
# =========================
FROM nginx:1.25-alpine

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy your nginx config
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Copy built frontend
COPY --from=build /app/frontend/dist /usr/share/nginx/html

EXPOSE 1643

CMD ["nginx", "-g", "daemon off;"]
