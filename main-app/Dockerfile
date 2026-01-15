# syntax=docker/dockerfile:1
FROM node:20-slim

WORKDIR /app

# Copy package.json & package-lock first for caching
COPY package*.json ./

# Cache npm downloads between builds
RUN --mount=type=cache,target=/root/.npm \
    npm install

# Copy rest of the source
COPY . .

EXPOSE 3001

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3001"]
