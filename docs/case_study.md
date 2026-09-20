# Case study — Multi-agent financial research debate

**Problem.** Single-agent RAG over filings collapses mixed evidence into one
paragraph. Preliminary 8-Ks get treated like 10-Qs. Disagreement is invisible.

**Approach.** Five specialists share a retrieved fact pool and emit typed claims
(topic key, polarity, confidence, assumptions, counterarguments, citations). A
deterministic matrix, critic, and validator sit *after* generation. Conflicts
resolve by primary-evidence rank; leftover conflicts stay unresolved.

**Result.** A workflow UI that shows the debate, not a chatbot. A regression
benchmark that scores contradiction detection and 10-Q preference against a
single-agent baseline. Default path runs offline with a heuristic provider.

**Trade-offs.** Five retrievals cost more latency than one. Hashing embeddings
are local and weak. Heuristic specialists are inspectable but not a frontier
model. Unresolved outcomes are a feature.

**Not claimed.** Production brokerage deployment. Real EDGAR completeness.
Profitability of any ticker.
