# Development Instructions

## 1. Workflow per phase
1. Read the relevant specification in `docs/`.
2. Check existing modules and contracts before adding files.
3. Implement pure logic in `scalebridge_science` first with unit tests (`pytest`).
4. Implement persistence and FastAPI endpoints in `backend/app` with integration tests.
5. Implement typed UI screens and reusable scientific components in `frontend/`.
6. Verify zero test failures, type errors, or regressions before marking a phase complete.

## 2. Prohibited actions
- Do not invent equations or silently fill in missing scientific inputs.
- Do not change documented API contracts without updating both backend schemas and frontend types.
- Do not present synthetic or demonstration datasets as real experimental data (`is_synthetic` must be `true`).
