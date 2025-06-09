FROM python:3.10-bookworm

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive \
    GDAL_VERSION=3.4.3 \
    GEOS_VERSION=3.11.2 \
    PROJ_VERSION=9.3.1

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
    python3-dev \
    python3-pip \
    python3-setuptools \
    swig \
    libsqlite3-0 \
    sqlite3 \
    libtiff5 \
    libcurl4 \
    && rm -rf /var/lib/apt/lists/*

# Install PROJ from source
RUN wget https://download.osgeo.org/proj/proj-${PROJ_VERSION}.tar.gz \
    && tar -xzf proj-${PROJ_VERSION}.tar.gz \
    && cd proj-${PROJ_VERSION} \
    && mkdir build && cd build \
    && cmake .. \
        -DCMAKE_BUILD_TYPE=Release \
        -DBUILD_TESTING=OFF \
        -DBUILD_PYTHON_BINDINGS=OFF \
        -DENABLE_CURL=OFF \
        -DRUN_NETWORK_DEPENDENT_TESTS=OFF \
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
    && ./configure \
        --with-geos=yes \
        --with-proj=/usr/local \
        --without-python \
        --without-curl \
        --without-xml2 \
    && make -j$(nproc) \
    && make install \
    && cd .. \
    && rm -rf gdal-${GDAL_VERSION}*

# Configure environment
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal \
    C_INCLUDE_PATH=/usr/include/gdal \
    PROJ_LIB=/usr/local/share/proj \
    LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH

# Update linker cache
RUN ldconfig

# Set working directory
WORKDIR /app

# Upgrade pip
RUN pip install --upgrade pip setuptools wheel

# Install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install GDAL Python bindings
RUN pip install --no-cache-dir "gdal==$(gdal-config --version).*"

# Copy application code
COPY . .

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]