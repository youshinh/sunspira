from pydantic import BaseModel, EmailStr
from beanie import PydanticObjectId
from datetime import datetime

# --- User Schemas (既存のコード) ---
class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserRead(BaseModel):
    id: PydanticObjectId
    email: EmailStr
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# --- ここから下を追記：Token Schema ---
class Token(BaseModel):
    access_token: str
    token_type: str