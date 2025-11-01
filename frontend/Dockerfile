FROM node:18-alpine as build

WORKDIR /app

# Copy package files first
COPY package.json ./

# Install dependencies and generate package-lock.json
RUN npm install

# Copy the rest of the application
COPY . .

# Build the React app
RUN npm run build

FROM nginx:alpine

# Remove default nginx configuration
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Copy built React app
COPY --from=build /app/build /usr/share/nginx/html

# Copy healthcheck script
COPY healthcheck.sh /healthcheck.sh
RUN chmod +x /healthcheck.sh

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
