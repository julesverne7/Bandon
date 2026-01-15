# Use Python 3.12 slim image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install pipenv
RUN pip install pipenv


# Copy Pipfile and Pipfile.lock
COPY Pipfile Pipfile.lock ./

# Install Python dependencies
RUN pipenv install --system --deploy --ignore-pipfile

# Copy project files
COPY . .

# Create necessary directories
RUN mkdir -p /app/media/uploads /app/media/results /app/media/visualizations /app/staticfiles

# Static files will be collected at runtime

# Expose port
EXPOSE 8000

# Run the application with Daphne (for WebSocket support)
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "backend.asgi:application"]
