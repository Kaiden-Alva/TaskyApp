FROM python:3.13

RUN apt-get update && apt-get install --no-install-recommends -y \
    build-essential \
    libpq-dev \
    postgresql-client && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

ADD https://astral.sh/uv/install.sh /install.sh
RUN chmod -R 755 /install.sh && /install.sh && rm /install.sh

# Set up the UV environment path
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /app

# Copy pyproject.toml first for dependency installation
COPY pyproject.toml .
COPY uv.lock* ./
COPY init_db.py .

# Install dependencies (force sync to ensure all deps are installed)
RUN uv sync --no-cache

# Copy backend application code
COPY backend/ ./backend/

# Set PATH to use virtual environment Python
ENV PATH="/app/.venv/bin:${PATH}"

# Set PYTHONPATH so Python can find the backend module
ENV PYTHONPATH="/app:${PYTHONPATH}"

# Copy entrypoint script
COPY backend/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Expose port for API
EXPOSE $PORT

# Use entrypoint script to initialize DB and start server
ENTRYPOINT ["/app/entrypoint.sh"]