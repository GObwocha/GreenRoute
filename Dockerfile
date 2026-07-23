# Use a lightweight Python base image
FROM python:3.12-slim

# Prevent Python from writing .pyc files and force output logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies required by OSMnx, geospatial libraries, and pycairo
RUN apt-get update && apt-get install -y \
    build-essential \
    libspatialindex-dev \
    gdal-bin \
    libgdal-dev \
    pkg-config \
    libcairo2-dev \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install Python packages
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy the entire project repository
COPY . /app/

# Expose the designated network port
EXPOSE 8000

# Execute the chained start command
CMD ["sh", "-c", "python manage.py migrate && python manage.py collectstatic --noinput && gunicorn Core.wsgi --bind 0.0.0.0:8000 --timeout 120"]