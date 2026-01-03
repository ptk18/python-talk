# Frontend uses Node
FROM node:20

WORKDIR /app

# Copy package.json & package-lock first for caching
COPY package*.json ./

# Install dependencies - remove lock file to avoid npm optional dependencies bug
RUN rm -f package-lock.json && npm install

# Copy environment files first
COPY .env* ./

# Copy rest of the source
COPY . .

# Build args for environment variables
ARG VITE_API_BASE_URL
ARG VITE_WS_BASE_URL

# Build
RUN npm run build

# Use Nginx to serve
FROM nginx:alpine
RUN rm -rf /usr/share/nginx/html/*
COPY --from=0 /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 1643
CMD ["nginx", "-g", "daemon off;"]