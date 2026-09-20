import type { DebateResult, Envelope, Role, TraceEvent } from "./types";
import { TOKENS } from "./types";

async function request<T>(path: string, role: Role, init?: RequestInit): Promise<Envelope<T>> {
  const response = await fetch(path, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${TOKENS[role]}`,
      ...(init?.headers ?? {}),
    },
  });
  return (await response.json()) as Envelope<T>;
}

export async function fetchHealth(): Promise<boolean> {
  try {
    const response = await fetch("/health");
    return response.ok;
  } catch {
    return false;
  }
}

export function runDebate(role: Role, question: string) {
  return request<DebateResult>("/v1/debate", role, { method: "POST", body: JSON.stringify({ question }) });
}

export function fetchDebate(role: Role, id: string) {
  return request<DebateResult>(`/v1/debate/${id}`, role);
}

export function fetchTrace(role: Role, id: string) {
  return request<{ events: TraceEvent[]; terminal_state: string }>(`/v1/debate/${id}/trace`, role);
}

export function listDebates(role: Role) {
  return request<{ items: { request_id: string; question: string; status: string; terminal_state: string; latency_ms: number }[] }>(
    "/v1/debates",
    role,
  );
}

export function runEval(role: Role) {
  return request<Record<string, unknown>>("/v1/eval/run?suite=regression", role, { method: "POST" });
}

export function fetchLatestEval(role: Role) {
  return request<Record<string, unknown>>("/v1/eval/latest", role);
}

export function fetchCorpus(role: Role) {
  return request<{ chunks: number; tickers: Record<string, number> }>("/v1/corpus", role);
}
