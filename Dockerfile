
FROM python:3.14-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create a non-root application user
RUN groupadd --system appuser \
    && useradd --system --gid appuser --create-home appuser

# Install dependencies
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install \
        --no-cache-dir \
        --index-url https://pypi.org/simple \
        --retries 10 \
        --timeout 120 \
        -r requirements.txt
# Copy application files
COPY --chown=appuser:appuser app ./app
COPY --chown=appuser:appuser alembic ./alembic
COPY --chown=appuser:appuser alembic.ini .
COPY --chown=appuser:appuser scripts ./scripts

# Run as non-root
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

