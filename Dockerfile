FROM python:3.11-slim

# Install system dependencies including ffmpeg (for video factory) and curl (for uv)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg curl && \
    rm -rf /var/lib/apt/lists/*

# Install uv package manager
RUN curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR="/usr/local/bin" sh

WORKDIR /app

# Copy the entire workspace
COPY . .

# Sync dependencies for all packages in the workspace
RUN uv sync --all-packages

# Set Python path so routers can be resolved from core-api
ENV PYTHONPATH=/app/src/apps/core-api

EXPOSE 8000

# Run the FastAPI server via uv
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
