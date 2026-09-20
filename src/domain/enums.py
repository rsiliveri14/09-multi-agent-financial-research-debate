from enum import StrEnum


class DocumentType(StrEnum):
    TEN_K = "10-K"
    TEN_Q = "10-Q"
    EIGHT_K = "8-K"


class QuestionType(StrEnum):
    LOOKUP = "lookup"
    COMPARISON = "comparison"
    MIXED = "mixed"
    CONTRADICTORY = "contradictory"
    TEMPORAL = "temporal"
    UNANSWERABLE = "unanswerable"


class RetrievalMode(StrEnum):
    LEXICAL = "lexical"
    VECTOR = "vector"
    HYBRID = "hybrid"
    HYBRID_RERANK = "hybrid_rerank"


class AgentRole(StrEnum):
    PLANNER = "planner"
    BULL = "bull"
    BEAR = "bear"
    FINANCIAL = "financial"
    RISK = "risk"
    EVIDENCE = "evidence"
    CRITIC = "critic"
    VALIDATOR = "validator"
    SYNTHESIZER = "synthesizer"
    SINGLE_AGENT = "single_agent"


class Polarities(StrEnum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"


class AgreementStatus(StrEnum):
    AGREE = "agree"
    DISAGREE = "disagree"
    PARTIAL = "partial"
    MISSING = "missing"


class RunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class TerminalState(StrEnum):
    COMPLETED = "completed"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    UNRESOLVED = "unresolved"
    LOOP_DETECTED = "loop_detected"
    BUDGET_EXCEEDED = "budget_exceeded"
    VALIDATION_FAILED = "validation_failed"
    PROVIDER_TIMEOUT = "provider_timeout"
    TOOL_FAILURE = "tool_failure"
    DATABASE_FAILURE = "database_failure"
    CANCELLED = "cancelled"


class ErrorCategory(StrEnum):
    VALIDATION_FAILURE = "validation_failure"
    AUTHENTICATION_FAILURE = "authentication_failure"
    AUTHORIZATION_FAILURE = "authorization_failure"
    PROVIDER_TIMEOUT = "provider_timeout"
    RATE_LIMIT = "rate_limit"
    PROVIDER_OUTAGE = "provider_outage"
    TOOL_FAILURE = "tool_failure"
    DATABASE_FAILURE = "database_failure"
    EVALUATION_FAILURE = "evaluation_failure"
    PROGRAMMING_ERROR = "programming_error"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    LOOP_DETECTED = "loop_detected"
    PERMISSION_VIOLATION = "permission_violation"
