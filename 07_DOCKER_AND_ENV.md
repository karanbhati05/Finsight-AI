# FinSight V2 — Docker & Environment Setup

---

## .env.example

```bash
# ── AI APIs ──────────────────────────────────────────────
GOOGLE_API_KEY=your_gemini_api_key
NEWS_API_KEY=your_newsapi_key
FINNHUB_API_KEY=your_finnhub_key

# ── Infrastructure ────────────────────────────────────────
REDIS_URL=redis://localhost:6379
DATABASE_URL=sqlite:///./finsight.db

# ── App ───────────────────────────────────────────────────
FRONTEND_URL=http://localhost:5173
BACKEND_URL=http://localhost:8000
ENVIRONMENT=development

# ── Pipeline defaults ─────────────────────────────────────
DEFAULT_TICKER=AAPL
DEFAULT_DAYS_BACK=60
```

---

## docker-compose.yml

```yaml
version: '3.9'

services:

  # ── Redis cache ─────────────────────────────────────────
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3

  # ── FastAPI backend ─────────────────────────────────────
  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - .:/app                          # mount full project
      - ./data:/app/data                # persist pipeline data
      - ./models:/app/models            # persist trained models
    env_file:
      - .env
    environment:
      - REDIS_URL=redis://redis:6379
    depends_on:
      redis:
        condition: service_healthy
    command: uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload

  # ── React frontend ──────────────────────────────────────
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "5173:5173"
    volumes:
      - ./frontend/src:/app/src         # hot reload
    environment:
      - VITE_API_URL=http://localhost:8000
    depends_on:
      - backend
    command: npm run dev -- --host

volumes:
  redis_data:
```

---

## backend/Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
COPY backend/requirements_backend.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements_backend.txt

# Download spaCy model
RUN python -m spacy download en_core_web_sm

# Copy source code
COPY . .

EXPOSE 8000
CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## frontend/Dockerfile

```dockerfile
FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
```

---

## Run everything with Docker

```bash
# Start all services
docker-compose up

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop everything
docker-compose down

# Rebuild after code changes
docker-compose up --build
```

---

## Run without Docker (development)

```bash
# Terminal 1 — Redis
docker run -d -p 6379:6379 redis:7-alpine

# Terminal 2 — Backend
cd finsight-v2
source venv/bin/activate
uvicorn backend.api.main:app --reload --port 8000

# Terminal 3 — Frontend
cd finsight-v2/frontend
npm run dev
```

