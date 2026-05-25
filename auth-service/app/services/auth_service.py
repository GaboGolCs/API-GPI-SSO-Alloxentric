from datetime import datetime, timedelta, timezone
import jwt
from passlib.context import CryptContext
from app.config import settings
from app.repositories.user_api_repo import UserApiRepository
from app.schemas.auth import LoginRequest
from app.exceptions import InvalidCredentialsError, TokenExpiredError, TokenInvalidError

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(self, repo: UserApiRepository):
        self.repo = repo

    def generate_jwt(self, payload: dict, expires_delta: timedelta) -> str:
        """
        Genera un token JWT empaquetando el payload y calculando su expiración.
        """
        to_encode = payload.copy()
        expire = datetime.now(timezone.utc) + expires_delta
        to_encode.update({"exp": expire})
        return jwt.encode(
            to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
        )

    async def login_user(self, login_data: LoginRequest) -> dict:
        """
        Busca al usuario en Firestore utilizando el repositorio, valida la contraseña 
        e inyecta el 'role' y 'client_id' requeridos por el ecosistema.
        """
        # 1. Extraemos los campos de las credenciales de forma segura desde el esquema
        client_id = login_data.client_id
        email = login_data.email
        password = login_data.password

        # 2. Buscamos el usuario en Firestore pasando los parámetros limpios
        user_doc = await self.repo.get_user_for_auth(client_id, email)
        
        if not user_doc:
            raise InvalidCredentialsError()

        # 3. Verificamos que la contraseña ingresada coincida con el hash de Firestore
        if not pwd_context.verify(password, user_doc.get("hashed_password")):
            raise InvalidCredentialsError()

        # 4. 🌟 SECCIÓN CRÍTICA: Aquí armamos el Payload inyectando las llaves requeridas
        access_payload = {
            "sub": user_doc.get("user_id"),
            "client_id": user_doc.get("client_id"),
            "role": user_doc.get("role")  # Soluciona el error 403 definitivamente
        }

        # 5. Generamos los tokens de acceso utilizando los settings del sistema
        access_token = self.generate_jwt(
            payload=access_payload, 
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )

        refresh_payload = {
            "sub":       user_doc.get("user_id"),
            "client_id": user_doc.get("client_id"),
            "role":      user_doc.get("role"),
            "type":      "refresh",
        }
        refresh_token = self.generate_jwt(
            payload=refresh_payload,
            expires_delta=timedelta(days=7),
        )

        return {
            "access_token":  access_token,
            "refresh_token": refresh_token,
            "token_type":    "bearer",
            "user_id":       user_doc.get("user_id"),
            "role":          user_doc.get("role"),
        }

    def verify_token(self, token: str, check_refresh: bool = False) -> dict:
        """
        Decodifica y valida las firmas del token JWT.
        """
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