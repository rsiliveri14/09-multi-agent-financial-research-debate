FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends build-essential curl && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md /app/
COPY src /app/src
COPY alembic /app/alembic
COPY alembic.ini /app/alembic.ini
COPY scripts /app/scripts
COPY evaluation /app/evaluation
COPY data /app/data
COPY configs /app/configs

RUN pip install --no-cache-dir .

ENV PYTHONPATH=/app/src:/app
ENV PYTHONUNBUFFERED=1

RUN useradd --create-home --uid 10001 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
CMD ["sh", "/app/scripts/entrypoint.sh"]
