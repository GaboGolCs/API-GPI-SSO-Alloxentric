from google.cloud.firestore import AsyncClient
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class UserRepository:
    def __init__(self, db: AsyncClient):
        self.db = db

    async def get_by_email(self, client_id: str, email: str) -> Optional[Dict[str, Any]]:
        try:
            clean_email = email.strip().lower()
            users_ref = (
                self.db.collection("clients")
                .document(client_id)
                .collection("users")
            )
            query = users_ref.where("email", "==", clean_email).limit(1)
            docs = await query.get()
            if docs:
                user_doc = docs[0]
                user_data = user_doc.to_dict()
                user_data["id"] = user_doc.id
                user_data["user_id"] = user_doc.id
                return user_data
            return None
        except Exception as e:
            logger.error(f"Error crítico consultando Firestore para {email}: {str(e)}")
            raise RuntimeError(f"Error al consultar la base de datos: {str(e)}")

    async def get_all(self, client_id: str) -> list:
        try:
            users_ref = (
                self.db.collection("clients")
                .document(client_id)
                .collection("users")
            )
            docs = await users_ref.get()
            users = []
            for doc in docs:
                data = doc.to_dict()
                if data:
                    data["id"]      = doc.id
                    data["user_id"] = doc.id
                    data.pop("hashed_password", None)
                    users.append(data)
            return users
        except Exception as e:
            logger.error(f"Error obteniendo usuarios: {str(e)}")
            raise RuntimeError(f"Error al obtener usuarios: {str(e)}")

    async def get(self, client_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        try:
            doc_ref = (
                self.db.collection("clients")
                .document(client_id)
                .collection("users")
                .document(user_id)
            )
            doc = await doc_ref.get()
            if doc.exists:
                data = doc.to_dict()
                data["id"] = doc.id
                data["user_id"] = doc.id
                return data
            return None
        except Exception as e:
            logger.error(f"Error obteniendo usuario {user_id}: {str(e)}")
            raise RuntimeError(f"Error al obtener usuario: {str(e)}")

    async def create(self, client_id: str, user_id: str, user_data: dict) -> dict:
        try:
            doc_ref = (
                self.db.collection("clients")
                .document(client_id)
                .collection("users")
                .document(user_id)
            )
            await doc_ref.set(user_data)
            result = user_data.copy()
            result.pop("hashed_password", None)
            return result
        except Exception as e:
            logger.error(f"Error creando usuario: {str(e)}")
            raise RuntimeError(f"Error al crear usuario: {str(e)}")

    async def update(self, client_id: str, user_id: str, update_data: dict) -> None:
        try:
            doc_ref = (
                self.db.collection("clients")
                .document(client_id)
                .collection("users")
                .document(user_id)
            )
            await doc_ref.update(update_data)
        except Exception as e:
            logger.error(f"Error actualizando usuario {user_id}: {str(e)}")
            raise RuntimeError(f"Error al actualizar usuario: {str(e)}")

    async def delete(self, client_id: str, user_id: str) -> None:
        try:
            doc_ref = (
                self.db.collection("clients")
                .document(client_id)
                .collection("users")
                .document(user_id)
            )
            await doc_ref.delete()
        except Exception as e:
            logger.error(f"Error eliminando usuario {user_id}: {str(e)}")
            raise RuntimeError(f"Error al eliminar usuario: {str(e)}")