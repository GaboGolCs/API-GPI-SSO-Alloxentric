from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class WorkerServiceError(Exception):
    """Base error for the workers service."""

    def __init__(self, message: str, status_code: int = 500) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(WorkerServiceError):
    def __init__(self, resource: str, resource_id: str) -> None:
        super().__init__(f"{resource} '{resource_id}' not found.", status_code=404)


class ForbiddenError(WorkerServiceError):
    def __init__(self, detail: str = "Access forbidden.") -> None:
        super().__init__(detail, status_code=403)


class ConflictError(WorkerServiceError):
    def __init__(self, detail: str) -> None:
        super().__init__(detail, status_code=409)


class UnprocessableError(WorkerServiceError):
    def __init__(self, detail: str) -> None:
        super().__init__(detail, status_code=422)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(WorkerServiceError)
    async def worker_service_error_handler(
        request: Request, exc: WorkerServiceError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message},
        )
