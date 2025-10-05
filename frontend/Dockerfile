# Stage 1: Build the React application
FROM node:18-alpine as builder

WORKDIR /app

COPY app/package.json ./
# Use npm ci for reproducible builds if package-lock.json is present
RUN npm install

COPY app/ /app/

RUN npm run build

# Stage 2: Serve the built application from a lightweight server
FROM node:18-alpine

WORKDIR /app

# Install a simple server
RUN npm install -g serve

# Copy built assets from the builder stage
COPY --from=builder /app/dist /app/dist

# Expose the port the server will run on
EXPOSE 3000

# Command to serve the app
CMD ["serve", "-s", "dist", "-l", "3000"]