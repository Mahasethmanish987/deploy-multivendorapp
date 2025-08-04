# Stage 1: Build stage with all dependencies
FROM python:3.10-slim-bookworm as builder

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies with build tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        binutils=2.40-2 \
        gdal-bin \
        libgdal-dev \
        python3-gdal \
        libgeos-dev \
        gettext \
        proj-bin \
        libspatialite-dev \
        build-essential \
        libcairo2-dev \
        libfreetype6-dev \
        pkg-config \
    && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Upgrade pip and setuptools
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir --no-deps pygdal==3.6.2.*

# Stage 2: Final runtime image
FROM python:3.10-slim-bookworm

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive \
    PYTHONPATH=/app \
    # GDAL configuration
    CPLUS_INCLUDE_PATH=/usr/include/gdal \
    C_INCLUDE_PATH=/usr/include/gdal \
    GDAL_LIBRARY_PATH=/usr/lib/libgdal.so \
    GEOS_LIBRARY_PATH=/usr/lib/libgeos_c.so \
    # Static files configuration
    STATIC_ROOT=/app/staticfiles \
    STATIC_URL=/static/

# Install runtime dependencies only
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        binutils=2.40-2 \
        gdal-bin \
        libgdal32 \
        python3-gdal \
        libgeos-c1v5 \
        gettext \
        proj-bin \
        libspatialite7 \
    && \
    # Clean up aggressively
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /tmp/* /var/tmp/* && \
    rm -rf /usr/share/man /usr/share/doc /usr/share/info

# Set working directory
WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Set default command
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]