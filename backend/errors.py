from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def _trace_id(request: Request) -> str:
    return getattr(request.state, "request_id", str(uuid4()))


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        if isinstance(exc.detail, dict):
            error_code = str(exc.detail.get("code", "HTTP_ERROR"))
            error_message = str(exc.detail.get("message", "HTTP error"))
        else:
            error_code = "HTTP_ERROR"
            error_message = str(exc.detail)

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "error",
                "trace_id": _trace_id(request),
                "data": {},
                "errors": [{"code": error_code, "message": error_message}],
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "status": "error",
                "trace_id": _trace_id(request),
                "data": {},
                "errors": [{"code": "VALIDATION_ERROR", "message": str(exc)}],
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "trace_id": _trace_id(request),
                "data": {},
                "errors": [{"code": "INTERNAL_ERROR", "message": str(exc)}],
            },
        )
