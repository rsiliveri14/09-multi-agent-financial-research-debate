# Portfolio notes

Artifacts:

1. Architecture diagram — `docs/architecture.md`
2. Sequence diagram — `docs/sequence.md`
3. Screenshots — `docs/screenshots/` (empty floor, debate, matrix, graph, unresolved 8-K/10-Q, eval)
4. Demo script — `docs/demo.md`
5. Evaluation — `make eval` → `evaluation/reports/regression.json`
6. Failure table — `docs/failure_modes.md`
7. Case study — `docs/case_study.md`
8. README
9. Trade-offs — README + `docs/evaluation.md`
10. Limitations — README

This repository was exercised locally (API, UI, pytest, eval, load test, Docker
Compose with Postgres + Redis). Kubernetes manifests are a design, not a cluster
that was deployed.

## Definition of Done

- [x] Clean laptop path: `.env.example`, `make run-api`, `npm run dev`
- [x] Docker Compose files + Postgres migrations (`alembic`); Compose verified locally (`STORE_BACKEND=postgres`, Redis healthy)
- [x] Main API + debate workflow
- [x] Bounded agent policy and typed tools
- [x] Errors mapped; tests pass (`make test`)
- [x] Evaluation + single-agent baseline (`make eval`)
- [x] Real metrics (eval JSON + Prometheus + locust/http load CSV)
- [x] Observability, security, failure-mode docs
- [x] README, architecture, sequence, screenshots, demo
- [x] No secrets committed; limitations documented

