# Use an official Python runtime as a parent image
FROM --platform=linux/amd64 python:3.11.4-slim

# Install pipenv
RUN pip install pipenv

# Install libpoppler-cpp-dev
# Also, install necessary tools and libraries to build and link software
RUN apt-get update && \
    apt-get install -y \
    apt-utils \
    build-essential \
    cmake \
    pkg-config \
    libpoppler-cpp-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Add a new user and switch to that user
RUN useradd -ms /bin/bash appuser
USER appuser

# Set the working directory in the container to be the same as the current directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY --chown=appuser:appuser . /app

# Install any needed packages specified in Pipfile
RUN pipenv install --deploy --ignore-pipfile

# # Install any needed packages specified in requirements.txt
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# Copy and set executable permissions for the start script
COPY --chown=appuser:appuser docker-deploy.sh /app/docker-deploy.sh
RUN chmod +x /app/docker-deploy.sh

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Start script
CMD sh ./docker-deploy.sh
