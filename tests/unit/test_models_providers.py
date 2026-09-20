from domain.models import Message
from models.embeddings import HashingEmbeddingProvider, cosine_similarity
from models.llm import HeuristicLLMProvider


async def test_hashing_embeddings_are_normalized_and_deterministic():
    embedder = HashingEmbeddingProvider(dim=64)
    left, right, other = await embedder.embed(["Apple net sales 391", "Apple net sales 391", "unrelated zebra"])
    assert abs(sum(x * x for x in left) - 1.0) < 1e-6
    assert left == right
    assert cosine_similarity(left, right) > cosine_similarity(left, other)


async def test_heuristic_llm_returns_usage():
    provider = HeuristicLLMProvider()
    response = await provider.generate([Message(role="user", content="Question: hello")])
    assert response.provider == "heuristic"
    assert response.input_tokens >= 1
    assert response.output_tokens >= 1
    assert response.estimated_cost_usd == 0.0
