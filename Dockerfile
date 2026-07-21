FROM python:3.13.14-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:0.11.29 /uv /uvx /bin/

# Venv outside /app so a dev bind mount of the repo does not shadow it.
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py

WORKDIR /app

# Dependency layer: cached unless the lockfile changes. The project is
# "virtual" in uv.lock, so this installs dependencies only.
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --compile-bytecode

COPY . .

# Run as an unprivileged user. Its UID should match the owner of the
# bind-mounted instance/ and uploads/ directories; override with `user:`
# in compose if that owner's uid differs.
RUN useradd --create-home --uid 1001 app
USER app

EXPOSE 8000
CMD ["gunicorn", "-w", "3", "-b", "0.0.0.0:8000", "app:app"]
