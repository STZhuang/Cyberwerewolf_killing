# Vue.js Frontend Dockerfile
# Multi-stage build with development, build, and production stages

# Development stage
FROM node:18-alpine as development

# Install development dependencies
RUN apk add --no-cache git curl

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Create non-root user for development
RUN addgroup -g 1001 -S appuser && \
    adduser -S nextjs -u 1001

# Expose port
EXPOSE 3000

# Health check for development
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/ || exit 1

# Default command for development
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# Build stage
FROM node:18-alpine as build

# Install build dependencies
RUN apk add --no-cache git

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build application with optimizations
RUN npm run build

# Production stage
FROM nginx:alpine as production

# Install required packages
RUN apk add --no-cache curl

# Create non-root user
RUN addgroup -g 1001 -S appuser && \
    adduser -S nextjs -u 1001

# Copy built app
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Create directories for cache and logs
RUN mkdir -p /var/cache/nginx /var/log/nginx /var/lib/nginx/tmp && \
    chown -R appuser:appuser /var/cache/nginx /var/log/nginx /var/lib/nginx/tmp

# Copy custom nginx configuration if needed
COPY --chown=appuser:appuser .docker/nginx/nginx.conf /etc/nginx/nginx.conf

# Security optimizations
RUN rm -rf /etc/nginx/conf.d/default.conf && \
    touch /etc/nginx/conf.d/.keep

# Expose port
EXPOSE 80

# Health check for production
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

# Add metadata labels
LABEL maintainer="Cyber Werewolves Team"
LABEL version="1.0.0"
LABEL description="Cyber Werewolves Frontend Service"

# Security and optimization
# Switch to non-root user
USER appuser

# Start nginx with optimized configuration
CMD ["nginx", "-g", "daemon off;"]