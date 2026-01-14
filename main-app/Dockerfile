# Frontend uses Node
FROM node:20

WORKDIR /app

# Copy package.json & package-lock first for caching
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy rest of the source
COPY . .

# Expose port
EXPOSE 3001

# Run dev server
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3001"]
