from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class DigitalTwinError(Exception):
    def __init__(self, message: str, status_code: int = 500) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(DigitalTwinError):
    def __init__(self, resource: str, resource_id: str) -> None:
        super().__init__(f"{resource} '{resource_id}' no encontrado.", status_code=404)


class ForbiddenError(DigitalTwinError):
    def __init__(self, detail: str = "Acceso denegado.") -> None:
        super().__init__(detail, status_code=403)


class ConflictError(DigitalTwinError):
    def __init__(self, detail: str) -> None:
        super().__init__(detail, status_code=409)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DigitalTwinError)
    async def digital_twin_error_handler(
        request: Request, exc: DigitalTwinError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message},
        )
