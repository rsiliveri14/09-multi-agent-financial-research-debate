"""Index the frozen Project-2-style sample corpus (already loaded at runtime)."""

from __future__ import annotations

import asyncio

from data.corpus import load_sample_corpus
from services.chunking import chunk_documents
from services.runtime import build_runtime


async def main() -> None:
    runtime = await build_runtime()
    docs = load_sample_corpus()
    chunks = chunk_documents(docs)
    print(f"corpus documents={len(docs)} chunks={len(chunks)} store={runtime.settings.store_backend}")


if __name__ == "__main__":
    asyncio.run(main())
