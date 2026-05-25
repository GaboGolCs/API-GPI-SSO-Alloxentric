from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, EmailStr
from google.cloud.firestore import AsyncClient
from app.dependencies import get_db
from app.config import settings

async def verify_internal_token(x_internal_token: str = Header(...)):
    if x_internal_token != settings.INTERNAL_API_KEY:
        raise HTTPException(status_code=403, detail="Token interno inválido")

router = APIRouter(
    prefix="/v1/internal",
    tags=["Internal"],
    dependencies=[Depends(verify_internal_token)],
)

class InternalAuthRequest(BaseModel):
    client_id: str
    email: EmailStr

@router.post("/users/by-email")
async def get_user_for_auth(
    payload: InternalAuthRequest,
    db: AsyncClient = Depends(get_db),
):
    ref = db.collection("clients").document(payload.client_id).collection("users")
    query = ref.where("email", "==", payload.email).limit(1)
    async for doc in query.stream():
        return doc.to_dict()
    raise HTTPException(status_code=404, detail="User not found")