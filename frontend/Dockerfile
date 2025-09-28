# Use official Node.js image
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY app/package*.json ./app/

# Install dependencies
WORKDIR /app/app
RUN npm install

# Copy rest of code
COPY app/ .

# Expose port
EXPOSE 3000

# Run frontend
CMD ["npm", "run", "dev", "--", "--host"]
