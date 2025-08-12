# Dockerfile
FROM python:3.12-slim

# Ustawienia runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Opcjonalnie: strefa czasu (żeby logi/cron miały Europe/Warsaw)
ENV TZ=Europe/Warsaw

WORKDIR /app

# Systemowe zależności (kompilacja i Postgres), tzdata dla strefy czasu
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Zależności Pythona
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Kod aplikacji
COPY . .

# (Opcjonalnie) nie-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Wskazanie settings (możesz nadpisać w .env / compose
ENV DJANGO_SETTINGS_MODULE=Dog_hotel.settings

# Port Gunicorna
EXPOSE 8000

# Start: migracje, statyki, Gunicorn
# GUNICORN_WORKERS możesz zmienić w .env/compose (domyślnie 3)
CMD bash -c "\
  python manage.py migrate --noinput && \
  python manage.py collectstatic --noinput && \
  gunicorn Dog_hotel.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers \${GUNICORN_WORKERS:-3} \
    --timeout 60 \
"

