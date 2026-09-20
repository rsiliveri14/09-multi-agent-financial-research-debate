"""End-to-end debate workflow. Deterministic core with optional LLM provider."""

from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any

from agents.policy import ExecutionPolicy
from config.settings import Settings
from domain.enums import AgentRole, AgreementStatus, RunStatus, TerminalState
from domain.errors import AppError, InsufficientEvidenceError, LoopDetectedError, ToolFailureError
from domain.models import (
    DebateMetrics,
    DebateRequest,
    DebateResult,
    DebateRunRecord,
    RunEvent,
    SpecialistBrief,
)
from models.llm import LLMProvider
from observability.logging import get_logger
from observability.metrics import debate_runs, observe_debate
from observability.tracing import traced
from services.claims import normalize_claims, specialist_diversity
from services.critic import critique
from services.disagreement import build_disagreement, contradiction_count
from services.facts import extract_facts
from services.planner import plan_research
from services.provenance import build_graph
from services.resolution import resolve_conflicts
from services.single_agent import run_single_agent
from services.specialists import SPECIALISTS
from services.synthesis import synthesize
from services.validator import apply_validations, unsupported_rate, validate_claims
from tools.contracts import RetrieveInput
from tools.router import ToolRouter

logger = get_logger(__name__)

FailureFlags = dict[str, bool]


