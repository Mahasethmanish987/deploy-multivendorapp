
FROM python:3.10-bookworm AS builder
RUN apt-get update && \
    apt-get install -y \
    binutils \
    libgdal-dev \
    libgeos-dev \
    gcc \
    g++ \
    && 
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal \
    C_INCLUDE_PATH=/usr/include/gdal
WORKDIR /app
RUN pip install --upgrade pip
ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
COPY requirements.txt .
RUN sed -i '/^gdal==/d' requirements.txt && \
    pip install -r requirements.txt
RUN pip install --no-deps pygdal==3.6.2.*
FROM python:3.10-bookworm AS final
RUN apt-get update && \
    apt-get install -y \
    gdal-bin \
    libgdal30 \
    libgeos-c1v5 \
    gettext \
    && rm -rf /var/lib/apt/lists/*
ENV GDAL_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/libgdal.so \
    GEOS_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/libgeos_c.so \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app
COPY . .

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]