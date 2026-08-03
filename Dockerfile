FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    DJANGO_SETTINGS_MODULE=app.settings \
    SGR_DOCKER_DEPLOY=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

RUN chmod +x /app/entrypoint.sh && \
    useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8112

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["streamlit", "run", "app.py", \
     "--server.port=8112", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--browser.gatherUsageStats=false", \
     "--server.enableWebsocketCompression=false"]
