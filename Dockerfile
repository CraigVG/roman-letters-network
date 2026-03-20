# Multi-stage build for Roman Letters static site
# Stage 1: Build the Next.js static site
FROM node:22-alpine AS builder

WORKDIR /app

# Copy package files
COPY site/package.json site/package-lock.json ./
RUN npm ci

# Copy source code and data
COPY site/ ./
COPY data/roman_letters.db ../data/roman_letters.db

# Build static site
ENV NODE_OPTIONS="--max-old-space-size=8192"
RUN npm run build

# Generate search index
RUN npx pagefind --site out || true

# Stage 2: Serve with nginx
FROM nginx:alpine

# Copy static output
COPY --from=builder /app/out /usr/share/nginx/html

# Custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
