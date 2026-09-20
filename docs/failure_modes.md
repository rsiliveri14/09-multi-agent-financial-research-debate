# Failure modes

| Failure | Detection | Recovery | User-visible result |
|---|---|---|---|
| Invalid input | Pydantic / FastAPI | Reject | 422 `VALIDATION_ERROR` |
| Authentication | Missing/invalid bearer | Reject | 401 `AUTHENTICATION_FAILURE` |
| Authorization | RBAC on tools and admin | Block | 403 `AUTHORIZATION_FAILURE` |
| Model timeout | timeout wrapper / flag | Typed failure | 504 or `provider_timeout` |
| Tool timeout | timeout wrapper / flag | Retry then fail | 502 `TOOL_FAILURE` or partial |
| Empty retrieval | retrieval validator | Abstain | `insufficient_evidence` |
| Invalid structured output | schema validator | Bounded repair, then typed failure | `validation_failed` |
| Database outage | DB exception / flag | 503 | `DATABASE_FAILURE` |
| Agent loop | iteration / wall-clock / token budget | Terminate | `loop_detected` / `budget_exceeded` |
| Permission violation | tool allow-list | Block | 403 |
| 8-K vs 10-Q conflict | disagreement matrix | Prefer periodic filing; else unresolved | `unresolved` with both citations |
| Prompt injection in filings | untrusted wrapper | Never execute retrieved text | Claims still require citation overlap |
| Rate limit | provider 429 | Retry-after mapping | 429 `RATE_LIMIT` |
| Provider outage | HTTP 5xx | Fail closed | 503 `PROVIDER_OUTAGE` |
