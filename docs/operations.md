# Operations

## Local (no Docker)

```bash
cp .env.example .env
python -m pip install -e ".[dev]"
make run-api
```

API: `http://127.0.0.1:8009` · OpenAPI: `/docs`

```bash
cd frontend && npm install && npm run dev
```

UI: `http://127.0.0.1:5179`

## Docker Compose

```bash
cp .env.example .env
docker compose up --build
```

- API `http://localhost:8009` (override host port with `API_HOST_PORT` if 8009 is taken)
- UI `http://localhost:8090`
- Postgres `localhost:5439`
- Redis `localhost:6389`

Default compose API uses `STORE_BACKEND=postgres`. The API container runs `alembic upgrade head` on boot. Redis is optional: run status is mirrored when Redis is healthy and ignored when it is not.

## Health

- `GET /health` liveness
- `GET /ready` corpus indexed
- `GET /metrics` Prometheus

## Rollback

Compose: `docker compose down`. Kubernetes: `kubectl rollout undo deploy/debate-api`. Database: `alembic downgrade -1`.

## Seed / demo

```bash
make seed
make demo
make eval
```
