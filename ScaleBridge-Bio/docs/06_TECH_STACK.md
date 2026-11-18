# 06 — Technology Stack

**Purpose:** Fix the technology choices so all contributors and agents use the same tools.
**Related:** [05_SYSTEM_ARCHITECTURE.md](05_SYSTEM_ARCHITECTURE.md) · [21_DEPLOYMENT.md](21_DEPLOYMENT.md) · [../ai-context/CODING_RULES.md](../ai-context/CODING_RULES.md)

---

## 1. Blueprint stack (CONFIRMED `[BP p.10]`)

| Layer | Tools | Role in MVP |
|---|---|---|
| Frontend | Next.js, React, TypeScript, Tailwind CSS, shadcn/ui | Projects, uploads, vessel editor, dashboards, scenario review, report screens |
| Visualization | Plotly | Time-series charts, overlays, engineering plots |
| Backend | Python, FastAPI, Pydantic | API, validation, orchestration, scientific-service integration |
| Data processing | Pandas, NumPy, SciPy, Pint | Parsing, numerical analysis, unit conversions, engineering calculations |
| Scientific modelling | Deterministic equations first; SciPy; optional CasADi / GEKKO later | Physics-based comparisons; optimization where justified |
| ML (later) | Scikit-learn, XGBoost, MLflow | Only after sufficient real, governed data — **not MVP** |
| Database | PostgreSQL; TimescaleDB optional | Users, orgs, projects, batches, measurements, scenarios, reports |
| Files / jobs | S3-compatible object storage; Celery + Redis optional | Raw files, generated reports, background processing |
| Deployment | Docker, GitHub Actions; cloud or on-premise path | Reproducible deployment, testing, release |

## 2. Supporting choices (PROPOSED — change requires owning-lead approval)

### 2.1 Backend
| Concern | Choice | Reason |
|---|---|---|
| Python version | 3.12 | Current stable, typing features |
| ORM / migrations | SQLAlchemy 2.x (typed ORM) + Alembic | Standard with FastAPI; explicit migrations |
| DB driver | psycopg 3 | Maintained, async-capable |
| XLSX parsing | openpyxl (via pandas) | Pandas default engine for .xlsx |
| CSV parsing | pandas `read_csv` with explicit dtype/encoding detection (`charset-normalizer`) | Robust to exports |
| Password hashing | argon2 (`argon2-cffi`) | Modern KDF |
| Tokens | Short-lived JWT access token (15 min) + rotating refresh token in httpOnly cookie | Stateless API, revocable refresh |
| PDF | Jinja2 HTML templates → WeasyPrint | Pure-Python, deterministic layout, HTML/CSS skills reuse |
| Charts in PDF | Plotly static export via Kaleido | Same chart library as UI |
| Object storage client | boto3 (S3 API) | Works with AWS S3, MinIO, others |
| Settings | pydantic-settings | Env-based config |
| Lint/format/types | ruff (lint+format), mypy (strict for `scalebridge_science`) | Fast, consistent |
| Tests | pytest, pytest-cov, hypothesis (property tests for units), httpx TestClient, testcontainers-postgres | Layered testing ([18](18_TESTING_AND_VALIDATION.md)) |
| Dependency mgmt | uv with `pyproject.toml` + lock file | Reproducible |

### 2.2 Frontend
| Concern | Choice |
|---|---|
| Node | 20 LTS |
| Next.js | App Router, TypeScript strict |
| Data fetching | TanStack Query |
| API types | Generated from FastAPI OpenAPI via `openapi-typescript` (+ `openapi-fetch`) — **never hand-write API types** |
| Forms / validation | react-hook-form + zod |
| Charts | `react-plotly.js` (dynamic import, client-only) |
| Tables | TanStack Table |
| Unit tests | Vitest + React Testing Library |
| E2E | Playwright |
| Lint/format | ESLint (next config) + Prettier |
| Package manager | pnpm |

### 2.3 Infrastructure
| Concern | Choice |
|---|---|
| Local stack | docker compose: `postgres:16`, `minio`, `api`, `web`, `mailpit` (invite emails in dev) |
| CI | GitHub Actions: lint, type-check, tests, build images |
| Registry | GitHub Container Registry |
| Hosting | Cloud provider **OPEN (OQ-007)**; on-prem via the same compose/images |

## 3. Explicitly deferred technologies
| Tech | Status |
|---|---|
| TimescaleDB | Deferred until measured query performance requires it (**OQ-026**) |
| Celery + Redis | Deferred; synchronous processing within NFR-07 limits (**OQ-027**) |
| CasADi / GEKKO | Later, only where optimization is justified `[BP p.10]` |
| scikit-learn / XGBoost / MLflow | Later, only with real governed data `[BP p.10]` |
| LLM / chatbot features | Excluded `[BP p.9]` |
| Kubernetes | Not needed for MVP |

## 4. Version policy (PROPOSED)
- Pin exact versions in lock files; upgrade deliberately in dedicated PRs.
- **Pint version is recorded in every `conversion_record`** and in assessment snapshots because unit definitions affect results.
- `scalebridge_science` has its own semver (`ENGINE_VERSION`) bumped on any change to numeric behaviour.

## 5. Acceptance criteria
- `docker compose up` brings up a working stack with seeded demo org on a clean machine.
- CI fails on lint, type, test or OpenAPI-client drift (generated TS client differs from committed client).
