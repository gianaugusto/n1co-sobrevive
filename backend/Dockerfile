FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir .

COPY alembic.ini ./
COPY migrations ./migrations

RUN useradd --create-home appuser
USER appuser
EXPOSE 8000

# Apply migrations, then serve. See docs/development.md.
CMD ["sh", "-c", "alembic upgrade head && uvicorn forgetme.main:build_app --factory --host 0.0.0.0 --port 8000"]