class DebateOrchestrator:
    def __init__(
        self,
        settings: Settings,
        tools: ToolRouter,
        llm: LLMProvider,
        failure_flags: FailureFlags | None = None,
    ) -> None:
        self.settings = settings
        self.tools = tools
        self.llm = llm
        self.failure_flags = failure_flags or {}

    async def run(self, request: DebateRequest, *, request_id: str | None = None) -> DebateResult:
        request_id = request_id or f"req_{uuid.uuid4().hex[:12]}"
        started = time.perf_counter()
        policy = ExecutionPolicy(self.settings, max_rounds=request.max_debate_rounds)
        events: list[RunEvent] = []
        errors: list[str] = []
        seq = 0

        def emit(event_type: str, node: str, payload: dict[str, Any] | None = None) -> None:
            nonlocal seq
            seq += 1
            events.append(RunEvent(seq=seq, event_type=event_type, node=node, payload=payload or {}))

        with traced("debate.run", request_id=request_id):
            try:
                policy.check()
                emit("started", "ingest", {"question": request.question[:200]})
                if self.failure_flags.get("provider_timeout"):
                    await asyncio.sleep(0)
                    from domain.errors import ProviderTimeoutError

                    raise ProviderTimeoutError()
                if self.failure_flags.get("invalid_structured_output"):
                    from domain.errors import ValidationAppError

                    raise ValidationAppError("forced invalid structured output")

                plan = plan_research(request)
                emit("plan", "plan", {"type": plan.question_type.value, "tickers": plan.tickers})
                policy.check()

                retrieval_started = time.perf_counter()
                evidence: dict[str, list] = {}
                retrieval_ms = 0
                tool_calls = 0
                queries_seen: set[str] = set()
                redundant = 0
                mode = request.retrieval_mode
                if self.failure_flags.get("tool_timeout"):
                    raise ToolFailureError("forced tool timeout")
                if self.failure_flags.get("empty_retrieval"):
                    evidence = {role: [] for role in SPECIALISTS}
                else:
                    for role in list(SPECIALISTS) + [AgentRole.SINGLE_AGENT]:
                        query = plan.agent_queries.get(role.value, request.question)
                        if query in queries_seen:
                            redundant += 1
                        queries_seen.add(query)
                        payload = RetrieveInput(
                            query=query,
                            issuer_tickers=plan.tickers or request.issuer_tickers,
                            document_types=[item.value for item in request.document_types],
                            as_of=request.as_of_date,
                            top_k=self.settings.rerank_top_k,
                            mode=mode,
                        )
                        with traced("tool.retrieve", role=role.value):
                            output = await self.tools.retrieve_filings(role, payload)
                        evidence[role.value] = output.hits
                        retrieval_ms += output.latency_ms
                        tool_calls += 1
                        emit(
                            "retrieve",
                            "retrieve",
                            {"role": role.value, "hits": len(output.hits), "latency_ms": output.latency_ms},
                        )
                retrieval_elapsed = int((time.perf_counter() - retrieval_started) * 1000)
                policy.check()

                specialist_started = time.perf_counter()
                briefs: list[SpecialistBrief] = []
                for role, runner in SPECIALISTS.items():
                    hits = evidence.get(role.value, [])
                    facts = extract_facts(hits)
                    brief = runner(hits, facts)
                    brief.latency_ms = int((time.perf_counter() - specialist_started) * 1000)
                    brief.token_input = sum(hit.chunk.token_count for hit in hits)
                    brief.token_output = max(
                        1, len(brief.summary.split()) + sum(len(claim.text.split()) for claim in brief.claims)
                    )
                    brief.estimated_cost_usd = (
                        brief.token_input * self.settings.input_token_usd
                        + brief.token_output * self.settings.output_token_usd
                    )
                    briefs.append(brief)
                    emit(
                        "specialist",
                        "specialists",
                        {"role": role.value, "claims": len(brief.claims), "stance": brief.stance.value},
                    )
                    policy.check(tokens=brief.token_input + brief.token_output)
                specialist_ms = int((time.perf_counter() - specialist_started) * 1000)

                claims = normalize_claims(briefs)
                emit("normalize", "normalize", {"claims": len(claims)})
                cells = build_disagreement(claims)
                unresolved = [cell.topic_key for cell in cells if cell.status == AgreementStatus.DISAGREE]
                emit(
                    "disagreement", "disagreement", {"cells": len(cells), "contradictions": contradiction_count(cells)}
                )
                findings = critique(claims, briefs, cells)
                emit("critic", "critic", {"findings": len(findings)})
                validations = validate_claims(claims)
                claims = apply_validations(claims, validations)
                emit("validate", "validate", {"unsupported_rate": unsupported_rate(claims)})

                resolved: list[str] = []
                if unresolved and policy.can_debate_again():
                    policy.rounds += 1
                    claims, resolved, unresolved = resolve_conflicts(claims, cells)
                    cells = build_disagreement(claims)
                    emit("resolve", "resolve", {"resolved": resolved, "unresolved": unresolved})
                    policy.check()

                report = synthesize(request.question, claims, cells, findings, briefs, unresolved)
                graph = build_graph(briefs, claims, cells, report)
                emit("synthesize", "synthesize", {"outcome": report.outcome.value})

                single = None
                if request.include_single_agent:
                    single_hits = evidence.get(AgentRole.SINGLE_AGENT.value, [])
                    single = run_single_agent(request.question, single_hits)
                    emit("baseline", "single_agent", {"abstained": single.abstained})

                elapsed_ms = int((time.perf_counter() - started) * 1000)
                token_in = sum(brief.token_input for brief in briefs)
                token_out = sum(brief.token_output for brief in briefs)
                cost = sum(brief.estimated_cost_usd for brief in briefs)
                metrics = DebateMetrics(
                    latency_ms=elapsed_ms,
                    retrieval_latency_ms=retrieval_elapsed or retrieval_ms,
                    specialist_latency_ms=specialist_ms,
                    token_input=token_in,
                    token_output=token_out,
                    estimated_cost_usd=round(cost, 8),
                    specialist_diversity=round(specialist_diversity(briefs), 3),
                    unsupported_claim_rate=round(unsupported_rate(claims), 3),
                    contradiction_count=contradiction_count(cells),
                    redundant_tool_calls=redundant,
                    debate_rounds=policy.rounds,
                )
                status = RunStatus.COMPLETED
                if report.outcome == TerminalState.INSUFFICIENT_EVIDENCE:
                    status = RunStatus.PARTIAL
                elif report.outcome == TerminalState.UNRESOLVED:
                    status = RunStatus.COMPLETED
                observe_debate(status.value, elapsed_ms, cost)
                debate_runs.labels(status=status.value).inc()
                result = DebateResult(
                    request_id=request_id,
                    status=status,
                    question=request.question,
                    plan=plan,
                    briefs=briefs,
                    claims=claims,
                    disagreement=cells,
                    critic_findings=findings,
                    validations=validations,
                    synthesis=report,
                    graph=graph,
                    single_agent=single,
                    metrics=metrics,
                    model_provider=self.llm.name,
                    model_name=self.llm.model,
                    terminal_state=report.outcome,
                    errors=errors,
                )
                result._events = events  # type: ignore[attr-defined]
                return result
            except LoopDetectedError as exc:
                errors.append(str(exc))
                return self._failed(request, request_id, started, TerminalState.LOOP_DETECTED, errors, events)
            except InsufficientEvidenceError as exc:
                errors.append(str(exc))
                return self._failed(request, request_id, started, TerminalState.INSUFFICIENT_EVIDENCE, errors, events)
            except AppError as exc:
                errors.append(exc.message)
                mapping = {
                    "provider_timeout": TerminalState.PROVIDER_TIMEOUT,
                    "tool_failure": TerminalState.TOOL_FAILURE,
                    "database_failure": TerminalState.DATABASE_FAILURE,
                    "validation_failure": TerminalState.VALIDATION_FAILED,
                }
                terminal = mapping.get(exc.category.value, TerminalState.CANCELLED)
                logger.warning("debate_failed", request_id=request_id, code=exc.code)
                return self._failed(request, request_id, started, terminal, errors, events, status=RunStatus.FAILED)

    def _failed(
        self,
        request: DebateRequest,
        request_id: str,
        started: float,
        terminal: TerminalState,
        errors: list[str],
        events: list[RunEvent],
        status: RunStatus = RunStatus.FAILED,
    ) -> DebateResult:
        from domain.models import ProvenanceGraph, SynthesisReport
        from services.planner import plan_research

        plan = plan_research(request)
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        report = SynthesisReport(
            headline="Debate did not complete",
            executive_summary=errors[0] if errors else terminal.value,
            outcome=terminal,
            confidence=0.0,
        )
        result = DebateResult(
            request_id=request_id,
            status=status,
            question=request.question,
            plan=plan,
            synthesis=report,
            graph=ProvenanceGraph(),
            metrics=DebateMetrics(latency_ms=elapsed_ms),
            model_provider=self.llm.name,
            model_name=self.llm.model,
            terminal_state=terminal,
            errors=errors,
        )
        result._events = events  # type: ignore[attr-defined]
        observe_debate(status.value, elapsed_ms, 0.0)
        debate_runs.labels(status=status.value).inc()
        return result


def to_run_record(result: DebateResult) -> DebateRunRecord:
    events = getattr(result, "_events", [])
    return DebateRunRecord(
        request_id=result.request_id,
        question=result.question,
        status=result.status,
        terminal_state=result.terminal_state,
        result=result,
        events=events,
        latency_ms=result.metrics.latency_ms,
        estimated_cost_usd=result.metrics.estimated_cost_usd,
        model_provider=result.model_provider,
        model_name=result.model_name,
        error=result.errors[0] if result.errors else None,
        completed_at=result.created_at,
    )
