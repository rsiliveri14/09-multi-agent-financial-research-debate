# Project 9: Multi-Agent Financial Research Debate

**Evidence-driven multi-agent research system with specialist agents, critic, disagreement analysis, and synthesis.**


## Engineering principles

1. Prefer deterministic software for deterministic work.
2. Use an LLM for language understanding, planning, synthesis, and explanation—not for calculations or facts that can be obtained from authoritative tools.
3. Every agent must have a bounded execution policy: maximum iterations, wall-clock time, token budget, tool timeout, retry policy, and explicit terminal states.
4. Every tool must have a typed input/output contract.
5. Every externally sourced claim must be traceable when the project requires evidence.
6. Never fabricate evaluation results. Run the benchmark and report actual measured results.
7. Use synthetic or openly licensed data unless a source explicitly permits the intended use.
8. Never commit secrets, API keys, credentials, or private customer information.
9. Design for local reproducibility with Docker Compose before adding cloud deployment.
10. Keep the core architecture model-provider agnostic.
11. Write tests before declaring a feature complete.
12. Every failure mode must have a deliberate behavior rather than an uncaught exception.

## Recommended baseline stack

Use Python 3.12, FastAPI, Pydantic v2, PostgreSQL, Redis where asynchronous state/queues are useful, Docker, pytest, Ruff, mypy, and GitHub Actions.

For agent workflows, prefer LangGraph when a stateful graph is useful. Keep business logic in ordinary Python modules so the application is not tightly coupled to the framework.

For retrieval, use PostgreSQL + pgvector for the default local implementation unless the project specifically requires a different vector database. Implement a repository interface so Qdrant/Pinecone/Milvus can be substituted.

For frontend work, use React + TypeScript + Vite + Tailwind CSS. Do not build a generic chat screen when a workflow-specific UI is more informative.

## Definition of portfolio quality

A project is not complete merely because an LLM returns an answer. It is complete when:
- the application can be run from a clean machine using documented commands;
- architecture is visible in the repository;
- APIs have schemas and error responses;
- tests cover important and failure paths;
- AI behavior is evaluated on reproducible data;
- latency/cost/quality measurements are captured where relevant;
- UI exposes distinctive behavior;
- logs and traces make failures diagnosable;
- README explains design decisions and trade-offs;
- limitations and future work are documented;
- screenshots or a short demo can be added to the portfolio.

## Suggested repository structure

```text
project/
├── README.md
├── LICENSE
├── pyproject.toml
├── .env.example
├── docker-compose.yml
├── Dockerfile
├── Makefile
├── src/
│   ├── api/
│   ├── agents/
│   ├── domain/
│   ├── services/
│   ├── tools/
│   ├── models/
│   ├── repositories/
│   ├── evaluation/
│   ├── observability/
│   ├── security/
│   └── config/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── evaluation/
│   └── regression/
├── data/
│   ├── sample/
│   └── benchmarks/
├── scripts/
├── deployment/
│   ├── docker/
│   └── kubernetes/
└── docs/
    ├── architecture.md
    ├── evaluation.md
    ├── operations.md
    └── security.md
```

## Required engineering artifacts

Create an architecture diagram, a sequence diagram for the main workflow, API contract, data model diagram where relevant, benchmark methodology, failure-mode table, security/threat model, local run instructions, deployment instructions, test report, evaluation report, demo script, and concise portfolio case-study summary.


---

## 1. Why this project belongs in a serious AI/ML portfolio

Do not implement fake debate where agents simply agree. Each specialist must have a distinct role, evidence requirements, confidence, assumptions, and counterarguments. Disagreement should be measurable and useful.

This specification is intentionally designed around skills that recur in current AI/ML engineering roles: production Python, RAG, agent orchestration, evaluation, observability, cloud/container deployment, testing, reliability, and cost/latency optimization. These should be demonstrated through working artifacts and measurements rather than a list of technologies.

---

## 2. Exact project objective

Build the complete system described by this document from an empty repository.

Do not stop at a plan. Implement the backend, AI workflow, data layer, evaluation harness, tests, local infrastructure, documentation, and workflow-specific UI where specified.

Do not replace difficult components with static output merely to make the demo appear successful. Mocks are allowed for deterministic unit tests and local fallbacks, but the real interfaces must remain implemented.

---

