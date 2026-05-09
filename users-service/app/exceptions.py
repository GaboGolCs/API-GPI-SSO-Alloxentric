from fastapi import HTTPException, status


class UserNotFoundError(HTTPException):
    # Agregamos 'detail' como parámetro opcional por si queremos sobrescribir el mensaje por defecto
    def __init__(
        self,
        detail: str = "El usuario especificado no fue encontrado en la base de datos.",
    ):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )


class UserAlreadyExistsError(HTTPException):
    def __init__(
        self,
        detail: str = "Ya existe un usuario registrado con este correo electrónico.",
    ):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
        )


class DatabaseOperationError(HTTPException):
    def __init__(
        self, detail: str = "Ocurrió un error al interactuar con la base de datos."
    ):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail
        )


class DeleteUserError(HTTPException):
    def __init__(self, detail: str = "No ha sido posible eliminar el usuario."):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail
        )
