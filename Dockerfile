# ── Stage 1: dependency builder ────────────────────────────────────────────
FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ── Stage 2: minimal runtime image ─────────────────────────────────────────
FROM python:3.12-slim
WORKDIR /app

# Security: non-root user
RUN useradd --create-home --shell /bin/bash appuser

COPY --from=builder /root/.local /home/appuser/.local
COPY . .
RUN chown -R appuser:appuser /app

USER appuser
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

# Single worker — Cloud Run scales via instances, not threads
CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
