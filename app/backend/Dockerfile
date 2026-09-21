FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

# Install runtime deps from the lockfile so dev matches production
# (Dockerfile.prod does the same). Installing from pyproject alone
# re-resolves to the newest releases and drifts away from prod.
COPY pyproject.toml requirements.lock ./
RUN uv pip install --system -r requirements.lock

COPY alembic.ini .
COPY alembic/ ./alembic/
COPY src/ ./src/

CMD ["sh", "-c", "alembic upgrade head && uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload"]
