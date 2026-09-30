from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        self.headers = headers
        super().__init__(message)


def error_body(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body(exc.code, exc.message),
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        message = "Request validation failed."
        errors: list[dict[str, Any]] = exc.errors()
        if errors:
            message = str(errors[0].get("msg", message)).removeprefix("Value error, ")
        return JSONResponse(
            status_code=400,
            content=error_body("VALIDATION_ERROR", message),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        codes = {
            400: "VALIDATION_ERROR",
            401: "UNAUTHENTICATED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            409: "CONFLICT",
        }
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body(
                codes.get(exc.status_code, "HTTP_ERROR"),
                str(exc.detail),
            ),
            headers=exc.headers,
        )

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(_: Request, __: IntegrityError) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content=error_body("CONFLICT", "The requested change conflicts with existing data."),
        )
