# API

Stable envelope:

```json
{
  "request_id": "req_123",
  "status": "completed",
  "data": {},
  "errors": []
}
```

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/health` | public | liveness |
| GET | `/ready` | public | corpus indexed |
| GET | `/metrics` | public | Prometheus |
| POST | `/v1/debate` | analyst | run debate |
| GET | `/v1/debate/{id}` | analyst | result |
| GET | `/v1/debate/{id}/trace` | analyst | node events |
| GET | `/v1/debate/{id}/graph` | analyst | provenance graph |
| GET | `/v1/debates` | analyst | recent runs |
| GET | `/v1/corpus` | analyst | index summary |
| POST | `/v1/eval/run?suite=regression` | admin | evaluation |
| GET | `/v1/eval/latest` | analyst | last report |
| POST | `/v1/admin/simulate-failure` | admin | inject faults |
| GET | `/v1/admin/nodes` | analyst | node catalog |

## Example

```bash
curl -s http://127.0.0.1:8009/v1/debate \
  -H 'Authorization: Bearer dev-analyst-token' \
  -H 'Content-Type: application/json' \
  -d '{"question":"What were Apple total net sales in FY2024, and did Greater China grow?"}'
```

Interactive OpenAPI: `http://127.0.0.1:8009/docs`.