## 3. Recommended technology stack

Python; FastAPI; LangGraph; PostgreSQL + pgvector; hybrid retrieval; cross-encoder reranking; React/TypeScript; OpenTelemetry; pytest; Docker; optional graph database for claim/evidence relationships.

### Technology-selection rule

If a dependency does not provide meaningful functionality, do not add it merely for resume keywords. Keep domain logic in ordinary Python and isolate framework-specific code behind interfaces.

Create interfaces for model providers, embeddings, vector stores, external tools, evaluators, and telemetry exporters wherever they can reasonably vary.

---

## 4. Data and benchmark strategy

Use public financial documents and create benchmark questions with evidence requirements and structured answer schema. Include mixed, incomplete, contradictory, and time-sensitive evidence.

Create `data/README.md` explaining:
- origin and licensing;
- schema;
- preprocessing;
- train/validation/test boundaries;
- benchmark construction;
- known limitations.

Never place secrets or private data in the repository.

---

## 5. End-to-end workflow

1. Receive question.
2. Create research plan.
3. Run Bull, Bear, Financial, Risk, and Evidence agents.
4. Require claims/evidence/confidence/assumptions/counterarguments.
5. Normalize claims.
6. Build disagreement matrix.
7. Critic attacks unsupported assumptions.
8. Evidence Validator checks claims.
9. Resolve conflicts by returning to primary evidence.
10. Synthesizer creates report.
11. Attach citations.
12. Store trajectories.

For every workflow step implement:
- input schema;
- output schema;
- validation;
- timeout;
- retry behavior where appropriate;
- structured logging;
- trace/span;
- error mapping;
- state transition.

Create `docs/architecture.md` with an architecture diagram and `docs/sequence.md` with the main sequence diagram.

---

## 6. Functional requirements

Strict output schemas. Role-specific tool boundaries. Citation requirement. Maximum debate rounds. Allow unresolved outcome when evidence is inconclusive. Provenance for every claim. Graph visualization of agents, claims, evidence, contradictions.

### Baseline behavior required in every project

#### Input validation
Reject malformed requests with stable API error codes.

#### Configuration
Use a typed settings object and environment variables. Provide `.env.example`.

#### Model-provider abstraction
Do not call an LLM provider directly from business logic. Use a provider interface such as:

```python
class LLMProvider(Protocol):
    async def generate(
        self,
        messages: list[Message],
        *,
        response_schema: type[BaseModel] | None = None,
        temperature: float = 0.0,
    ) -> LLMResponse:
        ...
```

#### Structured output
When structured data is expected:
1. validate with Pydantic;
2. capture invalid output safely;
3. perform only a bounded repair/retry;
4. return a typed failure state if validation still fails.

#### Agent loop limits
Every loop must have:
- maximum iterations;
- maximum wall-clock time;
- maximum token budget;
- explicit terminal states.

#### Failure taxonomy
Distinguish validation failure, authentication failure, authorization failure, provider timeout, rate limit, provider outage, tool failure, database failure, evaluation failure, and programming error. Do not turn every failure into HTTP 500.

---

## 7. Agent design

Do not put the entire application into one giant prompt.

Create explicit nodes/services for planning or routing, tool execution, retrieval, validation, evaluation, synthesis, and termination as appropriate.

For each node document:

| Field | Required |
|---|---|
| Purpose | Yes |
| Input schema | Yes |
| Output schema | Yes |
| Tools used | Yes |
| State modified | Yes |
| Failure states | Yes |
| Timeout | Yes |
| Retry policy | Yes |
| Observability | Yes |
| Security considerations | Yes |

The agent must terminate cleanly without relying on the LLM to decide that it should stop.

---

## 8. Database design

Use migrations. Do not create production tables implicitly from application startup.

Persist, where relevant:
- request/run ID;
- timestamps;
- status;
- model/provider/version;
- tool calls;
- evidence;
- evaluation results;
- errors;
- latency/cost;
- audit events.

For every table document purpose, primary key, foreign keys, indexes, sensitive fields, and retention considerations.

---

## 9. API design

Use FastAPI + Pydantic.

Provide:
- health endpoint;
- readiness endpoint;
- main workflow endpoint;
- status endpoint;
- run/trace endpoint;
- evaluation endpoint where relevant;
- protected administrative endpoints where needed.

