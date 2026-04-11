FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Install dependencies (cached layer)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy application code and migrations
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY translations/ ./translations/
COPY alembic.ini ./
COPY entrypoint.sh ./
RUN chmod +x entrypoint.sh

# Place executables on PATH
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["./entrypoint.sh"]
