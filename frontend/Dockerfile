FROM node:18-alpine

WORKDIR /app

# Copy package files FIRST
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm install

# Copy source code AFTER installing dependencies
COPY . .

# Build the app
RUN npm run build

# Expose port
EXPOSE 3000

# Serve the app
CMD ["npm", "run", "preview"]
