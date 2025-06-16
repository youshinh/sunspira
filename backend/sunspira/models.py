from beanie import Document, Link, PydanticObjectId # PydanticObjectId をインポート
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime
import uuid

# Linkを使用するために、将来作成するモデルを先行宣言
class User(Document):
    pass

class Conversation(Document):
    pass

class Agent(Document):
    pass

# --- User Model ---
class User(Document):
    email: EmailStr
    hashed_password: str
    is_active: bool = True
    is_superuser: bool = False
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

    class Settings:
        name = "users"

# --- Agent Models ---
class LinxProfile(BaseModel):
    creativity_score: float = 0.5
    risk_aversion_score: float = 0.5
    verbosity_score: float = 0.5
    learning_rate: float = 0.1
    mastered_skills: List[str] = []

class LinxLineage(BaseModel):
    parent1_id: Optional[str] = None
    parent2_id: Optional[str] = None

class Agent(Document):
    agent_id: str = f"agent-{uuid.uuid4()}"
    owner: Link[User]
    agent_type: str = "PERSONAL"
    description: str
    system_prompt: str
    linx_profile: LinxProfile = LinxProfile()
    linx_lineage: Optional[LinxLineage] = None
    status: str = "ACTIVE"

    class Settings:
        name = "agents"

# --- Conversation Models ---
class Sender(BaseModel):
    sender_type: str
    sender_id: str

class Message(Document):
    # ↓↓↓↓ ここの行を書き換えます ↓↓↓↓
    # conversation: Link[Conversation]  <- この行をコメントアウトまたは削除
    conversation_id: PydanticObjectId   # <- この行を追加
    
    sender: Sender
    content: str
    timestamp: datetime = datetime.now()

    class Settings:
        name = "messages"

class Conversation(Document):
    owner: Link[User]
    agent: Link[Agent]
    summary: Optional[str] = None
    created_at: datetime = datetime.now()

    class Settings:
        name = "conversations"

# 全てのモデル定義が終わった後に、モデルの参照を再構築する
User.model_rebuild()
Agent.model_rebuild()
Conversation.model_rebuild()
Message.model_rebuild()