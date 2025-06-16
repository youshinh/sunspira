from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from beanie import init_beanie, PydanticObjectId
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from typing import Annotated
from contextlib import asynccontextmanager # lifespanのためにインポート

load_dotenv()

# --- モデル、スキーマ、セキュリティ関数のインポート ---
from .models import User, Agent, Conversation, Message
from .schemas import UserCreate, UserRead, Token, ConversationRead, MessageCreate
from .security import get_password_hash, verify_password, create_access_token, get_current_user
from .tasks import process_agent_response_task

# --- lifespanコンテキストマネージャ（新しい初期化方法） ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    アプリケーションの起動と終了時に実行される処理
    """
    # 起動時の処理
    mongodb_connection_string = os.getenv("MONGO_CONNECTION_STRING_SECRET")
    if not mongodb_connection_string:
        raise ValueError("MongoDB connection string not found.")

    client = AsyncIOMotorClient(mongodb_connection_string)
    database = client.get_database("sunspira_db")

    await init_beanie(
        database=database,
        document_models=[
            User,
            Agent,
            Conversation,
            Message
        ]
    )
    print("Database connection and Beanie initialization complete.")
    
    yield # ここでアプリケーションがリクエストの受け付けを開始
    
    # 終了時の処理
    print("Closing database connection.")
    client.close()

# --- FastAPIアプリケーションの初期化 ---
# lifespanをここで適用します
app = FastAPI(
    title="SUNSPIRA Backend API",
    description="The core API for the SUNSPIRA computational life form.",
    version="2.1.0",
    lifespan=lifespan
)

# @app.on_event("startup") と @app.on_event("shutdown") はもう不要なので削除しました


# --- APIエンドポイントの定義 ---

@app.get("/", tags=["Health Check"])
async def root():
    return {"status": "ok", "message": "Welcome to the SUNSPIRA API"}

@app.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED, tags=["Users"])
async def create_user(user_in: UserCreate):
    existing_user = await User.find_one(User.email == user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="このメールアドレスは既に使用されています。",
        )
    hashed_password = get_password_hash(user_in.password)
    new_user = User(email=user_in.email, hashed_password=hashed_password)
    await new_user.insert()
    return new_user

@app.post("/login/token", response_model=Token, tags=["Users"])
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = await User.find_one(User.email == form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="メールアドレスまたはパスワードが正しくありません",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=UserRead, tags=["Users"])
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user

@app.post("/conversations", response_model=ConversationRead, status_code=status.HTTP_201_CREATED, tags=["Conversations"])
async def create_conversation(current_user: Annotated[User, Depends(get_current_user)]):
    agent = await Agent.find_one({"owner.id": current_user.id})
    if not agent:
        agent = Agent(
            owner=current_user,
            description="Default Personal Agent",
            system_prompt="You are a helpful assistant."
        )
        await agent.insert()

    new_conversation = Conversation(owner=current_user, agent=agent)
    await new_conversation.insert()
    
    return ConversationRead(
        id=new_conversation.id,
        owner_id=new_conversation.owner.id,
        agent_id=agent.agent_id,
        created_at=new_conversation.created_at
    )

@app.post("/conversations/{conversation_id}/messages", status_code=status.HTTP_202_ACCEPTED, tags=["Conversations"])
async def create_message_in_conversation(
    conversation_id: PydanticObjectId,
    message_in: MessageCreate,
    current_user: Annotated[User, Depends(get_current_user)]
):
    conversation = await Conversation.find_one(
        Conversation.id == conversation_id,
        Conversation.owner.id == current_user.id,
    )

    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found or access denied")

    # ↓↓↓↓ ここのロジックを修正しました ↓↓↓↓
    user_message = Message(
        conversation_id=conversation.id, # 新しい conversation_id フィールドにIDを直接セット
        sender={"sender_type": "USER", "sender_id": str(current_user.id)},
        content=message_in.content
    )
    await user_message.insert()

    process_agent_response_task.delay(str(user_message.id))

    return {"status": "ok", "message": "Message received. Agent is thinking..."}
@app.delete("/test-async-task", tags=["Tests"])
async def test_async(message: str = "Hello Celery"):
    return {"deprecated": "This endpoint is no longer in use."}