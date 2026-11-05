FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \\
    PYTHONUNBUFFERED=1 \\
    PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY requirements.txt ./requirements.txt
RUN python -m pip install --upgrade pip && pip install -r requirements.txt
COPY . .

# Railway y Render proporcionan PORT. El fallback permite ejecutar localmente.
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
