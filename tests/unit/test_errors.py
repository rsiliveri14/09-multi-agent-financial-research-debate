from pydantic import ValidationError

from domain.errors import AuthenticationError, ValidationAppError
from domain.models import DebateRequest


def test_debate_request_rejects_short_question():
    try:
        DebateRequest(question="hi")
        ok = True
    except ValidationError:
        ok = False
    assert ok is False


def test_error_taxonomy_status_codes():
    err = ValidationAppError("bad")
    assert err.http_status == 422
    assert err.code == "VALIDATION_ERROR"
    auth = AuthenticationError()
    assert auth.http_status == 401
