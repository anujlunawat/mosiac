FROM node:lts-alpine AS builder

WORKDIR /frontend

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build


FROM nginx:alpine AS production

WORKDIR /frontend
# Remove default nginx content
RUN rm -rf /usr/share/nginx/html/*
COPY --from=builder /frontend/dist /frontend/dist
