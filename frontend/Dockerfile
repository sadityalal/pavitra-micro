FROM node:18-alpine as build

WORKDIR /app

# Copy package files first (for better caching)
COPY package*.json ./
COPY vite.config.js ./
COPY index.html ./

# Install ALL dependencies including axios
RUN npm install

# Copy source files
COPY src/ ./src/

# Build the app
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built app to nginx
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
