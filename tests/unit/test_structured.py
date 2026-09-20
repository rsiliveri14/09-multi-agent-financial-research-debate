from pydantic import BaseModel

from models.structured import bounded_repair, parse_structured


class Sample(BaseModel):
    headline: str
    confidence: float = 0.0


def test_parse_structured_ok():
    model = parse_structured(Sample, {"headline": "ok", "confidence": 0.2})
    assert model.headline == "ok"


def test_bounded_repair_fills_defaults():
    model = bounded_repair(Sample, {})
    assert model.headline == ""
    assert model.confidence == 0.0
