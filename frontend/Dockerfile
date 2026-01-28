# STAGE 1: Build the React App
FROM node:20 as builder

WORKDIR /app

# 1. Copy the shared package first (CRITICAL for new code structure)
COPY packages/shared /app/packages/shared

# 2. Copy frontend dependencies
COPY frontend/package*.json ./frontend/

# 3. Install dependencies
WORKDIR /app/frontend
# install-links allows npm to see the local ../packages/shared folder
RUN npm install --install-links

# 4. Copy the rest of the frontend source code
COPY frontend/ ./

# 5. Build Arguments for Environment Variables
ARG VITE_API_BASE_URL
ARG VITE_WS_BASE_URL

# 6. Build for Production
RUN npm run build

# STAGE 2: Serve with Nginx (Like the old server)
FROM nginx:alpine

# WE DELETED THE CRASHING 'rm' COMMAND HERE

# Copy the build output from the builder stage
COPY --from=builder /app/frontend/dist /usr/share/nginx/html

# Copy config
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 1643
CMD ["nginx", "-g", "daemon off;"]