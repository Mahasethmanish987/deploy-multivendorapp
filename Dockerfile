# ========== BUILDER STAGE ==========
FROM python:3.10-bookworm AS builder

# Install build dependencies (needed to compile pygdal)
RUN apt-get update && \
    apt-get install -y \
    binutils \
    libgdal-dev \
    libgeos-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set GDAL environment for compilation
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal \
    C_INCLUDE_PATH=/usr/include/gdal

WORKDIR /app

# Upgrade pip and create a virtual environment
RUN pip install --upgrade pip
ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install Python dependencies (including pygdal)
COPY requirements.txt .
RUN sed -i '/^gdal==/d' requirements.txt && \
    pip install -r requirements.txt
RUN pip install --no-deps pygdal==3.6.2.*

# ========== FINAL STAGE ==========
FROM python:3.10-bookworm AS final

# Install only runtime libraries (no -dev packages)
# gdal-bin pulls libgdal32 and libgeos-c1v5 automatically
RUN apt-get update && \
    apt-get install -y \
    gdal-bin \
    gettext \
    && rm -rf /var/lib/apt/lists/*

# Set GDAL environment for runtime (point to the shared libs)
ENV GDAL_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/libgdal.so \
    GEOS_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/libgeos_c.so \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Copy the entire virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app
COPY . .

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]