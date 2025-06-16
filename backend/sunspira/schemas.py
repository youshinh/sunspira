from pydantic import BaseModel, EmailStr
from beanie import PydanticObjectId
from datetime import datetime

# --- User Schemas ---
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

class Token(BaseModel):
    access_token: str
    token_type: str

# --- Conversation Schemas ---
class ConversationRead(BaseModel):
    id: PydanticObjectId
    owner_id: PydanticObjectId
    agent_id: str
    created_at: datetime

    class Config:
        from_attributes = True

# --- Message Schemas ---
class MessageCreate(BaseModel):
    content: str

class MessageRead(BaseModel):
    id: PydanticObjectId
    conversation_id: PydanticObjectId
    sender_type: str
    sender_id: str
    content: str
    timestamp: datetime

    class Config:
        from_attributes = True