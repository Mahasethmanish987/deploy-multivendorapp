FROM python:3.10-bookworm

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && \
    apt-get install -y \
    binutils \
    gdal-bin \
    libgdal-dev \
    python3-gdal \  # Critical - installs pre-built Python bindings
    libgeos-dev \
    gettext \
    && rm -rf /var/lib/apt/lists/*

# Set GDAL environment variables
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal \
    C_INCLUDE_PATH=/usr/include/gdal \
    GDAL_LIBRARY_PATH=/usr/lib/libgdal.so \
    GEOS_LIBRARY_PATH=/usr/lib/libgeos_c.so

# Install Python dependencies
WORKDIR /app

# Upgrade pip
RUN pip install --upgrade pip

# Remove gdal from requirements before installing
COPY requirements.txt .
RUN sed -i '/^gdal==/d' requirements.txt && \
    pip install -r requirements.txt

# Install GDAL bindings from system package
RUN pip install --no-deps pygdal==3.6.2.*

# Copy application code
COPY . .

# Set default command
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]