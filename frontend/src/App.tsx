import type { DebateResult, GraphEdge, GraphNode, Role } from "./types";
import { SAMPLES } from "./types";
import { fetchCorpus, fetchDebate, fetchHealth, fetchLatestEval, fetchTrace, listDebates, runDebate, runEval } from "./api";
import { useEffect, useMemo, useState } from "react";

type Tab = "debate" | "graph" | "trace" | "eval";
type UiState = "empty" | "loading" | "partial" | "error" | "completed";

const ROLE_COLOR: Record<string, string> = {
  bull: "#3ee0c4",
  bear: "#ff5d73",
  financial: "#7db4ff",
  risk: "#f5c15d",
  evidence: "#c4b5fd",
};

export default function App() {
  const [role, setRole] = useState<Role>("analyst");
  const [tab, setTab] = useState<Tab>("debate");
  const [question, setQuestion] = useState(SAMPLES[0]);
  const [health, setHealth] = useState<boolean | null>(null);
  const [result, setResult] = useState<DebateResult | null>(null);
  const [runs, setRuns] = useState<{ request_id: string; question: string; terminal_state: string; latency_ms: number }[]>([]);
  const [trace, setTrace] = useState<{ seq: number; event_type: string; node: string }[]>([]);
  const [evalReport, setEvalReport] = useState<Record<string, unknown> | null>(null);
  const [corpus, setCorpus] = useState<{ chunks: number; tickers: Record<string, number> } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [demoNote, setDemoNote] = useState<string | null>(null);

  const uiState: UiState = loading
    ? result
      ? "partial"
      : "loading"
    : error
      ? "error"
      : result
        ? "completed"
        : "empty";

  async function refresh() {
    const alive = await fetchHealth();
    setHealth(alive);
    if (!alive) return;
    const listed = await listDebates(role);
    if (listed.data) setRuns(listed.data.items);
    const c = await fetchCorpus(role);
    if (c.data) setCorpus(c.data);
    const latest = await fetchLatestEval(role);
    if (latest.data && Object.keys(latest.data).length) setEvalReport(latest.data);
  }

  useEffect(() => {
    void refresh();
  }, [role]);

  async function submit(text: string) {
    setLoading(true);
    setError(null);
    setTab("debate");
    try {
      const envelope = await runDebate(role, text);
      if (envelope.errors?.length) {
        setError(envelope.errors.map((item) => item.message).join("; "));
        if (envelope.data) setResult(envelope.data);
      } else {
        setResult(envelope.data);
      }
      if (envelope.data) {
        const traced = await fetchTrace(role, envelope.data.request_id);
        setTrace(traced.data?.events ?? []);
      }
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "debate failed");
    } finally {
      setLoading(false);
    }
  }

  async function loadRun(id: string) {
    setLoading(true);
    setError(null);
    try {
      const envelope = await fetchDebate(role, id);
      if (envelope.errors?.length) {
        setError(envelope.errors.map((item) => item.message).join("; "));
        return;
      }
      setResult(envelope.data);
      const traced = await fetchTrace(role, id);
      setTrace(traced.data?.events ?? []);
      setTab("debate");
    } catch (err) {
      setError(err instanceof Error ? err.message : "load failed");
    } finally {
      setLoading(false);
    }
  }

  async function evaluate() {
    setLoading(true);
    setError(null);
    try {
      const envelope = await runEval("admin");
      if (envelope.errors?.length) setError(envelope.errors.map((item) => item.message).join("; "));
      setEvalReport(envelope.data);
      setTab("eval");
    } catch (err) {
      setError(err instanceof Error ? err.message : "eval failed");
    } finally {
      setLoading(false);
    }
  }

  async function playDemo() {
    setDemoNote("1/4 Mixed Apple question");
    setQuestion(SAMPLES[0]);
    await submit(SAMPLES[0]);
    setTab("graph");
    setDemoNote("2/4 Provenance graph");
    await new Promise((resolve) => window.setTimeout(resolve, 900));
    setDemoNote("3/4 8-K vs 10-Q (unresolved allowed)");
    setQuestion(SAMPLES[1]);
    await submit(SAMPLES[1]);
    setDemoNote("4/4 Eval vs single-agent");
    await evaluate();
    setDemoNote("Demo finished — synthetic corpus, heuristic provider, not investment advice.");
  }

  return (
    <div className="min-h-screen bg-ink text-slate-100">
      <header className="border-b border-line px-6 py-4 flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-accent">Multi-agent research</p>
          <h1 className="text-xl font-semibold">Financial Debate Floor</h1>
        </div>
        <div className="flex items-center gap-3 text-sm">
          <span className={health ? "text-accent" : "text-bear"}>{health ? "API live" : "API down"}</span>
          <span className="text-[10px] uppercase tracking-wide text-slate-500">{uiState}</span>
          <select
            className="bg-panel border border-line rounded px-2 py-1"
            value={role}
            onChange={(event) => setRole(event.target.value as Role)}
          >
            <option value="analyst">analyst</option>
            <option value="admin">admin</option>
          </select>
        </div>
      </header>

      <main className="grid grid-cols-1 lg:grid-cols-[320px_1fr] gap-4 p-4">
        <aside className="space-y-4">
          <section className="bg-panel border border-line rounded-lg p-4">
            <h2 className="text-sm font-semibold mb-2">Research question</h2>
            <textarea
              className="w-full h-28 bg-ink border border-line rounded p-2 text-sm"
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
            />
            <button
              className="mt-2 w-full bg-accent text-ink font-semibold rounded py-2 disabled:opacity-50"
              disabled={loading || !question.trim()}
              onClick={() => void submit(question)}
            >
              {loading ? "Debating…" : "Run debate"}
            </button>
            <button
              className="mt-2 w-full border border-line rounded py-2 text-xs text-slate-300 disabled:opacity-50"
              disabled={loading}
              onClick={() => void playDemo()}
            >
              Play 90s demo
            </button>
            {error && (
              <button
                className="mt-2 w-full border border-bear text-bear rounded py-2 text-xs"
                onClick={() => void submit(question)}
              >
                Retry last question
              </button>
            )}
            <div className="mt-3 space-y-1">
              {SAMPLES.map((sample) => (
                <button
                  key={sample}
                  className="block text-left text-xs text-slate-400 hover:text-accent"
                  onClick={() => setQuestion(sample)}
                >
                  {sample}
                </button>
              ))}
            </div>
          </section>
          <section className="bg-panel border border-line rounded-lg p-4">
            <h2 className="text-sm font-semibold mb-2">Corpus</h2>
            {corpus ? (
              <p className="text-xs text-slate-400">
                {corpus.chunks} chunks · {Object.keys(corpus.tickers).join(", ")}
              </p>
            ) : (
              <p className="text-xs text-slate-500">No corpus loaded.</p>
            )}
            <h3 className="text-sm font-semibold mt-3 mb-1">Recent runs</h3>
            <ul className="space-y-1 max-h-48 overflow-auto text-xs">
              {runs.slice(0, 12).map((run) => (
                <li key={run.request_id}>
                  <button
                    className="text-left text-slate-400 hover:text-accent"
                    onClick={() => void loadRun(run.request_id)}
                  >
                    {run.terminal_state} · {run.latency_ms}ms · {run.question.slice(0, 48)}
                  </button>
                </li>
              ))}
              {!runs.length && <li className="text-slate-500">Empty.</li>}
            </ul>
          </section>
        </aside>

        <section>
          <nav className="flex gap-2 mb-3">
            {(["debate", "graph", "trace", "eval"] as Tab[]).map((item) => (
              <button
                key={item}
                className={`px-3 py-1 rounded text-sm ${tab === item ? "bg-accent text-ink" : "bg-panel border border-line"}`}
                onClick={() => setTab(item)}
              >
                {item}
              </button>
            ))}
            <button className="ml-auto px-3 py-1 rounded text-sm bg-panel border border-line" onClick={() => void evaluate()}>
              Compare vs single-agent
            </button>
          </nav>

          {demoNote && <div className="mb-3 border border-accent/40 text-accent rounded p-3 text-sm">{demoNote}</div>}
          {error && <div className="mb-3 border border-bear text-bear rounded p-3 text-sm">{error}</div>}
          {uiState === "empty" && <EmptyState />}
          {(uiState === "loading" || uiState === "partial") && (
            <p className="text-slate-400 mb-3">Specialists retrieving evidence…</p>
          )}
          {result && tab === "debate" && <DebateView result={result} />}
          {result && tab === "graph" && <GraphView nodes={result.graph.nodes} edges={result.graph.edges} />}
          {tab === "trace" && <TraceView events={trace} />}
          {tab === "eval" && <EvalView report={evalReport} />}
        </section>
      </main>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="border border-dashed border-line rounded-lg p-10 text-center text-slate-400">
      Run a question to see Bull vs Bear disagreement, the evidence matrix, and an unresolved-capable synthesis.
    </div>
  );
}

