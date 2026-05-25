from ulid import ULID
from passlib.context import CryptContext
from app.repositories.user_repo import UserRepository
from app.schemas.user import UserCreate, UserUpdate
from app.exceptions import (
    UserNotFoundError,
    UserAlreadyExistsError,
    DatabaseOperationError,
)

# Configurador de encriptación
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    async def get_all_users(self, client_id: str) -> list:
        try:
            return await self.repo.get_all(client_id)
        except Exception as e:
            raise DatabaseOperationError(
                detail=str(e) + " No se han podido obtener los usuarios."
            )

    async def get_user(self, client_id: str, user_id: str) -> dict:
        user = await self.repo.get(client_id, user_id)
        if not user:
            raise UserNotFoundError()
        return user

    async def create_user(self, client_id: str, user_in: UserCreate, user_id: str = None) -> dict:
        existing_user = await self.repo.get_by_email(client_id, user_in.email)
        if existing_user:
            raise UserAlreadyExistsError()

        # Si no nos pasan un ID (por ejemplo, creación directa), generamos el ULID clásico
        if not user_id:
            user_id = f"usr_{str(ULID())}"
            
        user_data = user_in.model_dump()

        # 1. Extraer la contraseña en texto plano
        plain_password = user_data.pop("password")
        
        # 2. Encriptarla y guardarla como hashed_password usando tu pwd_context
        user_data["hashed_password"] = pwd_context.hash(plain_password)

        user_data["user_id"] = user_id
        user_data["client_id"] = client_id
        user_data["status"] = "active"

        try:
            return await self.repo.create(client_id, user_id, user_data)

        except Exception as e:
            raise DatabaseOperationError(
                detail=str(e) + " No se ha podido crear el usuario."
            )

    async def update_user(
        self, client_id: str, user_id: str, user_in: UserUpdate
    ) -> dict:
        # Validar existencia
        await self.get_user(client_id, user_id)

        update_data = user_in.model_dump(exclude_unset=True)

        # Si se envió una nueva contraseña, la encriptamos antes de guardar
        if "password" in update_data:
            plain_password = update_data.pop("password")
            update_data["hashed_password"] = pwd_context.hash(plain_password)

        try:
            if update_data:
                await self.repo.update(client_id, user_id, update_data)
        except Exception as e:
            raise DatabaseOperationError(
                detail=str(e) + " No se han podido actualizar el usuario."
            )

        return await self.get_user(client_id, user_id)

    # Eliminamos un user
    async def delete_user(self, client_id: str, user_id: str) -> None:
        # 1. Validar existencia. Si no existe, get_user lanzará UserNotFoundError.
        # No usamos try/except aquí. Dejamos que el error "pase de largo" hacia FastAPI.
        await self.get_user(client_id, user_id)

        # 2. Intentar borrar
        try:
            await self.repo.delete(client_id, user_id)
        except Exception as e:
            raise DatabaseOperationError(
                detail=str(e) + " No se han podido eliminar el usuario."
            )
