# Multi-Agent Financial Research Debate

Evidence-driven debate among **Bull**, **Bear**, **Financial**, **Risk**, and **Evidence** specialists, with a critic, disagreement matrix, primary-evidence conflict resolution, and a synthesizer that is allowed to stay unresolved.

This is a portfolio system, not investment advice. The sample corpus is synthetic (frozen from Project 2's SEC-style filings). Default inference is a local **heuristic** provider — no API key required.

## Why it exists

A chatbot that "debates itself" in one prompt is not a debate. Here each specialist has a distinct filter on the same retrieved facts, every material claim carries citations, and leftover 8-K vs 10-Q conflicts remain unresolved instead of being averaged away.

## Quick start

```bash
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
python -m pip install -e ".[dev]"
make run-api
```

In another terminal:

```bash
cd frontend && npm install && npm run dev
```

- API: http://127.0.0.1:8009/docs
- UI: http://127.0.0.1:5179
- Auth header: `Authorization: Bearer dev-analyst-token` (admin: `dev-admin-token`)

Docker (API + UI + Postgres + Redis):

```bash
cp .env.example .env
docker compose up --build
```

Then open http://localhost:8090

## What the system does

1. Plan the question (tickers, topics, type).
2. Hybrid-retrieve filing chunks per specialist query (BM25 + hashed dense + rerank).
3. Run five specialists with typed claims: evidence, confidence, assumptions, counterarguments.
4. Normalize onto `TICKER.metric.period` keys.
5. Build a disagreement matrix.
6. Critic attacks stale 8-Ks, missing citations, and cherry-picking.
7. Validator checks numeric/lexical support.
8. Resolver prefers 10-K/10-Q over 8-K; otherwise **unresolved**.
9. Synthesizer writes the report and provenance graph.
10. Single-agent RAG runs as a baseline on the same question.

## Stack

Python 3.12, FastAPI, Pydantic v2, LangGraph (sequential fallback), PostgreSQL/pgvector, Redis, React + Vite + Tailwind, OpenTelemetry + Prometheus, pytest, Docker, GitHub Actions.

LLM, embeddings, vector store, tools, evaluators, and telemetry sit behind interfaces. Domain logic is ordinary Python.

## Tests and evaluation

```bash
make test          # unit + live in-process debates (real corpus, no mocks)
make test-live     # same live paths plus HTTP against uvicorn if LIVE_HTTP=1
make eval          # frozen 6-item suite → evaluation/reports/regression.json
make eval-full     # 10-item suite
```

Do not quote quality numbers that were not produced by `make eval` on this checkout.

Measured on this checkout (`make eval`, heuristic provider, 6 regression items, 2026-09-19):

| Metric | Multi-agent | Single-agent RAG |
|---|---|---|
| Evidence-supported accuracy | 0.75 | 0.75 |
| Final correctness | 0.77 | 0.75 |
| Contradiction detection | 0.67 | 0.33 |
| Specialist diversity | 0.58 | 0.00 |
| Latency p50 | 7 ms | ~0 ms (in-process extract) |
| Estimated cost (heuristic) | $0.0005 | $0.00 |

Contradiction detection improved; numeric accuracy did not. Extra retrievals are the price. Re-run `make eval` after model or corpus changes — do not copy these figures forward blindly.

## Trade-offs

1. **Quality vs latency** — five retrievals plus critic/validator beat a single RAG pass on contradiction detection; they cost more wall-clock.
2. **Agents vs cost** — extra specialists increase tokens when `LLM_PROVIDER=openai`; locally cost is an estimate only.
3. **Hashing embeddings vs hosted encoders** — local and deterministic; weaker recall.
4. **Memory store vs Postgres** — demo boots without Docker; Compose/K8s persist runs.

## Limitations

- Synthetic filings, not live EDGAR.
- Heuristic specialists are inspectable, not a frontier LLM.
- Screenshots of the debate floor, matrix, graph, unresolved 8-K/10-Q, and eval chart are in `docs/screenshots/`.
- Kubernetes manifests are a design, not a running production cluster.
- `docker compose up --build` is the durable path (`STORE_BACKEND=postgres`). It was verified on this machine (API image, web image, Postgres, Redis, alembic, a live debate). If port 8009 is already taken by `make run-api`, use `API_HOST_PORT=8010 docker compose up --build`.
- Live `LLM_PROVIDER=openai` is implemented behind `LLMProvider` and is unmeasured until you set `OPENAI_API_KEY` and re-run `make eval`.

## Docs

- [Architecture](docs/architecture.md)
- [Sequence](docs/sequence.md)
- [API](docs/api.md)
- [Failure modes](docs/failure_modes.md)
- [Security](docs/security.md)
- [Operations](docs/operations.md)
- [Evaluation](docs/evaluation.md)
- [Demo](docs/demo.md)
- [Load test](docs/load_test.md)
- [Case study](docs/case_study.md)
- [Data](data/README.md)

## Next

Temporal debate rounds, a real claim/evidence graph database, adaptive specialist count, and learned termination — see the playbook in the project spec.
