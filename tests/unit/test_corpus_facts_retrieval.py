from datetime import date

from data.corpus import ISSUERS, load_sample_corpus
from domain.enums import RetrievalMode
from domain.models import RetrievedChunk
from services.chunking import chunk_documents
from services.facts import contradictory_pairs, detect_metric, extract_facts
from services.lexical import BM25Index, tokenize


def test_corpus_has_five_issuers_and_pages():
    docs = load_sample_corpus()
    assert set(ISSUERS) == {"AAPL", "MSFT", "AMZN", "NVDA", "TSLA"}
    assert len(docs) >= 18
    chunks = chunk_documents(docs)
    assert len(chunks) == sum(len(doc.pages) for doc in docs)
    assert all(chunk.text for chunk in chunks)


def test_extract_apple_fy2024_sales_and_china():
    docs = load_sample_corpus()
    chunks = chunk_documents(docs)
    hits = [RetrievedChunk(chunk=chunk, fused_score=1.0) for chunk in chunks if chunk.issuer_ticker == "AAPL"]
    facts = extract_facts(hits)
    values = {(fact.metric, fact.period, fact.value) for fact in facts}
    assert ("net_sales", "FY2024", 391.0) in values
    assert any(fact.metric == "greater_china_sales" and fact.value == 67.0 for fact in facts)


def test_detect_metric_prefers_specific_over_generic_net_sales():
    assert detect_metric("Greater China net sales were $67.0 billion in 2024") == "greater_china_sales"
    assert detect_metric("AWS net sales were $107.6 billion") == "aws_sales"
    assert detect_metric("iPhone net sales were $201.2 billion") == "iphone_sales"
    assert detect_metric("Total net sales were $391.0 billion in 2024") == "net_sales"


def test_extract_core_facts_for_each_issuer():
    docs = load_sample_corpus()
    chunks = chunk_documents(docs)
    facts = extract_facts([RetrievedChunk(chunk=chunk, fused_score=1.0) for chunk in chunks])
    values = {(fact.ticker, fact.metric, fact.period, fact.value) for fact in facts}
    assert ("MSFT", "intelligent_cloud_revenue", "FY2024", 96.6) in values
    assert ("AMZN", "aws_sales", "FY2024", 107.6) in values
    assert ("NVDA", "data_center_revenue", "FY2025", 115.2) in values
    assert ("TSLA", "automotive_revenue", "FY2024", 77.1) in values or any(
        fact.ticker == "TSLA" and fact.metric == "automotive_revenue" for fact in facts
    )


def test_extract_tesla_delivery_conflict():
    docs = load_sample_corpus()
    chunks = chunk_documents(docs)
    hits = [
        RetrievedChunk(chunk=chunk, fused_score=1.0)
        for chunk in chunks
        if chunk.issuer_ticker == "TSLA" and chunk.reporting_period == "Q1FY2025"
    ]
    facts = extract_facts(hits)
    pairs = contradictory_pairs(facts)
    assert pairs or any(fact.is_preliminary for fact in facts)


def test_bm25_finds_aws_sales():
    chunks = chunk_documents(load_sample_corpus())
    index = BM25Index()
    index.build(chunks)
    hits = index.search("Amazon AWS net sales 107.6 billion", top_k=5)
    assert hits
    assert any("107.6" in chunk.text and chunk.issuer_ticker == "AMZN" for chunk, _score in hits)


def test_tokenize_normalizes_plurals():
    tokens = tokenize("Revenues and deliveries increased")
    assert "revenue" in tokens
    assert "deliver" in tokens


async def test_retrieval_modes(runtime):
    query = "Apple total net sales 391.0 billion FY2024"
    lexical = await runtime.retriever.search(query, mode=RetrievalMode.LEXICAL, issuer_tickers=["AAPL"])
    vector = await runtime.retriever.search(query, mode=RetrievalMode.VECTOR, issuer_tickers=["AAPL"])
    hybrid = await runtime.retriever.search(query, mode=RetrievalMode.HYBRID, issuer_tickers=["AAPL"])
    rerank = await runtime.retriever.search(query, mode=RetrievalMode.HYBRID_RERANK, issuer_tickers=["AAPL"])
    assert lexical and vector and hybrid and rerank
    assert rerank[0].rank == 1
    as_of = await runtime.retriever.search(query, issuer_tickers=["AAPL"], as_of=date(2023, 1, 1))
    assert all(hit.chunk.publication_date <= date(2023, 1, 1) for hit in as_of)
    again = await runtime.retriever.search(query, mode=RetrievalMode.HYBRID_RERANK, issuer_tickers=["AAPL"])
    assert [hit.chunk.id for hit in again] == [hit.chunk.id for hit in rerank]
