# Stage 1: Build React App
# FROM node:18 AS builder

# WORKDIR /MCMC-POC

# # Copy package.json and package-lock.json first (for better caching)
# COPY package*.json ./

# # Clean npm cache & install dependencies
# RUN npm cache clean --force
# RUN npm install

# # Copy all project files
# COPY . .

# # Increase heap memory, disable source maps
# ENV NODE_OPTIONS="--max-old-space-size=12288"
# ENV GENERATE_SOURCEMAP=false

# # Run the build process
# RUN npm run build

# # Stage 2: Serve the app using Nginx
# FROM nginx:latest

# # Copy built React app from builder stage to Nginx
# COPY --from=builder /MCMC-POC/build /usr/share/nginx/html

# # Expose port 80 for serving the application
# EXPOSE 80

# # Start Nginx
# CMD ["nginx", "-g", "daemon off;"]




# Old docker file
# Use an official Node.js runtime as the base image
# FROM node:18 AS builder
FROM node:18-alpine

#ENV NODE_VERSION 18.18.0
# Set the working directory
WORKDIR /MCMC-POC

# Copy package.json and package-lock.json
COPY package*.json ./


# RUN apk add --no-cache python3
RUN npm cache clean --force

# Install dependencies
RUN npm install
# Copy the rest of the app's files
COPY . .

# Build the app
RUN NODE_OPTIONS="--max-old-space-size=8192" npm run build
#RUN CI=true npm run build


# Expose the port that the app will run on
EXPOSE 3000

##Specify the command to run when the container starts
CMD ["npm", "start"]

