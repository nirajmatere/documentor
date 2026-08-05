FROM python:3.10-slim

# Install system dependencies required by python packages
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Documentor source into the container
COPY . /app/documentor-src

# Install the package
RUN pip install --no-cache-dir /app/documentor-src

# Setup entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# GitHub Actions maps the user's repo to /github/workspace and sets it as the working directory.
ENTRYPOINT ["/entrypoint.sh"]
