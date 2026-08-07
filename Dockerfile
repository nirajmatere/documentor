FROM python:3.10-slim AS builder

# Install system dependencies required for building python packages (like tree-sitter)
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Copy Documentor source into the builder
COPY . /build/documentor-src

# Create a virtual environment and install the package
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir /build/documentor-src

# Stage 2: Final Image
FROM python:3.10-slim

# Copy the virtual environment from the builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Install runtime dependencies (git may be needed for resolving .gitignore files)
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Setup entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# GitHub Actions maps the user's repo to /github/workspace and sets it as the working directory.
ENTRYPOINT ["/entrypoint.sh"]
