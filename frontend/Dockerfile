FROM node:18-alpine as builder

WORKDIR /app

# Copy package files first
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm install

# Copy all source files
COPY public/ ./public/
COPY src/ ./src/

# Build the app
RUN npm run build

FROM nginx:alpine

# Copy built app to nginx
COPY --from=builder /app/build /usr/share/nginx/html

# Copy nginx configuration
COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf

# Create a simple health check
RUN echo '#!/bin/sh' > /healthcheck.sh && \
    echo 'if [ -f /usr/share/nginx/html/index.html ]; then exit 0; else exit 1; fi' >> /healthcheck.sh && \
    chmod +x /healthcheck.sh

# Add security headers
RUN echo "server_tokens off;" >> /etc/nginx/nginx.conf

# Create nginx user with proper permissions
RUN chown -R nginx:nginx /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD /healthcheck.sh

CMD ["nginx", "-g", "daemon off;"]
