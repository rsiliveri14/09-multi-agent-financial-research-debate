# Data model

```mermaid
erDiagram
  research_runs ||--o{ run_events : traces
  research_runs {
    uuid id PK
    string request_id UK
    text question
    string status
    string terminal_state
    string model_provider
    string model_name
    int latency_ms
    float estimated_cost_usd
    text error
    jsonb result_json
    timestamptz created_at
    timestamptz completed_at
  }
  run_events {
    int id PK
    uuid run_id FK
    int seq
    string event_type
    string node
    jsonb payload
    timestamptz created_at
  }
  audit_events {
    int id PK
    string request_id
    string actor_role
    string action
    jsonb payload
    timestamptz created_at
  }
  evaluation_results {
    int id PK
    string suite
    jsonb report
    timestamptz created_at
  }
```

| Table | Purpose | PK | FKs | Indexes | Sensitive | Retention |
|---|---|---|---|---|---|---|
| `research_runs` | One debate | `id` UUID | — | `request_id` unique, `status` | question text, result JSON | Operator-defined; demo keeps all |
| `run_events` | Trace | `id` serial | `run_id → research_runs` | `run_id`, `event_type` | payloads may include snippets | Same as parent run |
| `audit_events` | Consequential actions | `id` serial | — | `request_id`, `action` | actor role | Longer than runs |
| `evaluation_results` | Harness output | `id` serial | — | `suite` | none expected | Keep latest per suite |

No secrets belong in these tables. API tokens stay in the environment. The in-memory repository implements the same contract for laptop demos without Postgres.
