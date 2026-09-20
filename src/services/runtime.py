from __future__ import annotations

from dataclasses import dataclass, field

from config.settings import Settings, get_settings
from data.corpus import load_sample_corpus
from domain.models import Chunk
from models.embeddings import build_embedder
from models.llm import build_llm
from models.reranker import build_reranker
from observability.logging import configure_logging, get_logger
from observability.tracing import configure_tracing
from repositories.memory import MemoryRunRepository
from repositories.protocol import RunRepository
from services.cache import StatusCache
from services.chunking import chunk_documents
from services.debate import DebateOrchestrator
from services.retrieval import HybridRetriever
from tools.router import ToolRouter

logger = get_logger(__name__)


@dataclass
class AppRuntime:
    settings: Settings
    retriever: HybridRetriever
    tools: ToolRouter
    orchestrator: DebateOrchestrator
    repository: RunRepository
    chunks: list[Chunk]
    failure_flags: dict[str, bool] = field(default_factory=dict)
    ready: bool = False
    last_eval: dict | None = None
    status_cache: StatusCache | None = None


_RUNTIME: AppRuntime | None = None


async def build_runtime(settings: Settings | None = None) -> AppRuntime:
    settings = settings or get_settings()
    configure_logging(settings.log_level)
    configure_tracing(settings)
    embedder = build_embedder(settings)
    reranker = build_reranker(settings)
    retriever = HybridRetriever(embedder, reranker, settings)
    documents = load_sample_corpus()
    chunks = chunk_documents(documents)
    vectors = await embedder.embed([chunk.text for chunk in chunks])
    for chunk, vector in zip(chunks, vectors, strict=True):
        chunk.embedding = vector
    retriever.index(chunks)
    tools = ToolRouter(retriever, timeout_seconds=settings.tool_timeout_seconds)
    llm = build_llm(settings)
    flags: dict[str, bool] = {}
    orchestrator = DebateOrchestrator(settings, tools, llm, failure_flags=flags)
    repository: RunRepository
    if settings.store_backend == "postgres":
        from db.session import create_engine, session_factory
        from repositories.postgres import PostgresRunRepository

        engine = create_engine(settings)
        factory = session_factory(engine)
        repository = PostgresRunRepository(factory)
    else:
        repository = MemoryRunRepository()
    cache = StatusCache(settings.redis_url)
    await cache.connect()
    runtime = AppRuntime(
        settings=settings,
        retriever=retriever,
        tools=tools,
        orchestrator=orchestrator,
        repository=repository,
        chunks=chunks,
        failure_flags=flags,
        ready=True,
        status_cache=cache,
    )
    logger.info(
        "runtime_ready",
        chunks=len(chunks),
        store=settings.store_backend,
        llm=llm.name,
        redis=cache.available,
    )
    return runtime


def get_runtime() -> AppRuntime:
    if _RUNTIME is None:
        raise RuntimeError("runtime is not initialized")
    return _RUNTIME


def set_runtime(runtime: AppRuntime) -> None:
    global _RUNTIME
    _RUNTIME = runtime
