# Use lightweight Python base with geospatial support
FROM python:3.11-slim-bullseye

# Install geospatial dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libgdal-dev=3.2.2+dfsg-1+deb11u1 \
    gdal-bin=3.2.2+dfsg-1+deb11u1 \
    proj-bin=7.2.1-1 \
    proj-data=7.2.1-1 \
    binutils=2.36.1-7 \
    libproj-dev=7.2.1-1 \
    && rm -rf /var/lib/apt/lists/*

# Set required environment variables
ENV PROJ_LIB=/usr/share/proj \
    GDAL_LIBRARY_PATH=/usr/lib

# Install Python dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run migrations and application
CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]