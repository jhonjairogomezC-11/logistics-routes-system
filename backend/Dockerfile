FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependencias del sistema requeridas para psycopg2 y otros
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar
COPY requirements/ /app/requirements/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements/production.txt

# Copiar el proyecto
COPY . /app/

EXPOSE 8000

# El comando se sobreescribe en docker-compose, pero dejamos un default
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