function DebateView({ result }: { result: DebateResult }) {
  return (
    <div className="space-y-4">
      <div className="bg-panel border border-line rounded-lg p-4">
        <p className="text-xs uppercase tracking-wide text-slate-400">
          {result.plan.question_type} · {result.terminal_state} · {result.metrics.latency_ms}ms · $
          {result.metrics.estimated_cost_usd.toFixed(6)}
        </p>
        <h2 className="text-lg font-semibold mt-1">{result.synthesis.headline}</h2>
        <p className="text-sm text-slate-300 mt-2">{result.synthesis.executive_summary}</p>
        <p className="text-xs text-slate-500 mt-2">{result.plan.rationale}</p>
      </div>
      <div className="grid md:grid-cols-2 xl:grid-cols-5 gap-3">
        {result.briefs.map((brief) => (
          <article key={brief.role} className="bg-panel border border-line rounded-lg p-3">
            <header className="flex justify-between items-center mb-2">
              <span className="font-semibold capitalize" style={{ color: ROLE_COLOR[brief.role] ?? "#fff" }}>
                {brief.role}
              </span>
              <span className="text-xs text-slate-400">{brief.stance}</span>
            </header>
            <p className="text-xs text-slate-400 mb-2">{brief.summary}</p>
            <ul className="space-y-2">
              {brief.claims.slice(0, 3).map((claim) => (
                <li key={claim.id} className="text-xs">
                  <span className={claim.supported === false ? "text-bear" : "text-slate-200"}>{claim.text}</span>
                  {claim.citations[0] && (
                    <p className="text-[10px] text-slate-500 mt-1">
                      {claim.citations[0].issuer_ticker} {claim.citations[0].document_type} p.{claim.citations[0].page}{" "}
                      {claim.citations[0].section}
                    </p>
                  )}
                </li>
              ))}
            </ul>
          </article>
        ))}
      </div>
      <Matrix cells={result.disagreement} />
      <div className="grid md:grid-cols-2 gap-3">
        <div className="bg-panel border border-line rounded-lg p-4">
          <h3 className="font-semibold mb-2">Critic</h3>
          <ul className="space-y-2 text-xs">
            {result.critic_findings.slice(0, 6).map((finding, index) => (
              <li key={`${finding.claim_id}-${index}`}>
                <span className="text-warn">{finding.severity}</span> · {finding.attack}
              </li>
            ))}
            {!result.critic_findings.length && <li className="text-slate-500">No attacks.</li>}
          </ul>
        </div>
        <div className="bg-panel border border-line rounded-lg p-4">
          <h3 className="font-semibold mb-2">Unresolved / risks</h3>
          <ul className="space-y-1 text-xs text-slate-300">
            {result.synthesis.unresolved.map((item) => (
              <li key={item}>⚠ {item}</li>
            ))}
            {result.synthesis.material_risks.map((item) => (
              <li key={item}>Risk: {item}</li>
            ))}
            {!result.synthesis.unresolved.length && !result.synthesis.material_risks.length && (
              <li className="text-slate-500">None recorded.</li>
            )}
          </ul>
          {result.single_agent && (
            <div className="mt-3 border-t border-line pt-3">
              <p className="text-xs uppercase text-slate-500">Single-agent baseline</p>
              <p className="text-xs mt-1">{result.single_agent.answer}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function Matrix({ cells }: { cells: DebateResult["disagreement"] }) {
  const statusColor: Record<string, string> = {
    agree: "bg-emerald-900/70",
    disagree: "bg-rose-900/80",
    partial: "bg-amber-900/70",
    missing: "bg-slate-800",
  };
  return (
    <div className="bg-panel border border-line rounded-lg p-4 overflow-auto">
      <h3 className="font-semibold mb-2">Disagreement matrix</h3>
      <table className="w-full text-xs">
        <thead className="text-slate-400">
          <tr>
            <th className="text-left py-1">Topic</th>
            <th>Status</th>
            <th>Score</th>
            <th className="text-left">Notes</th>
          </tr>
        </thead>
        <tbody>
          {cells.map((cell) => (
            <tr key={cell.topic_key} className={statusColor[cell.status] ?? ""}>
              <td className="py-1 pr-2 font-mono">{cell.topic_key}</td>
              <td className="text-center">{cell.status}</td>
              <td className="text-center">{cell.agreement_score.toFixed(2)}</td>
              <td>{cell.notes}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function GraphView({ nodes, edges }: { nodes: GraphNode[]; edges: GraphEdge[] }) {
  const layout = useMemo(() => layoutGraph(nodes), [nodes]);
  return (
    <div className="bg-panel border border-line rounded-lg p-4 overflow-auto">
      <h3 className="font-semibold mb-2">Provenance graph</h3>
      <svg viewBox="0 0 960 520" className="w-full min-h-[420px]">
        {edges.map((edge, index) => {
          const from = layout[edge.source];
          const to = layout[edge.target];
          if (!from || !to) return null;
          const color = edge.kind === "conflicts" ? "#ff5d73" : "#3a4a66";
          return <line key={`${edge.source}-${edge.target}-${index}`} x1={from.x} y1={from.y} x2={to.x} y2={to.y} stroke={color} strokeWidth="1" />;
        })}
        {nodes.map((node) => {
          const pos = layout[node.id];
          if (!pos) return null;
          return (
            <g key={node.id}>
              <circle cx={pos.x} cy={pos.y} r={node.kind === "agent" ? 18 : 11} fill={colorFor(node)} />
              <text x={pos.x + 16} y={pos.y + 4} fontSize="10" fill="#cbd5e1">
                {node.label.slice(0, 28)}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

function layoutGraph(nodes: GraphNode[]): Record<string, { x: number; y: number }> {
  const bands: Record<string, number> = {
    question: 40,
    agent: 120,
    claim: 240,
    evidence: 360,
    contradiction: 440,
    synthesis: 500,
  };
  const grouped: Record<string, GraphNode[]> = {};
  for (const node of nodes) {
    grouped[node.kind] = grouped[node.kind] ?? [];
    grouped[node.kind].push(node);
  }
  const positions: Record<string, { x: number; y: number }> = {};
  for (const [kind, group] of Object.entries(grouped)) {
    group.forEach((node, index) => {
      const y = bands[kind] ?? 260;
      const x = 80 + (index * 820) / Math.max(1, group.length);
      positions[node.id] = { x, y };
    });
  }
  return positions;
}

function colorFor(node: GraphNode): string {
  if (node.kind === "agent") return ROLE_COLOR[node.label] ?? "#7db4ff";
  if (node.kind === "contradiction") return "#ff5d73";
  if (node.kind === "evidence") return "#64748b";
  if (node.kind === "synthesis") return "#f5c15d";
  if (node.kind === "question") return "#3ee0c4";
  return "#94a3b8";
}

function TraceView({ events }: { events: { seq: number; event_type: string; node: string }[] }) {
  if (!events.length) return <p className="text-slate-500">No trace yet.</p>;
  return (
    <ol className="bg-panel border border-line rounded-lg p-4 space-y-2 text-sm">
      {events.map((event) => (
        <li key={event.seq} className="flex gap-3">
          <span className="text-slate-500 w-8">{event.seq}</span>
          <span className="text-accent">{event.node || event.event_type}</span>
          <span className="text-slate-400">{event.event_type}</span>
        </li>
      ))}
    </ol>
  );
}

function EvalView({ report }: { report: Record<string, unknown> | null }) {
  if (!report || !Object.keys(report).length) {
    return <p className="text-slate-500">Run the regression suite from the button above (admin token).</p>;
  }
  const multi = (report.multi_agent as Record<string, number>) || {};
  const single = (report.single_agent as Record<string, number>) || {};
  const keys = ["final_correctness", "contradiction_detection", "evidence_supported_accuracy", "latency_ms_p50", "cost_usd_mean"];
  return (
    <div className="bg-panel border border-line rounded-lg p-4 space-y-4">
      <h3 className="font-semibold">Single-agent RAG vs multi-agent debate</h3>
      <div className="space-y-3">
        {keys.map((key) => (
          <EvalBar key={key} label={key} multi={Number(multi[key] ?? 0)} single={Number(single[key] ?? 0)} />
        ))}
      </div>
      <table className="w-full text-sm">
        <thead className="text-slate-400">
          <tr>
            <th className="text-left">Metric</th>
            <th>Multi-agent</th>
            <th>Single-agent</th>
          </tr>
        </thead>
        <tbody>
          {keys.map((key) => (
            <tr key={key} className="border-t border-line">
              <td className="py-2">{key}</td>
              <td className="text-center">{fmt(multi[key])}</td>
              <td className="text-center">{fmt(single[key])}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function EvalBar({ label, multi, single }: { label: string; multi: number; single: number }) {
  const peak = Math.max(multi, single, 0.001);
  return (
    <div>
      <p className="text-xs text-slate-400 mb-1">{label}</p>
      <div className="space-y-1">
        <div className="flex items-center gap-2">
          <span className="w-16 text-[10px] text-accent">multi</span>
          <div className="flex-1 h-2 bg-ink rounded">
            <div className="h-2 rounded bg-accent" style={{ width: `${Math.min(100, (multi / peak) * 100)}%` }} />
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-16 text-[10px] text-slate-500">single</span>
          <div className="flex-1 h-2 bg-ink rounded">
            <div className="h-2 rounded bg-slate-500" style={{ width: `${Math.min(100, (single / peak) * 100)}%` }} />
          </div>
        </div>
      </div>
    </div>
  );
}

function fmt(value: number | undefined): string {
  if (value === undefined || Number.isNaN(value)) return "—";
  return Number.isInteger(value) ? String(value) : value.toFixed(3);
}
