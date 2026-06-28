FROM python:3.12-slim

LABEL maintainer="Dockfix Labs <security@dockfixlabs.dev>"
LABEL org.opencontainers.image.title="AgentGuard App"
LABEL org.opencontainers.image.description="GitHub App for automated PR security reviews"
LABEL org.opencontainers.image.source="https://github.com/dockfixlabs/agentguard-app"
LABEL org.opencontainers.image.license="MIT"

WORKDIR /app

# Install dependencies first for better caching
COPY pyproject.toml setup.py ./
RUN pip install --no-cache-dir -e ".[app]"

# Copy application code
COPY . .

# Install AgentGuard itself
RUN pip install --no-cache-dir dfx-agentguard

# Create non-root user
RUN useradd -m -u 1000 agentguard && chown -R agentguard:agentguard /app
USER agentguard

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
