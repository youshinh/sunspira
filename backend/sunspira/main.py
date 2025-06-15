# backend/sunspira/main.py
from fastapi import FastAPI, HTTPException, status
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

# --- モデルとスキーマ、セキュリティ関数のインポート ---
from .models import User, Agent, Conversation, Message
from .schemas import UserCreate, UserRead
from .security import get_password_hash


# --- FastAPIアプリケーションの初期化 ---
app = FastAPI(
    title="SUNSPIRA Backend API",
    description="The core API for the SUNSPIRA computational life form.",
    version="2.1.0"
)

# --- データベース接続の初期化 ---
@app.on_event("startup")
async def startup_db_client():
    mongodb_connection_string = os.getenv("MONGO_CONNECTION_STRING_SECRET")
    
    if not mongodb_connection_string:
        raise ValueError("MongoDB connection string not found.")

    app.mongodb_client = AsyncIOMotorClient(mongodb_connection_string)
    app.mongodb = app.mongodb_client.get_database("sunspira_db")

    await init_beanie(
        database=app.mongodb,
        document_models=[
            User,
            Agent,
            Conversation,
            Message
        ]
    )

@app.on_event("shutdown")
async def shutdown_db_client():
    app.mongodb_client.close()


# --- APIエンドポイントの定義 ---
@app.get("/", tags=["Health Check"])
async def root():
    return {"status": "ok", "message": "Welcome to the SUNSPIRA API"}

# --- 新しいユーザーを作成 ---
@app.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED, tags=["Users"])
async def create_user(user_in: UserCreate):
    """
    新しいユーザーを作成します。
    """
    # 既に同じメールアドレスのユーザーが存在しないかチェック
    existing_user = await User.find_one(User.email == user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="このメールアドレスは既に使用されています。",
        )

    # パスワードをハッシュ化
    hashed_password = get_password_hash(user_in.password)

    # 新しいユーザーオブジェクトを作成
    new_user = User(
        email=user_in.email,
        hashed_password=hashed_password
    )

    # データベースに保存
    await new_user.insert()

    # 作成したユーザー情報を返す (パスワードは含まれない)
    return new_user