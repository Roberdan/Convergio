# 🎨 Convergio Frontend - Dockerfile

# --- Build Stage ---
FROM node:20-alpine as builder

WORKDIR /app

# Copy package files and install dependencies
COPY package.json package-lock.json ./
RUN npm install

# Copy the rest of the application source code
COPY . .

# Build the application
RUN npm run build

# --- Production Stage ---
FROM nginx:1.25-alpine

# Copy the built assets from the builder stage
COPY --from=builder /app/build /usr/share/nginx/html

# Copy the custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]

LABEL org.opencontainers.image.title="Convergio Frontend"
LABEL org.opencontainers.image.description="AI-powered business orchestration platform frontend"
LABEL org.opencontainers.image.source="https://github.com/Roberdan/Convergio"
LABEL org.opencontainers.image.licenses="CC-BY-NC-SA-4.0"
LABEL org.opencontainers.image.authors="Roberto D'Angelo <roberdan@fightthestroke.org>"

# 📁 Set working directory
WORKDIR /app

# 📦 Copy package files
COPY package*.json ./

# 🔧 Install dependencies
RUN npm ci --only=production

# 📁 Copy source code
COPY . .

# 🏗️ Build application
RUN npm run build

# 🚀 Production stage
FROM nginx:alpine

# 📦 Install curl for health checks
RUN apk add --no-cache curl

# 📁 Copy built application
COPY --from=builder /app/build /usr/share/nginx/html

# 🔧 Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# 👤 Create non-root user
RUN addgroup -g 1001 -S convergio && \
    adduser -S convergio -u 1001

# 🔍 Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:4000/health || exit 1

# 🚀 Expose port
EXPOSE 4000

# 🎯 Start nginx
CMD ["nginx", "-g", "daemon off;"]