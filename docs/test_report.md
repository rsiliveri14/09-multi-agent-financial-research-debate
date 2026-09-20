# Test report

Command: `.venv/bin/pytest -q --ignore=tests/integration`

Result: **149 passed** (`make test`). Integration: **2 passed** (`INTEGRATION=1`, Compose Postgres on 5439 + Redis on 6389). Typecheck: `mypy src` — **no issues**. Frontend: `tsc --noEmit` and `vite build` succeeded. `pip-audit`: no known vulnerabilities.

Live coverage (real corpus, orchestrator, ASGI; HTTP when uvicorn is up):

| Layer | What it hits |
|---|---|
| Live orchestrator | All 10 benchmark questions |
| Extra lookups | AAPL / MSFT / AMZN / NVDA / TSLA |
| FastAPI ASGI | Debate + get + trace + graph |
| Eval harness | Regression (6) and full (10) |
| Regression | Every gold item |
| Load | httpx + Locust against `/health` and `/v1/debate` — see `docs/load_test.md` |

HTTP tests skip if nothing is listening on `LIVE_API_URL` unless `LIVE_HTTP=1`.

Integration tests (`INTEGRATION=1`) need Compose Postgres on port 5439 and Redis on 6389. Both were run on this checkout after `docker compose up -d db redis`.

Ruff: `ruff check src tests evaluation scripts`.

Evaluation: `python -m evaluation.runners.harness --suite regression` — `evaluation/reports/regression.json`. Do not quote quality numbers that were not produced by that command on this checkout.
