# Use a smaller base image to reduce disk usage
FROM python:3.10-slim-bookworm

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive \
    # Python path configuration
    PYTHONPATH=/app

# Install system dependencies with aggressive cleanup
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
    && \
    # Critical cleanup to save space
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /tmp/* /var/tmp/* && \
    rm -rf /usr/share/man /usr/share/doc /usr/share/info

# Set GDAL environment variables AFTER installation
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal \
    C_INCLUDE_PATH=/usr/include/gdal \
    GDAL_LIBRARY_PATH=/usr/lib/libgdal.so \
    GEOS_LIBRARY_PATH=/usr/lib/libgeos_c.so

# Set working directory
WORKDIR /app

# Upgrade pip and setuptools
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    # Install GDAL bindings matching system version
    pip install --no-cache-dir --no-deps pygdal==3.6.2.*

# Copy application code with .dockerignore to exclude unnecessary files
COPY . .

# Set default command
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]