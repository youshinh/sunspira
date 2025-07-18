from fastapi import FastAPI, HTTPException, status, Depends, WebSocket, WebSocketDisconnect
from fastapi.security import OAuth2PasswordRequestForm
from beanie import init_beanie, PydanticObjectId
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from typing import Annotated
from contextlib import asynccontextmanager
import uuid
import asyncio
import redis.asyncio as redis # aioredisの代わりにredis.asyncioを直接使う

# --- 他のモジュールからインポート ---
from .models import User, Agent, Conversation, Message
from .schemas import UserCreate, UserRead, Token, ConversationRead, MessageCreate
from .security import get_password_hash, verify_password, create_access_token, get_current_user
from .tasks import process_agent_response_task
from .websocket_manager import ConnectionManager

load_dotenv()

# --- グローバルなインスタンス ---
manager = ConnectionManager()

# --- Redis Pub/Subリスナー（新しいライブラリの作法に修正） ---
async def pubsub_listener():
    redis_url = os.getenv("REDIS_URL")
    r = redis.from_url(redis_url, decode_responses=True)
    async with r.pubsub() as pubsub:
        await pubsub.psubscribe("progress:*")
        print("Redis Pub/Sub listener started using redis-py.")
        while True:
            try:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message:
                    channel = message["channel"]
                    task_id = channel.split(":", 1)[1]
                    data = message["data"]
                    await manager.broadcast_to_task(task_id, data)
            except asyncio.TimeoutError:
                # タイムアウトは正常な動作なので何もしない
                await asyncio.sleep(0.01)
            except Exception as e:
                print(f"Redis listener error: {e}")

# --- lifespanコンテキストマネージャ ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # # 起動時の処理
    # mongodb_connection_string = os.getenv("MONGO_CONNECTION_STRING_SECRET")
    # if not mongodb_connection_string:
    #     raise ValueError("MongoDB connection string not found.")
    
    # client = AsyncIOMotorClient(mongodb_connection_string)
    # database = client.get_database("sunspira_db")
    # await init_beanie(database=database, document_models=[User, Agent, Conversation, Message])
    # print("Database connection and Beanie initialization complete.")

    # listener_task = asyncio.create_task(pubsub_listener())
    
    print("Lifespan startup complete (DB/Redis connection skipped).")
    yield
    
    # # 終了時の処理
    # print("Shutting down...")
    # listener_task.cancel()
    # try:
    #     await listener_task
    # except asyncio.CancelledError:
    #     print("Listener task successfully cancelled.")
    # client.close()
    print("Shutdown complete.")


# --- FastAPIアプリケーションの初期化 ---
app = FastAPI(
    title="SUNSPIRA Backend API",
    description="The core API for the SUNSPIRA computational life form.",
    version="2.1.0",
    lifespan=lifespan
)

# ... (ここから下のAPIエンドポイント部分は一切変更ありません) ...
@app.websocket("/ws/v1/tasks/{task_id}/subscribe")
async def websocket_task_subscribe(websocket: WebSocket, task_id: str):
    await manager.connect(websocket, task_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, task_id)

@app.get("/", tags=["Health Check"])
async def root():
    return {"status": "ok", "message": "Welcome to the SUNSPIRA API"}

@app.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED, tags=["Users"])
async def create_user(user_in: UserCreate):
    existing_user = await User.find_one(User.email == user_in.email)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="このメールアドレスは既に使用されています。")
    hashed_password = get_password_hash(user_in.password)
    new_user = User(email=user_in.email, hashed_password=hashed_password)
    await new_user.insert()
    return new_user

@app.post("/login/token", response_model=Token, tags=["Users"])
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = await User.find_one(User.email == form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="メールアドレスまたはパスワードが正しくありません", headers={"WWW-Authenticate": "Bearer"})
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=UserRead, tags=["Users"])
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user

@app.post("/conversations", response_model=ConversationRead, status_code=status.HTTP_201_CREATED, tags=["Conversations"])
async def create_conversation(current_user: Annotated[User, Depends(get_current_user)]):
    agent = await Agent.find_one({"owner.id": current_user.id})
    if not agent:
        agent = Agent(owner=current_user, description="Default Personal Agent", system_prompt="You are a helpful assistant.")
        await agent.insert()
    new_conversation = Conversation(owner=current_user, agent=agent)
    await new_conversation.insert()
    return ConversationRead(id=new_conversation.id, owner_id=new_conversation.owner.id, agent_id=agent.agent_id, created_at=new_conversation.created_at)

@app.post("/conversations/{conversation_id}/messages", status_code=status.HTTP_202_ACCEPTED, tags=["Conversations"])
async def create_message_in_conversation(
    conversation_id: PydanticObjectId,
    message_in: MessageCreate,
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    特定の会話に新しいメッセージを投稿し、AIの応答タスクを非同期で開始します。
    認証が必要です。
    """
    conversation = await Conversation.find_one(
        Conversation.id == conversation_id,
        Conversation.owner.id == current_user.id,
    )

    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found or access denied")
    
    # task_idを一度だけ生成して、変数に保存する
    task_id = str(uuid.uuid4())

    user_message = Message(
        conversation_id=conversation.id,
        sender={"sender_type": "USER", "sender_id": str(current_user.id)},
        content=message_in.content
        # task_idをDBに保存するロジックは、必要なら後で追加しましょう
    )
    await user_message.insert()

    # Celeryタスクには、保存したtask_idを渡す
    process_agent_response_task.delay(str(user_message.id), task_id)

    # フロントエンドにも、同じtask_idを返す
    return {"status": "ok", "message": "Message received. Agent is thinking...", "task_id": task_id}