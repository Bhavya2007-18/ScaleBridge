# Architecture Rules

## 1. Workspace structure
```
ScaleBridge-Bio/
├── docs/                  # Technical & scientific specification (01..22)
├── ai-context/            # Agent guardrails & architecture rules
├── sample-data/           # Clearly labeled synthetic/reference CSV datasets
├── backend/
│   ├── scalebridge_science/  # Pure scientific & readiness engine (zero I/O)
│   ├── app/                  # FastAPI modular monolith (api, core, db, modules)
│   └── tests/                # Pytest suite (unit, dimensional, API integration)
├── frontend/              # Next.js (React, TypeScript, Tailwind, Plotly)
└── docker-compose.yml     # Reproducible container stack
```

## 2. Dependency rules
- `frontend` communicates with `backend` exclusively via `/api/v1/*` JSON/multipart REST endpoints.
- `backend/app/modules/*` orchestrate persistence and call `scalebridge_science` for unit conversion, calculations, compatibility checks, risk rules, and validation task generation.
- `reports` renders persisted `Assessment` records only—it never recomputes engineering numbers.
- Immutable entities (`passport_versions`, `vessel_versions`, `measurements`, `assessments`, `reports`, `audit_events`) are insert-only.
