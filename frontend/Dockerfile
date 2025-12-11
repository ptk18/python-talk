# Frontend uses Node
FROM node:20

WORKDIR /app

# Copy package.json & package-lock first for caching
COPY package*.json ./

# Install dependencies - remove lock file to avoid npm optional dependencies bug
RUN rm -f package-lock.json && npm install

# Copy rest of the source
COPY . .

# Build
RUN npm run build

# Use Nginx to serve
FROM nginx:alpine
RUN rm -rf /usr/share/nginx/html/*
COPY --from=0 /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 5173
CMD ["nginx", "-g", "daemon off;"]