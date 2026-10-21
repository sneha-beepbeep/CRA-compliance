# Production image. Build from the repo root:  docker build -f infra/Dockerfile .
#
# The build context is an ALLOWLIST (see /.dockerignore): only app code, templates,
# static assets, catalog YAML, SQL and the lock files are sent. Book-derived files
# (IP not cleared), docs/, tests/, dev tooling and local environments (.venv, .uv,
# .playwright, .localpg) never reach the builder.
#
# Base images are pinned by digest; bump tag and digest together (Renovate/Dependabot).
ARG PYTHON_IMAGE=python:3.12-slim-bookworm@sha256:6a0e06f5ba0b373d051aabd3fffb9b873f27f9a2a3a14bcbe37dee6f0e3bbc70
ARG UV_IMAGE=ghcr.io/astral-sh/uv:0.13.4@sha256:9f130421e930bfbdc563c00740466603f8723158e90297d07957c2294640262b

FROM ${UV_IMAGE} AS uv

# ---- build: resolve runtime dependencies and collect static files -------------
FROM ${PYTHON_IMAGE} AS build
COPY --from=uv /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/app/.venv
WORKDIR /app
COPY pyproject.toml uv.lock ./
# Runtime dependencies only: the dev, localpg and browser groups are never installed.
RUN uv sync --frozen --no-default-groups --no-install-project
COPY manage.py ./
COPY tracker ./tracker
COPY apps ./apps
COPY templates ./templates
COPY static ./static
COPY data ./data
COPY db ./db
RUN DJANGO_SECRET_KEY=build-only DATABASE_URL=postgres://build@localhost/build \
    /app/.venv/bin/python manage.py collectstatic --noinput --settings=tracker.settings.prod

# ---- runtime: no uv, no build tooling; code owned by root, run as uid 10001 ----
FROM ${PYTHON_IMAGE} AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/app/.venv/bin:$PATH \
    DJANGO_SETTINGS_MODULE=tracker.settings.prod
RUN groupadd --gid 10001 app \
 && useradd --uid 10001 --gid app --no-create-home --home-dir /nonexistent --shell /usr/sbin/nologin app
WORKDIR /app
# Files stay root-owned and read-only to the app user (it never writes under /app).
COPY --from=build /app /app
USER 10001:10001
EXPOSE 8000
CMD ["gunicorn", "tracker.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", \
     "--worker-tmp-dir", "/dev/shm", "--access-logfile", "-"]
