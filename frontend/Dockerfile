# ============================================================
# AI Healthcare System — Frontend Dockerfile (Multi-Stage Vite)
# ============================================================
# Stage 1: Build static assets
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies (cached layer)
COPY package.json package-lock.json ./
RUN npm ci

# Copy source and build
COPY . .
ARG NEXT_PUBLIC_API_URL
ARG VITE_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV VITE_PUBLIC_API_URL=$VITE_PUBLIC_API_URL

RUN npm run build

# --- Stage 2: Production Nginx Server ---
FROM nginx:stable-alpine AS runner

# Copy built static files to Nginx web directory
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom Nginx configuration to support SPA routing
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]
