# Build stage
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files first (for better caching)
COPY package.json ./

# Install all dependencies and generate package-lock.json
RUN npm install

# Copy source code
COPY . .

# Build the app
RUN npm run build

# Production stage
FROM nginx:alpine

# Install curl for healthcheck
RUN apk add --no-cache curl

# Copy built app to nginx
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy healthcheck script
COPY healthcheck.sh /healthcheck.sh
RUN chmod +x /healthcheck.sh

# Create non-root user for security
RUN addgroup -g 1001 -S nodejs && \
    adduser -S react -u 1001

# Change ownership of nginx files
RUN chown -R react:nodejs /var/cache/nginx && \
    chown -R react:nodejs /var/log/nginx && \
    chown -R react:nodejs /etc/nginx/conf.d

# Create nginx pid directory and set permissions
RUN touch /var/run/nginx.pid && \
    chown -R react:nodejs /var/run/nginx.pid

# Switch to non-root user
USER react

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD /healthcheck.sh

CMD ["nginx", "-g", "daemon off;"]