Use a stable response envelope:

```json
{
  "request_id": "req_123",
  "status": "completed",
  "data": {},
  "errors": []
}
```

Document every endpoint in OpenAPI and provide example requests.

---

## 10. Frontend requirements

Build a workflow-specific UI, not a generic chatbot.

Show the project's distinctive behavior: evidence, model predictions, tool graph, approval state, memory, trace, evaluation, cost routing, or benchmark results as applicable.

Handle loading, empty, partial, error, retry, and completed states.

Use TypeScript types synchronized with the API.

---

## 11. Evaluation plan

Measure evidence-supported accuracy, unsupported claims, contradiction detection, final correctness, specialist diversity, redundant-tool use, latency, and cost. Compare single-agent RAG versus multi-agent debate and report whether quality improvement justifies extra cost/latency.

Create:

```text
evaluation/
├── datasets/
├── evaluators/
├── runners/
├── reports/
└── README.md
```

Provide a reproducible command such as:

```bash
make eval
```

or:

```bash
python -m evaluation.run --config configs/eval.yaml
```

Do not write claimed performance numbers into the README until the experiment has actually been run.

---

## 12. Testing requirements

### Unit tests
Test domain logic, parsers, validators, routing policies, scoring functions, and state transitions.

### Integration tests
Run against real local PostgreSQL/Redis containers where used.

### Agent tests
Test representative trajectories with mocked model/tool providers.

### Failure tests
Force timeouts, malformed outputs, empty retrieval, database errors, tool errors, provider errors, and permission errors.

### Regression tests
Keep a small stable benchmark and run it in CI.

### Load tests
Measure throughput and p95/p99 latency for important API paths.

Run the suite with:

```bash
pytest
```

---

## 13. Security requirements

Implement:
- secrets through environment/secret management;
- authentication for protected endpoints;
- RBAC where needed;
- input/output validation;
- least-privilege tool permissions;
- prompt-injection-aware tool/retrieval boundaries;
- PII redaction in logs;
- dependency scanning;
- non-root containers where practical;
- restricted network for sandboxes;
- audit logging for consequential actions.

Create `docs/security.md` with assets, trust boundaries, threats, mitigations, and residual risks.

---

## 14. Observability requirements

Every request receives a correlation ID.

Capture, where applicable:
- request latency;
- model calls;
- model latency;
- input/output tokens;
- estimated cost;
- retrieval latency;
- tool latency;
- retries;
- evaluation score;
- failure category.

Use OpenTelemetry traces and Prometheus-compatible metrics where practical.

Never log raw secrets or unrestricted sensitive prompts.

---

## 15. Docker and local environment

Create:
- `Dockerfile`;
- `docker-compose.yml`;
- `.dockerignore`;
- `.env.example`;
- `Makefile`.

A clean-machine setup should be approximately:

```bash
git clone <repo>
cd <repo>
cp .env.example .env
docker compose up --build
```

Then documented seed/initialization commands should make the demo usable.

---

## 16. CI/CD

GitHub Actions should run:
- lint;
- type checking;
- unit tests;
- integration tests;
- dependency/security checks;
- fast evaluation regression suite;
- Docker build.

Use a small regression benchmark on PRs and a larger scheduled benchmark when appropriate.

---

## 17. Deployment

Provide a production-style deployment design even if the first release is local.

Document service boundaries, containers, environment variables, database, queues, object storage, secrets, autoscaling, health checks, monitoring, and rollback.

Provide Kubernetes manifests or Helm/Kustomize configuration where it materially improves the project.

---

## 18. Failure-mode matrix

Create `docs/failure_modes.md` with at least:

| Failure | Detection | Recovery | User-visible result |
|---|---|---|---|
| Invalid input | Pydantic | Reject | Validation error |
| Model timeout | timeout wrapper | Retry/fallback | Processing state |
| Tool timeout | timeout wrapper | Retry/circuit breaker | Partial/failure result |
| Empty retrieval | retrieval validator | Query rewrite/abstain | Insufficient evidence |
| Invalid structured output | schema validator | Bounded repair | Typed failure |
| Database outage | DB exception | Retry/backoff | Temporary unavailable |
| Agent loop | iteration detector | Terminate | Loop detected |
| Permission violation | authorization | Block | Forbidden action |

Add project-specific failures.

---

