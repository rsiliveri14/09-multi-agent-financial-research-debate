# Node catalog

Every workflow node has a bounded policy. Details are also served at `GET /v1/admin/nodes`.
Machine-readable source: `src/agents/registry.py`.

The agent loop is bounded by `MAX_ITERATIONS`, `MAX_WALL_CLOCK_SECONDS`, `MAX_TOKEN_BUDGET`, and `MAX_DEBATE_ROUNDS`. The LLM cannot decide to continue.

| Node | Purpose | Input | Output | Tools | State | Failure | Timeout | Retry | Observability | Security |
|---|---|---|---|---|---|---|---|---|---|---|
| plan | Classify the question and produce specialist retrieval queries | PlannerInput | ResearchPlan | — | plan | validation_failed | 2s | none | span:plan | Question length-bounded; redacted in logs |
| retrieve | Hybrid retrieve + rerank filing chunks per specialist query | ResearchPlan | list[RetrievedChunk] | retrieve_filings | evidence | tool_failure / insufficient_evidence | 6s | 2 | span:retrieve, retrieval_latency_ms | Retrieved text is untrusted; never executed |
| specialists | Bull, Bear, Financial, Risk, Evidence emit typed claims | SpecialistInput | SpecialistBrief | retrieve_filings | briefs | provider_timeout / validation_failed | 20s | bounded structured-output repair | span:specialist, token_usage | Role-specific queries; no write tools |
| normalize | Canonicalize claims onto `TICKER.metric.period` | NormalizeInput | NormalizeOutput | — | claims | validation_failed | 2s | none | span:normalize | Deterministic; no external I/O |
| disagreement | Build the matrix and count contradictions | DisagreementInput | DisagreementOutput | — | disagreement, unresolved | validation_failed | 2s | none | span:disagreement, contradiction_count | Deterministic; no external I/O |
| critic | Attack unsupported assumptions, cherry-picking, stale 8-Ks | CriticInput | CriticOutput | — | critic_findings | validation_failed | 3s | none | span:critic | Read-only over claims and briefs |
| validate | Check each claim against citation span and numbers | ValidatorInput | ValidatorOutput | — | validations, claims | validation_failed | 3s | none | span:validate, unsupported_claim_rate | Citations must resolve to indexed chunks |
| resolve | Prefer 10-K/10-Q over 8-K; else leave unresolved | DisagreementOutput | claims + unresolved keys | retrieve_filings | claims, resolved, unresolved | insufficient_evidence | 6s | one extra retrieve | span:resolve | Cannot invent values |
| synthesize | Final report without forcing consensus | SynthesizerInput | SynthesisReport | — | report | insufficient_evidence / unresolved | 4s | none | span:synthesize | Citations only from retrieved evidence |
