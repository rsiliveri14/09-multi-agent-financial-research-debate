# Evaluation

Measure whether multi-agent debate improves *evidence-grounded* quality enough to
justify extra latency and token cost versus single-agent RAG.

## Suites

| Suite | Command | Items |
|---|---|---|
| regression | `make eval` | 6 frozen questions |
| full | `make eval-full` | 10 questions |

Config: `configs/eval.yaml`.

## Metrics

- **evidence-supported accuracy** — gold numeric facts appear in supported claims
- **unsupported claim rate** — validator rejects
- **contradiction detection** — disagreement matrix fires when gold expects conflict
- **final correctness** — accuracy plus preferred-document bonus (10-Q over 8-K)
- **specialist diversity** — pairwise Jaccard distance of topic sets
- **redundant-tool use** — duplicate retrieval queries
- **latency** — p50/p95/p99
- **cost** — estimated USD from token accounting

Do not copy numbers into the README until `make eval` has been run on this machine.

## Output

JSON reports land in `evaluation/reports/`. CI stores the regression file as an artifact of the run.
