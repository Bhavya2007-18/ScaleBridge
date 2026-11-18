# Coding Rules

## 1. General rules
- Keep functions small, deterministic, and single-purpose.
- Never silently swallow exceptions or substitute default numeric values for missing scientific inputs.
- Preserve both `original_value` + `original_unit` and normalized SI `value` + `unit`.

## 2. Python (`backend/` & `scalebridge_science/`)
- Python 3.12+, strict type annotations everywhere, Pydantic v2 models for all contracts.
- `scalebridge_science` must remain **100% pure**: no FastAPI, SQLAlchemy, file I/O, network, environment variables, `datetime.now()`, or `random`.
- All unit conversions must go through `scalebridge_science.units` (Pint `UnitRegistry`). Never convert `rpm` via radians (`60 rpm = 1.0 1/s`).
- Database repositories must enforce `organization_id` filtering on every tenant query.

## 3. TypeScript & Next.js (`frontend/`)
- TypeScript `strict: true`. No `any`.
- Format all numbers with explicit units, provenance badges, and value-nature badges.
- Render `insufficient_evidence` and `cannot_evaluate` states explicitly with their missing-input explanations.
