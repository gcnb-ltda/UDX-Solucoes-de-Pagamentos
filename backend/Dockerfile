FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml alembic.ini ./
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir .

COPY alembic ./alembic
COPY app ./app
COPY tests ./tests

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"]
