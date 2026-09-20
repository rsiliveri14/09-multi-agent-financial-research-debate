export type Role = "analyst" | "admin";

export const TOKENS: Record<Role, string> = {
  analyst: "dev-analyst-token",
  admin: "dev-admin-token",
};

export type Envelope<T> = {
  request_id: string;
  status: string;
  data: T | null;
  errors: { code: string; message: string }[];
};

export type Citation = {
  document_type: string;
  page: number;
  section: string;
  evidence_span: string;
  issuer_ticker: string;
  reporting_period: string;
  source_url: string;
};

export type Claim = {
  id: string;
  agent_role: string;
  topic_key: string;
  text: string;
  polarity: string;
  confidence: number;
  value: number | null;
  supported: boolean | null;
  stale_source: boolean;
  citations: Citation[];
};

export type Brief = {
  role: string;
  stance: string;
  summary: string;
  claims: Claim[];
  assumptions: string[];
  counterarguments: string[];
  confidence: number;
};

export type DisagreementCell = {
  topic_key: string;
  status: string;
  agreement_score: number;
  values: Record<string, number | null>;
  polarities: Record<string, string>;
  notes: string;
};

export type GraphNode = { id: string; kind: string; label: string; meta: Record<string, unknown> };
export type GraphEdge = { source: string; target: string; kind: string; label: string };

export type DebateResult = {
  request_id: string;
  status: string;
  question: string;
  plan: { question_type: string; tickers: string[]; topics: string[]; rationale: string };
  briefs: Brief[];
  claims: Claim[];
  disagreement: DisagreementCell[];
  critic_findings: { claim_id: string; agent_role: string; severity: string; attack: string; recommendation: string }[];
  synthesis: {
    headline: string;
    executive_summary: string;
    agreed_facts: string[];
    unresolved: string[];
    material_risks: string[];
    citations: Citation[];
    confidence: number;
    outcome: string;
  };
  graph: { nodes: GraphNode[]; edges: GraphEdge[] };
  single_agent: { answer: string; abstained: boolean; confidence: number } | null;
  metrics: {
    latency_ms: number;
    retrieval_latency_ms: number;
    token_input: number;
    token_output: number;
    estimated_cost_usd: number;
    specialist_diversity: number;
    unsupported_claim_rate: number;
    contradiction_count: number;
    redundant_tool_calls: number;
    debate_rounds: number;
  };
  terminal_state: string;
};

export type TraceEvent = { seq: number; event_type: string; node: string; payload: Record<string, unknown> };

export const SAMPLES = [
  "What were Apple total net sales in FY2024, and did Greater China grow?",
  "Apple Q2 FY2025 net sales: reconcile the 8-K preliminary figure versus the 10-Q.",
  "NVIDIA FY2025 Data Center revenue versus export-control risk for FY2026 visibility.",
  "Tesla Q1 2025 deliveries: 8-K preliminary versus 10-Q, and what happened to automotive gross margin?",
  "What were Amazon net sales and AWS net sales in 2024?",
  "What is Apple's FY2030 iPhone unit guidance versus Samsung market share?",
];
