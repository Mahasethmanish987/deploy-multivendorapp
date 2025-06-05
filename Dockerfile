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
    libgeos-dev \
    gettext \
    && rm -rf /var/lib/apt/lists/*

# Create symlinks for both GDAL and GEOS
RUN for lib in gdal geos_c; do \
        LIB_PATH=$(find /usr -name "lib${lib}.so*" | head -1); \
        echo "Found $lib library at: $LIB_PATH"; \
        ln -sf $LIB_PATH /usr/lib/lib${lib}.so; \
        echo "Created symlink: /usr/lib/lib${lib}.so → $LIB_PATH"; \
    done

# Verify libraries exist
RUN ls -l /usr/lib/libgdal.so /usr/lib/libgeos_c.so && \
    ldconfig -p | grep -E 'gdal|geos'

# Set environment variables
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal \
    C_INCLUDE_PATH=/usr/include/gdal \
    GDAL_LIBRARY_PATH=/usr/lib/libgdal.so \
    GEOS_LIBRARY_PATH=/usr/lib/libgeos_c.so \
    LD_LIBRARY_PATH=/usr/lib:/usr/lib/x86_64-linux-gnu

# Update linker cache
RUN ldconfig

# Install Python dependencies
WORKDIR /app

# Upgrade pip
RUN pip install --upgrade pip

# Install requirements
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application code
COPY . .

# Set default command
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]