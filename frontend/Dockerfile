# Multi-stage build for production
FROM node:18-alpine as builder

WORKDIR /app

# Copy package files first (for better caching)
COPY package*.json ./
COPY vite.config.js ./
COPY index.html ./

# Install dependencies
RUN npm install

# Copy source files
COPY src/ ./src/

# Build the app
RUN npm run build

# Production stage
FROM nginx:alpine

# Install curl for health checks
RUN apk add --no-cache curl

# Copy built app to nginx
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:80 || exit 1

CMD ["nginx", "-g", "daemon off;"]