# Production image. Build from the repo root:  docker build -f infra/Dockerfile .
# .dockerignore keeps every book-derived file (regtech_cyber.db, *.json, schema.sql,
# build_db.py, the notebook) and docs/ out of the build context.
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
RUN pip install --no-cache-dir uv==0.11.*
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY manage.py ./
COPY tracker ./tracker
COPY apps ./apps
COPY templates ./templates
COPY static ./static
COPY data ./data
COPY db ./db
RUN DJANGO_SECRET_KEY=build-only DATABASE_URL=postgres://x@localhost/x \
    uv run --no-sync python manage.py collectstatic --noinput --settings=tracker.settings.prod
RUN useradd --uid 10001 --no-create-home app && chown -R app /app/staticfiles
USER app
ENV DJANGO_SETTINGS_MODULE=tracker.settings.prod
EXPOSE 8000
CMD ["uv", "run", "--no-sync", "gunicorn", "tracker.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--access-logfile", "-"]
