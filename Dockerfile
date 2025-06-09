FROM python:3.10-bookworm

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    libproj-dev \
    libgeos-dev \
    python3-gdal \
    build-essential \
    wget \
    unzip \
    gettext \
    python3-dev \
    python3-pip \
    python3-setuptools \
    && rm -rf /var/lib/apt/lists/*

# Configure GDAL and PROJ environment variables
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal \
    C_INCLUDE_PATH=/usr/include/gdal \
    PROJ_LIB=/usr/share/proj \
    LD_LIBRARY_PATH=/usr/lib:$LD_LIBRARY_PATH

# Set working directory
WORKDIR /app

# Upgrade pip
RUN pip install --upgrade pip setuptools wheel

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Python GDAL bindings (matched with installed version)
RUN pip install --no-cache-dir "gdal==$(gdal-config --version).*"

# Copy project code
COPY . .

# Run server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
