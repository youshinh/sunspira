from pydantic import BaseModel, EmailStr
from beanie import PydanticObjectId
from datetime import datetime

# --- User Schemas ---

# ユーザー登録時にAPIが受け取るデータの形
class UserCreate(BaseModel):
    email: EmailStr
    password: str

# APIがユーザー情報を返す際のデータの形（パスワードは含めない）
class UserRead(BaseModel):
    id: PydanticObjectId
    email: EmailStr
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True # ORMモデルからPydanticモデルへ変換できるようにする