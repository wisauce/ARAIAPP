FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN useradd --create-home --uid 10001 araiap

COPY pyproject.toml README.md alembic.ini ./
COPY app ./app
COPY alembic ./alembic

RUN pip install . && mkdir -p /app/data && chown araiap:araiap /app/data

USER araiap
EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
