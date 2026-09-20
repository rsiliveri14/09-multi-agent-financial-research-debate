# Deployment

First release is local Compose (verified: Postgres, Redis, API image, web image,
alembic, a live debate). The Kubernetes manifests are a production-*style*
design, not a claim that this has been served on a cluster.

## Service boundaries

- `debate-api` — FastAPI workers, corpus in process (or pgvector later)
- `debate-web` — nginx + static React
- Grafana dashboard JSON: `deployment/observability/grafana-debate.json` (import into Grafana; not a hosted Grafana)
- Secrets via K8s Secret / external manager, never images
- HPA on API CPU when traffic exists
- Readiness `/ready`, liveness `/health`
- Rollback: previous ReplicaSet; `alembic downgrade`

Object storage is not required for the sample corpus. If real filings are added,
store raw HTML in a bucket and keep chunks in Postgres.
