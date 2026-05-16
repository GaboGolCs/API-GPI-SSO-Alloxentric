from datetime import datetime, timedelta, timezone
import jwt
from passlib.context import CryptContext
from app.config import settings
from app.repositories.user_api_repo import UserApiRepository
from app.schemas.auth import LoginRequest, TokenResponse
from app.exceptions import InvalidCredentialsError, TokenExpiredError, TokenInvalidError

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(self, repo: UserApiRepository):
        self.repo = repo

    def generate_jwt(self, payload: dict, expires_delta: timedelta) -> str:
        to_encode = payload.copy()
        expire = datetime.now(timezone.utc) + expires_delta
        to_encode.update({"exp": expire})
        return jwt.encode(
            to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
        )

    async def login(self, login_in: LoginRequest) -> TokenResponse:
        # 1. Solicitar el usuario al repositorio remoto
        user = await self.repo.get_user_for_auth(login_in.client_id, login_in.email)

        # ✨ LA SOLUCIÓN: Validar si el usuario existe ANTES de leer sus datos
        if not user:
            raise InvalidCredentialsError()

        # 2. Verificar si la contraseña coincide con el hash
        if not pwd_context.verify(login_in.password, user["hashed_password"]):
            raise InvalidCredentialsError()

        # 3. Preparar los payloads de los tokens
        access_payload = {
            "sub": user["user_id"],
            "client_id": user["client_id"],
            "role": user["role"],
        }
        refresh_payload = {"sub": user["user_id"], "type": "refresh"}

        # 4. Generar tokens
        access_token = self.generate_jwt(
            access_payload, timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        refresh_token = self.generate_jwt(
            refresh_payload, timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user_id=user["user_id"],
            role=user["role"],
        )

    def verify_token(self, token: str, check_refresh: bool = False) -> dict:
        try:
            payload = jwt.decode(
                token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
            )
            if check_refresh and payload.get("type") != "refresh":
                raise TokenInvalidError()
            return payload
        except jwt.ExpiredSignatureError:
            raise TokenExpiredError()
        except jwt.PyJWTError:
            raise TokenInvalidError()