## 19. Performance and cost engineering

Measure:
- p50/p95/p99 latency;
- token usage;
- cost per successful task;
- cache hit rate where applicable;
- database latency;
- retrieval latency;
- concurrency.

Document at least three trade-offs, such as quality vs latency, retrieval depth vs context size, number of agents vs cost, synchronous vs asynchronous execution, or hosted vs local models.

---

## 20. Portfolio presentation

Produce:
1. architecture diagram;
2. workflow/sequence diagram;
3. 3–5 screenshots;
4. 60–120 second demo;
5. benchmark/evaluation chart;
6. failure-analysis table;
7. concise case study;
8. reproducible README;
9. technical trade-offs;
10. limitations and next steps.

Do not claim production deployment if it was only run locally.

---

## 21. Suggested implementation phases

### Phase 1 — Foundation
Repository, configuration, domain models, database, Docker, linting, typing, health endpoints.

### Phase 2 — Core functionality
Implement deterministic data/business flow before adding the LLM.

### Phase 3 — AI layer
Add provider abstraction, structured outputs, retrieval/tool interfaces, and agent state machine.

### Phase 4 — Reliability
Add retries, timeouts, idempotency, bounded loops, failure states, and audit/trace events.

### Phase 5 — Evaluation
Create benchmark, baseline, evaluators, experiment runner, and regression tests.

### Phase 6 — UI
Expose workflow, evidence, trace, and evaluation.

### Phase 7 — Operations
Add metrics, traces, dashboards, load tests, container hardening, and deployment configuration.

### Phase 8 — Portfolio
Write architecture documentation, benchmark report, failure analysis, screenshots, demo, and case study.

---

## 22. Definition of Done

- [ ] Clean repository can be cloned and started.
- [ ] `.env.example` is complete.
- [ ] Docker Compose works.
- [ ] Database migrations work.
- [ ] Main API works.
- [ ] Main workflow works.
- [ ] Agent state is bounded.
- [ ] Tool schemas are typed.
- [ ] Errors are handled.
- [ ] Tests pass.
- [ ] Evaluation benchmark runs.
- [ ] Baseline comparison exists.
- [ ] Metrics are real and reproducible.
- [ ] Observability exists.
- [ ] Security documentation exists.
- [ ] Failure-mode documentation exists.
- [ ] README is complete.
- [ ] Architecture diagram exists.
- [ ] UI/demo exists where specified.
- [ ] No secrets are committed.
- [ ] No fabricated performance claims exist.
- [ ] Limitations are documented.

---

## 23. Final instruction to the implementing LLM

You are the lead engineer responsible for implementing this repository end-to-end.

Do not stop after generating a plan. Implement incrementally. After every major phase:
1. run tests;
2. inspect failures;
3. fix failures;
4. update documentation;
5. continue.

Do not create fake implementations merely to satisfy acceptance criteria. If a third-party service is unavailable, create a clearly documented local adapter/mock for development and keep the real provider interface intact.

Do not hard-code benchmark results.

Do not claim a feature works unless it has been exercised by a test or documented manual verification.

At completion provide:
- changed files;
- commands used to run the system;
- test results;
- evaluation results;
- known limitations;
- next engineering improvements.

---
# COMPLETE HUMAN EXECUTION PLAYBOOK

## External requirements
- Reuse Project 2 SEC corpus whenever possible.
- SEC API credentials are not required for `data.sec.gov`; comply with SEC access policy.
- Official: https://www.sec.gov/developer

## Exact sequence
1. Freeze the Project 2 corpus.
2. Create Bull/Bear specialist schemas.
3. Implement two-agent debate first.
4. Add Evidence Validator.
5. Build disagreement matrix.
6. Add Financial and Risk agents.
7. Add Critic.
8. Add Synthesizer.
9. Add graph/provenance UI.
10. Compare single-agent RAG vs multi-agent system.
11. Measure whether quality improvement justifies cost/latency.

## “Done” before moving on
- Every specialist has a distinct role.
- Every material claim has evidence.
- Unresolved disagreements remain unresolved instead of being forced into consensus.

## If stuck
Start with two agents only. Add more specialists only after the evidence/conflict pipeline works.

## Future enhancements
Temporal swarms, knowledge graphs, adaptive agent count, agent-specific tool permissions, and learned debate termination.
