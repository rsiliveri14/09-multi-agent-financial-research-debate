from domain.enums import ErrorCategory


class AppError(Exception):
    """Typed application failure with a stable category and HTTP mapping."""

    def __init__(
        self,
        message: str,
        *,
        category: ErrorCategory,
        http_status: int,
        code: str,
        details: dict | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.category = category
        self.http_status = http_status
        self.code = code
        self.details = details or {}


class ValidationAppError(AppError):
    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(
            message,
            category=ErrorCategory.VALIDATION_FAILURE,
            http_status=422,
            code="VALIDATION_ERROR",
            details=details,
        )


class AuthenticationError(AppError):
    def __init__(self, message: str = "Authentication required") -> None:
        super().__init__(
            message,
            category=ErrorCategory.AUTHENTICATION_FAILURE,
            http_status=401,
            code="AUTHENTICATION_FAILURE",
        )


class AuthorizationError(AppError):
    def __init__(self, message: str = "Forbidden") -> None:
        super().__init__(
            message,
            category=ErrorCategory.AUTHORIZATION_FAILURE,
            http_status=403,
            code="AUTHORIZATION_FAILURE",
        )


class ProviderTimeoutError(AppError):
    def __init__(self, message: str = "Model provider timed out") -> None:
        super().__init__(
            message,
            category=ErrorCategory.PROVIDER_TIMEOUT,
            http_status=504,
            code="PROVIDER_TIMEOUT",
        )


class RateLimitError(AppError):
    def __init__(self, message: str = "Provider rate limit exceeded") -> None:
        super().__init__(
            message,
            category=ErrorCategory.RATE_LIMIT,
            http_status=429,
            code="RATE_LIMIT",
        )


class ProviderOutageError(AppError):
    def __init__(self, message: str = "Model provider unavailable") -> None:
        super().__init__(
            message,
            category=ErrorCategory.PROVIDER_OUTAGE,
            http_status=503,
            code="PROVIDER_OUTAGE",
        )


class ToolFailureError(AppError):
    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(
            message,
            category=ErrorCategory.TOOL_FAILURE,
            http_status=502,
            code="TOOL_FAILURE",
            details=details,
        )


class DatabaseFailureError(AppError):
    def __init__(self, message: str = "Database unavailable") -> None:
        super().__init__(
            message,
            category=ErrorCategory.DATABASE_FAILURE,
            http_status=503,
            code="DATABASE_FAILURE",
        )


class InsufficientEvidenceError(AppError):
    def __init__(self, message: str = "Insufficient evidence to answer") -> None:
        super().__init__(
            message,
            category=ErrorCategory.INSUFFICIENT_EVIDENCE,
            http_status=200,
            code="INSUFFICIENT_EVIDENCE",
        )


class LoopDetectedError(AppError):
    def __init__(self, message: str = "Agent iteration limit reached") -> None:
        super().__init__(
            message,
            category=ErrorCategory.LOOP_DETECTED,
            http_status=409,
            code="LOOP_DETECTED",
        )


class EvaluationFailureError(AppError):
    def __init__(self, message: str = "Evaluation failed") -> None:
        super().__init__(
            message,
            category=ErrorCategory.EVALUATION_FAILURE,
            http_status=500,
            code="EVALUATION_FAILURE",
        )
