from __future__ import annotations

import hashlib
from uuid import uuid4

from domain.models import Chunk, Document


def chunk_documents(documents: list[Document]) -> list[Chunk]:
    """Section-aware chunking: one chunk per filing page/section."""
    chunks: list[Chunk] = []
    for document in documents:
        offset = 0
        for index, page in enumerate(document.pages):
            text = page.text.strip()
            token_count = max(1, len(text.split()))
            digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
            chunks.append(
                Chunk(
                    id=uuid4(),
                    document_id=document.id,
                    issuer_ticker=document.issuer.ticker,
                    document_type=document.document_type,
                    reporting_period=document.reporting_period,
                    publication_date=document.publication_date,
                    chunk_index=index,
                    text=text,
                    page=page.page,
                    section=page.section,
                    start_char=offset,
                    end_char=offset + len(text),
                    token_count=token_count,
                    source_url=document.source_url,
                    content_hash=digest,
                    metadata={
                        "title": document.title,
                        "issuer_name": document.issuer.name,
                        "cik": document.issuer.cik,
                    },
                )
            )
            offset += len(text) + 2
    return chunks


def publication_rank(document_type: str) -> int:
    ranking = {"10-K": 3, "10-Q": 3, "8-K": 1}
    return ranking.get(document_type, 0)
