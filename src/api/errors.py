from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from api.envelope import fail
from domain.errors import AppError


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", "req_unknown")
        return JSONResponse(
            status_code=exc.http_status,
            content=fail(request_id, exc.code, exc.message, details=exc.details),
        )

    @app.exception_handler(RequestValidationError)
    async def request_validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", "req_unknown")
        return JSONResponse(
            status_code=422,
            content=fail(request_id, "VALIDATION_ERROR", "Request validation failed", details={"errors": exc.errors()}),
        )

    @app.exception_handler(ValidationError)
    async def validation_handler(request: Request, exc: ValidationError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", "req_unknown")
        return JSONResponse(
            status_code=422,
            content=fail(request_id, "VALIDATION_ERROR", "Request validation failed", details={"errors": exc.errors()}),
        )
