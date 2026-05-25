from fastapi import HTTPException


class NotFoundError(HTTPException):
    def __init__(self, detail: str = "Recurso no encontrado"):
        super().__init__(status_code=404, detail=detail)


class UnauthorizedError(HTTPException):
    def __init__(self, detail: str = "No autenticado"):
        super().__init__(status_code=401, detail=detail)


class ForbiddenError(HTTPException):
    def __init__(self, detail: str = "No autorizado"):
        super().__init__(status_code=403, detail=detail)


class DatabaseOperationError(HTTPException):
    def __init__(self, detail: str = "Error en la base de datos"):
        super().__init__(status_code=500, detail=detail)
