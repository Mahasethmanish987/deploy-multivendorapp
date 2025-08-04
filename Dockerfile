FROM python:3.10-bookworm

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive \
    # GDAL configuration
    CPLUS_INCLUDE_PATH=/usr/include/gdal \
    C_INCLUDE_PATH=/usr/include/gdal \
    GDAL_LIBRARY_PATH=/usr/lib/libgdal.so \
    GEOS_LIBRARY_PATH=/usr/lib/libgeos_c.so \
    # Python path configuration
    PYTHONPATH=/app

# Install system dependencies with version pinning
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        binutils=2.40-2 \
        gdal-bin \
        libgdal-dev \
        python3-gdal \
        libgeos-dev \
        gettext \
        # Additional spatial dependencies
        proj-bin \
        libspatialite-dev && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Upgrade pip and setuptools
RUN pip install --no-cache-dir --upgrade pip setuptools

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install GDAL bindings matching system version
RUN pip install --no-cache-dir --no-deps pygdal==3.6.2.*

# Copy application code
COPY . .

# Collect static files (if needed)
# RUN python manage.py collectstatic --noinput

# Set default command
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]