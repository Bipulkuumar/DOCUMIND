# DocuMind — Production Deployment Guide

This guide provides step-by-step instructions for deploying the **DocuMind Document Intelligence & RAG API Platform** into a production cloud environment.

---

## 1. Architecture Overview

```text
                               INTERNET
                                  │
                                  ▼
                        ┌──────────────────┐
                        │ Static Frontend  │ (Vite/React on Vercel / Netlify / Nginx)
                        └────────┬─────────┘
                                 │ HTTPS
                                 ▼
                        ┌──────────────────┐
                        │ FastAPI Backend  │ (Render / Railway / AWS ECS / Container)
                        │                  │
                        │ Auth & Router    │
                        │ Document Engine  │
                        │ Vector Search    │
                        │ Grounded RAG     │
                        └──────┬─────┬─────┘
                               │     │
                    ┌──────────┘     └──────────┐
                    ▼                           ▼
           ┌─────────────────┐         ┌──────────────────┐
           │ PostgreSQL 16   │         │ LLM / Embeddings │
           │ + pgvector      │         │ Provider         │
           │ (Neon/Supabase) │         │ (OpenAI / Local) │
           └─────────────────┘         └──────────────────┘
```

---

## 2. Required Infrastructure & Cloud Services

| Layer | Recommended Hosting Provider | Alternative Providers |
| :--- | :--- | :--- |
| **Database** | Supabase PostgreSQL 16 or Neon Postgres | AWS RDS for PostgreSQL 16 |
| **Backend API** | Render Web Service / Railway | Fly.io / AWS ECS Fargate |
| **Frontend UI** | Vercel / Netlify | Cloudflare Pages / AWS S3 + CloudFront |
| **Container Engine**| Docker Compose (Single Host) | Podman / Kubernetes |

---

## 3. Environment Variables & Secret Management

Create production environment variables in your cloud provider's dashboard or secrets manager. **Never commit `.env` files to git.**

### Backend Environment Variables (`.env`)

```env
# Application Settings
APP_NAME=DocuMind
ENVIRONMENT=production
DEBUG=False
API_V1_STR=/api/v1
SECRET_KEY=<32-char-random-secret>
CORS_ORIGINS=["https://documind.vercel.app","https://yourdomain.com"]

# Database (PostgreSQL + pgvector)
DATABASE_URL=postgresql+asyncpg://user:password@db.provider.com:5432/documind_db

# Security & JWT
JWT_SECRET_KEY=<production-jwt-secret-key>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# File Storage
STORAGE_DIR=/var/data/documind/documents
MAX_UPLOAD_SIZE_MB=25

# AI Provider Configuration
LLM_PROVIDER=openai
LLM_API_KEY=sk-proj-your-openai-api-key
LLM_MODEL=gpt-3.5-turbo
LLM_BASE_URL=https://api.openai.com/v1

EMBEDDING_PROVIDER=local
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
EMBEDDING_DIMENSION=384
```

### Frontend Environment Variables (`frontend/.env`)

```env
VITE_API_URL=https://api.documind.yourdomain.com/api/v1
```

---

## 4. Database Setup & pgvector Initialization

1. Provision a PostgreSQL 16 database instance.
2. Enable the `vector` extension in PostgreSQL:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
3. Run schema migrations using Alembic:
   ```bash
   cd backend
   alembic upgrade head
   ```

Alembic will automatically construct tables (`users`, `documents`, `document_chunks`, `conversations`, `messages`, `retrieval_logs`, `api_usage`) and build the HNSW cosine vector index on `document_chunks(embedding)`.

---

## 5. Backend Deployment (Docker Container)

### Step 1: Build & Test Container Locally
```bash
docker build -t documind-backend:latest ./backend
docker run -p 8000:8000 --env-file backend/.env documind-backend:latest
```

### Step 2: Deploy to Container Hosting (e.g., Render / Railway)
- Connect repository branch `main`.
- Set Build Command: `pip install -r backend/requirements.txt` (or use Dockerfile).
- Set Start Command: `uvicorn app.main:app --host 0.0.0.0 --port 8000`.
- Add release step: `alembic upgrade head`.

---

## 6. Frontend Deployment (Static Hosting)

### Step 1: Build Static Assets
```bash
cd frontend
npm ci
npm run build
```

### Step 2: Deploy `dist/` Directory
- Upload `dist/` folder to Vercel, Netlify, or static server.
- Ensure SPA single-page routing rewrite rule is configured (`/*` redirects to `/index.html`).

---

## 7. Health Checks & Monitoring

Verify deployment endpoints:
- **Live Backend API**: `https://documind-45rg.onrender.com`
- **Root Health**: `GET https://documind-45rg.onrender.com/health`
- **API v1 Health**: `GET https://documind-45rg.onrender.com/api/v1/health`
- **Swagger Docs**: `GET https://documind-45rg.onrender.com/docs`
- **Metrics**: `GET https://documind-45rg.onrender.com/api/v1/metrics`

Run automated smoke test:
```bash
python scripts/production_smoke_test.py --url https://documind-45rg.onrender.com
```

---

## 8. Troubleshooting & Rollback

| Problem | Cause | Solution |
| :--- | :--- | :--- |
| **500 Internal Error on DB query** | pgvector extension missing | Execute `CREATE EXTENSION IF NOT EXISTS vector;` in DB console |
| **401 Unauthorized loops** | Expired JWT or SECRET_KEY mismatch | Clear browser localStorage and verify `JWT_SECRET_KEY` |
| **CORS Rejected** | `CORS_ORIGINS` missing frontend domain | Add exact domain (e.g. `https://your-app.vercel.app`) to `CORS_ORIGINS` |
| **Alembic migration failed** | Schema out of sync | Rollback with `alembic downgrade -1` or check `alembic_version` table |

---

## 9. Rollback Strategy

To roll back a bad release:
1. Revert Git `main` branch to previous commit tag.
2. Re-trigger cloud deployment build.
3. If database schema was changed:
   ```bash
   alembic downgrade <previous_revision_id>
   ```
