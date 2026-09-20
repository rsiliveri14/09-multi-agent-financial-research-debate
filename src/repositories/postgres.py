from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from db.models import EvaluationResult, ResearchRun, RunEventRow
from domain.enums import RunStatus, TerminalState
from domain.errors import DatabaseFailureError
from domain.models import DebateResult, DebateRunRecord, RunEvent
from repositories.protocol import RunRepository


class PostgresRunRepository(RunRepository):
    def __init__(self, factory: async_sessionmaker[AsyncSession]) -> None:
        self.factory = factory

    async def save(self, record: DebateRunRecord) -> DebateRunRecord:
        try:
            async with self.factory() as session:
                existing = await session.scalar(select(ResearchRun).where(ResearchRun.request_id == record.request_id))
                payload = record.result.model_dump(mode="json") if record.result else {}
                if existing is None:
                    row = ResearchRun(
                        id=record.id,
                        request_id=record.request_id,
                        question=record.question,
                        status=record.status.value,
                        terminal_state=record.terminal_state.value,
                        model_provider=record.model_provider,
                        model_name=record.model_name,
                        latency_ms=record.latency_ms,
                        estimated_cost_usd=record.estimated_cost_usd,
                        error=record.error,
                        result_json=payload,
                        created_at=record.created_at,
                        completed_at=record.completed_at,
                    )
                    session.add(row)
                    for event in record.events:
                        session.add(
                            RunEventRow(
                                run_id=record.id,
                                seq=event.seq,
                                event_type=event.event_type,
                                node=event.node,
                                payload=event.payload,
                                created_at=event.created_at,
                            )
                        )
                else:
                    existing.status = record.status.value
                    existing.terminal_state = record.terminal_state.value
                    existing.result_json = payload
                    existing.latency_ms = record.latency_ms
                    existing.estimated_cost_usd = record.estimated_cost_usd
                    existing.error = record.error
                    existing.completed_at = record.completed_at
                await session.commit()
            return record
        except Exception as exc:
            raise DatabaseFailureError() from exc

    async def get(self, request_id: str) -> DebateRunRecord | None:
        try:
            async with self.factory() as session:
                row = await session.scalar(
                    select(ResearchRun)
                    .options(selectinload(ResearchRun.events))
                    .where(ResearchRun.request_id == request_id)
                )
                if row is None:
                    return None
                return _to_record(row)
        except Exception as exc:
            raise DatabaseFailureError() from exc

    async def list(self, limit: int = 50) -> list[DebateRunRecord]:
        try:
            async with self.factory() as session:
                rows = (
                    await session.scalars(
                        select(ResearchRun)
                        .options(selectinload(ResearchRun.events))
                        .order_by(ResearchRun.created_at.desc())
                        .limit(limit)
                    )
                ).all()
                return [_to_record(row) for row in rows]
        except Exception as exc:
            raise DatabaseFailureError() from exc

    async def save_eval(self, suite: str, report: dict[str, Any]) -> None:
        try:
            async with self.factory() as session:
                session.add(EvaluationResult(suite=suite, report=report))
                await session.commit()
        except Exception as exc:
            raise DatabaseFailureError() from exc

    async def latest_eval(self) -> dict[str, Any] | None:
        try:
            async with self.factory() as session:
                row = await session.scalar(
                    select(EvaluationResult).order_by(EvaluationResult.created_at.desc()).limit(1)
                )
                if row is None:
                    return None
                payload = dict(row.report or {})
                payload.setdefault("suite", row.suite)
                return payload
        except Exception as exc:
            raise DatabaseFailureError() from exc


def _to_record(row: ResearchRun) -> DebateRunRecord:
    result = DebateResult.model_validate(row.result_json) if row.result_json else None
    events = [
        RunEvent(
            seq=event.seq,
            event_type=event.event_type,
            node=event.node,
            payload=event.payload,
            created_at=event.created_at,
        )
        for event in (row.events or [])
    ]
    return DebateRunRecord(
        id=row.id,
        request_id=row.request_id,
        question=row.question,
        status=RunStatus(row.status),
        terminal_state=TerminalState(row.terminal_state),
        result=result,
        events=events,
        created_at=row.created_at,
        completed_at=row.completed_at,
        latency_ms=row.latency_ms,
        estimated_cost_usd=row.estimated_cost_usd,
        model_provider=row.model_provider,
        model_name=row.model_name,
        error=row.error,
    )
