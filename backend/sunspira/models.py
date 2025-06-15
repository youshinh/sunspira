# backend/sunspira/models.py

from beanie import Document, Link
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
    """ユーザー情報を格納するモデル"""
    # Pydantic V2では、idフィールドは自動的に_idにマップされるので明示的な定義は不要
    
    email: EmailStr
    hashed_password: str
    is_active: bool = True
    is_superuser: bool = False
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

    class Settings:
        name = "users" # MongoDB上のコレクション名

# --- Agent Models ---
class LinxProfile(BaseModel):
    """エージェントの個性を定義する「遺伝子」情報"""
    creativity_score: float = 0.5
    risk_aversion_score: float = 0.5
    verbosity_score: float = 0.5
    learning_rate: float = 0.1
    mastered_skills: List[str] = []

class LinxLineage(BaseModel):
    """親エージェントIDを格納する「家系図」情報"""
    parent1_id: Optional[str] = None
    parent2_id: Optional[str] = None

class Agent(Document):
    """AIエージェントの定義を格納するモデル"""
    agent_id: str = f"agent-{uuid.uuid4()}"
    owner: Link[User]
    agent_type: str = "PERSONAL" # PERSONAL, META, SANDBOX
    description: str
    system_prompt: str
    linx_profile: LinxProfile = LinxProfile()
    linx_lineage: Optional[LinxLineage] = None
    status: str = "ACTIVE" # ACTIVE, IN_SANDBOX, RETIRED

    class Settings:
        name = "agents"

# --- Conversation Models ---
class Sender(BaseModel):
    sender_type: str # "USER" or "AGENT"
    sender_id: str

class Message(Document):
    """各メッセージの詳細を格納するモデル"""
    conversation: Link[Conversation]
    sender: Sender
    content: str
    timestamp: datetime = datetime.now()

    class Settings:
        name = "messages"

class Conversation(Document):
    """対話セッション全体を管理するモデル"""
    owner: Link[User]
    agent: Link[Agent]
    summary: Optional[str] = None
    created_at: datetime = datetime.now()

    class Settings:
        name = "conversations"