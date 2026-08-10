FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

RUN chmod +x /app/docker/entrypoint.sh \
    && mkdir -p /app/media /app/staticfiles

EXPOSE 8000 8001

ENTRYPOINT ["/app/docker/entrypoint.sh"]
CMD ["gunicorn", "Enterprise_Legal_AI_Case_Management_Platform.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "120"]
