# Data

## Origin and licensing

This project **freezes** the synthetic SEC-style corpus from Project 2
(`02_citation_grounded_financial_research_agent`). The prose is original sample
text written for research/demo use. Figures are illustrative and are **not** a
redistribution of EDGAR HTML.

License: CC0 / public-domain dedication for the sample corpus; MIT for code.

Real EDGAR metadata can be fetched later; comply with
[SEC developer policy](https://www.sec.gov/developer). Identify a contact
User-Agent and keep request rates conservative. SEC API credentials are not
required for `data.sec.gov`.

## Schema

Each document has issuer `{name,ticker,cik}`, `document_type` (10-K / 10-Q / 8-K),
`reporting_period`, `publication_date`, `source_url`, `content_hash`, and
`pages[].{page,section,text}`. Chunks inherit those fields.

## Preprocessing

1. Keep page/section boundaries (one chunk per page).
2. Embed with hashing-trick vectors by default (deterministic, no API key).
3. Index BM25 + dense vectors; fuse with RRF; heuristic (or optional cross-encoder) rerank.

## Train / validation / test

This is an evaluation set, not a supervised trainer.

- `regression`: 6 frozen IDs used in CI (`make eval`)
- `full`: 10 items including mixed, contradictory, temporal, comparison, and unanswerable
- No training split

## Benchmark construction

Questions require sourced numbers, mixed polarity (growth vs decline), 8-K vs 10-Q
conflicts, and out-of-corpus abstention. Gold labels store topic keys and values.

## Known limitations

- Synthetic numbers are internally consistent but must not be used as market data.
- Hashing embeddings are weaker than a real encoder.
- The corpus is small (five issuers, ~20 filings).
