# ==============================================================================
# MIRROR CITY Frontend Production Dockerfile (Multi-stage Build)
# ==============================================================================

# --- Stage 1: Build static bundle ---
FROM node:20-slim AS builder

WORKDIR /app

# Copy dependency configs
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source files
COPY . .

# Build for production
RUN npm run build

# --- Stage 2: Serve with Nginx ---
FROM nginx:alpine

# Copy built artifacts from stage 1 to Nginx default folder
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom Nginx configuration to support SPA routing (Vite React Router fallback)
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
