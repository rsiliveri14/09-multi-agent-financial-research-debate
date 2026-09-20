# Security

## Assets

- Synthetic filing corpus and derived embeddings
- Debate trajectories, citations, and evaluation reports
- API tokens and optional OpenAI keys
- PostgreSQL contents when `STORE_BACKEND=postgres`

## Trust boundaries

1. Browser → API (Bearer token)
2. API → LLM provider
3. API → retrieval index (untrusted document text)
4. API → Postgres/Redis
5. Specialists → tools (allow-listed per role)

## Threats and mitigations

| Threat | Mitigation |
|---|---|
| Stolen demo tokens | Env-only secrets; rotate in production; never commit `.env` |
| Prompt injection via filings | Wrap evidence in `<untrusted_evidence>`; tools cannot execute text |
| Tool abuse | `TOOL_PERMISSIONS` per `AgentRole` |
| PII in logs | Redact emails, phones, `sk-` keys, Bearer tokens |
| SSRF via model base URL | Operator-controlled settings, not request-controlled |
| Container escape | Non-root UID 10001 in API image |
| Dependency CVEs | `pip-audit` in CI |

## Residual risk

The default tokens (`dev-analyst-token`) are for local demo only. Hashing embeddings are not a privacy boundary. Heuristic specialists can still cherry-pick; the critic is a mitigator, not a guarantee. No production IdP is wired.
