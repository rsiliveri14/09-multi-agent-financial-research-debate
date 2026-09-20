# Load test

Two runners hit the same mix (roughly 3:1 `/health`:`/v1/debate`) against `http://127.0.0.1:8009` with the heuristic provider.

```bash
make load-test          # httpx workers (default)
make load-test-locust   # Locust; CPU monitor skipped so sandbox psutil cannot abort the run
```

Do not import `tests/load/locustfile.py` under pytest: Locust's gevent monkey-patch recurses with httpx/SSL.

## httpx (`make load-test`, 20 workers, 20s, 2026-09-19)

| Name | Requests | Failures | Median ms | Average ms | p95 ms | Max ms | RPS |
|---|---|---|---|---|---|---|---|
| GET `/health` | 3161 | 0 | 49 | 76 | 181 | 2716 | 158 |
| POST `/v1/debate` | 1069 | 0 | 115 | 148 | 341 | 2627 | 53 |
| Aggregated | 4230 | 0 | 59 | 95 | 249 | 2716 | 212 |

CSV: `evaluation/reports/load_stats.csv`.

## Locust (`make load-test-locust`, 20 users, 5/s ramp, 20s, 2026-09-19)

| Name | Requests | Failures | Median ms | Average ms | p95 ms | Max ms | RPS |
|---|---|---|---|---|---|---|---|
| GET `/health` | 748 | 0 | 3 | 32 | 220 | 624 | 39 |
| POST `/v1/debate` | 279 | 0 | 22 | 106 | 630 | 1018 | 14 |
| Aggregated | 1027 | 0 | 9 | 52 | 320 | 1018 | 53 |

Zero HTTP failures on both runners. Max latency is queueing on a single local uvicorn process, not application errors. Re-run after switching `LLM_PROVIDER=openai`; those latencies will not match this table.
