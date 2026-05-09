from google.cloud.firestore import AsyncClient
from typing import Optional, Dict, Any, List


class UserRepository:
    def __init__(self, db: AsyncClient):
        self.db = db

    async def get_all(self, client_id: str) -> List[Dict[str, Any]]:

        users_ref = (
            self.db.collection("clients").document(client_id).collection("users")
        )
        users_list = []
        async for doc in users_ref.stream():
            users_list.append(doc.to_dict())
        return users_list

    async def create(
        self, client_id: str, user_id: str, user_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        doc_ref = (
            self.db.collection("clients")
            .document(client_id)
            .collection("users")
            .document(user_id)
        )
        await doc_ref.set(user_data)
        return user_data

    async def get(self, client_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        doc_ref = (
            self.db.collection("clients")
            .document(client_id)
            .collection("users")
            .document(user_id)
        )
        doc = await doc_ref.get()
        return doc.to_dict() if doc.exists else None

    async def get_by_email(
        self, client_id: str, email: str
    ) -> Optional[Dict[str, Any]]:
        users_ref = (
            self.db.collection("clients").document(client_id).collection("users")
        )
        query = users_ref.where("email", "==", email).limit(1)
        async for doc in query.stream():
            return doc.to_dict()
        return None

    async def update(
        self, client_id: str, user_id: str, update_data: Dict[str, Any]
    ) -> None:
        doc_ref = (
            self.db.collection("clients")
            .document(client_id)
            .collection("users")
            .document(user_id)
        )
        await doc_ref.update(update_data)

    async def delete(self, client_id: str, user_id: str) -> None:
        doc_ref = (
            self.db.collection("clients")
            .document(client_id)
            .collection("users")
            .document(user_id)
        )
        await doc_ref.delete()
