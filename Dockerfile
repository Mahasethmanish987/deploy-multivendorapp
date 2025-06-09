FROM python:3.10-bookworm

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive \
    GDAL_VERSION=3.4.3 \
    GEOS_VERSION=3.11.2 \
    PROJ_VERSION=9.1.1

# Install system dependencies
RUN apt-get update && \
    apt-get install -y \
    build-essential \
    cmake \
    wget \
    unzip \
    libsqlite3-dev \
    libtiff-dev \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
    libgeos++-dev \
    gettext \
    postgresql-client-13 \
    && rm -rf /var/lib/apt/lists/*

# Install PROJ from source
RUN wget https://download.osgeo.org/proj/proj-${PROJ_VERSION}.tar.gz \
    && tar -xzf proj-${PROJ_VERSION}.tar.gz \
    && cd proj-${PROJ_VERSION} \
    && mkdir build && cd build \
    && cmake .. -DCMAKE_BUILD_TYPE=Release \
    && make -j$(nproc) \
    && make install \
    && cd ../.. \
    && rm -rf proj-${PROJ_VERSION}*

# Install GEOS from source
RUN wget https://download.osgeo.org/geos/geos-${GEOS_VERSION}.tar.bz2 \
    && tar -xjf geos-${GEOS_VERSION}.tar.bz2 \
    && cd geos-${GEOS_VERSION} \
    && mkdir build && cd build \
    && cmake .. -DCMAKE_BUILD_TYPE=Release \
    && make -j$(nproc) \
    && make install \
    && cd ../.. \
    && rm -rf geos-${GEOS_VERSION}*

# Install GDAL from source
RUN wget https://github.com/OSGeo/gdal/releases/download/v${GDAL_VERSION}/gdal-${GDAL_VERSION}.tar.gz \
    && tar -xzf gdal-${GDAL_VERSION}.tar.gz \
    && cd gdal-${GDAL_VERSION} \
    && ./configure --with-geos=yes --with-proj=/usr/local \
    && make -j$(nproc) \
    && make install \
    && cd .. \
    && rm -rf gdal-${GDAL_VERSION}*

# Configure environment
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal \
    C_INCLUDE_PATH=/usr/include/gdal \
    GDAL_LIBRARY_PATH=/usr/local/lib/libgdal.so \
    GEOS_LIBRARY_PATH=/usr/local/lib/libgeos_c.so \
    PROJ_LIB=/usr/local/share/proj \
    LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH

# Update linker cache
RUN ldconfig

# Set working directory
WORKDIR /app

# Upgrade pip
RUN pip install --upgrade pip setuptools wheel

# Install requirements (NumPy is included in requirements.txt)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install GDAL Python bindings AFTER other packages
RUN pip install --no-cache-dir "gdal==$(gdal-config --version).*"

# Verify installations
RUN python -c "import numpy; print(f'NumPy version: {numpy.__version__}')" && \
    python -c "from osgeo import gdal; print(f'GDAL bindings version: {gdal.__version__}')" && \
    gdalinfo --version && \
    geos-config --version && \
    proj

# Copy application code
COPY . .

# Set production-ready command (using Gunicorn)
CMD ["python","manage.py","runserver","0.0.0.0:8000"]