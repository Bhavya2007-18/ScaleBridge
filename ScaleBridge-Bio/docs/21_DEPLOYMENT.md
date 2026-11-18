# 21 — Deployment

**Purpose:** Specify local development, containerization, environment configuration, CI/CD, and cloud/on-premise deployment paths `[BP p.10]`.
**Related:** [06_TECH_STACK.md](06_TECH_STACK.md) · [17_SECURITY_AND_PRIVACY.md](17_SECURITY_AND_PRIVACY.md)

---

## 1. Environments & topology (CONFIRMED Docker + GitHub Actions, cloud/on-prem `[BP p.10]`; specifics PROPOSED)
- **Local Dev:** Python venv + Node/pnpm directly on host OR `docker compose up` (`postgres:16`, `minio` or local filesystem object store fallback, `backend`, `frontend`).
- **Local SQLite / Filesystem Dev Fallback (PROPOSED):** To ensure zero-friction local verification when Docker is not running, the backend supports `STORAGE_BACKEND=local` (stores objects under `./var/storage` with identical `orgs/{org_id}/...` layout and SHA-256 verification) and standard SQLAlchemy database URLs (`postgresql+psycopg://...` in production/Docker, or `sqlite:///./var/scalebridge.db` for standalone local testing).
- **CI:** GitHub Actions running `ruff`, `mypy`, `pytest` (scientific engine + API), and `pnpm build` / `tsc`.

## 2. Environment variables (`backend/.env.example`, `frontend/.env.example`)

| Variable | Description | Example (dev only) |
|---|---|---|
| `DATABASE_URL` | SQLAlchemy connection URL | `postgresql+psycopg://scalebridge:scalebridge@localhost:5432/scalebridge` |
| `STORAGE_BACKEND` | `s3` or `local` | `local` |
| `S3_ENDPOINT_URL` | S3 / MinIO endpoint | `http://localhost:9000` |
| `S3_BUCKET` | Bucket name | `scalebridge-files` |
| `JWT_SECRET_KEY` | Signing key (≥32 bytes random in prod) | `change-me-in-production-min-32-chars` |
| `CORS_ORIGINS` | Allowed frontend origins | `http://localhost:3000` |
| `NEXT_PUBLIC_API_BASE_URL` | Backend base URL for Next.js | `http://localhost:8000/api/v1` |
