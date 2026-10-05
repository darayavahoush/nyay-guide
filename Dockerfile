FROM node:20-slim AS web
WORKDIR /web
COPY frontend/package*.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates && rm -rf /var/lib/apt/lists/*
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY scripts/ scripts/
# The small encoder is fetched at build time. If the download fails the app still builds and falls back to the hashing encoder.
RUN sh scripts/fetch_model.sh backend/models/multilingual-e5-small
COPY backend/ backend/
RUN cd backend && python -m app.india.slm --build || echo "encoder not built; the app will fall back at runtime"
COPY --from=web /web/dist frontend/dist
ENV PYTHONUNBUFFERED=1 SLM=auto OMP_NUM_THREADS=1
CMD ["sh", "-c", "cd backend && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
