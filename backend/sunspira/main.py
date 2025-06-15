from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from typing import Annotated

load_dotenv()

# --- モデル、スキーマ、セキュリティ関数のインポート ---
from .models import User, Agent, Conversation, Message
from .schemas import UserCreate, UserRead, Token
from .security import get_password_hash, verify_password, create_access_token, get_current_user # get_current_user を追加


# --- FastAPIアプリケーションの初期化 ---
app = FastAPI(
    title="SUNSPIRA Backend API",
    description="The core API for the SUNSPIRA computational life form.",
    version="2.1.0"
)

# --- データベース接続の初期化 ---
@app.on_event("startup")
async def startup_db_client():
    """アプリケーション起動時にデータベースに接続します"""
    mongodb_connection_string = os.getenv("MONGO_CONNECTION_STRING_SECRET")
    
    if not mongodb_connection_string:
        raise ValueError("MongoDB connection string not found. Please set MONGO_CONNECTION_STRING_SECRET environment variable.")

    app.mongodb_client = AsyncIOMotorClient(mongodb_connection_string)
    app.mongodb = app.mongodb_client.get_database("sunspira_db")

    # Beanie（モデルとDBを繋ぐライブラリ）を初期化
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
    """アプリケーション終了時にデータベース接続をクローズします"""
    app.mongodb_client.close()


# --- APIエンドポイントの定義 ---

@app.get("/", tags=["Health Check"])
async def root():
    """APIサーバーが正常に動作しているかを確認するためのヘルスチェック用エンドポイントです。"""
    return {"status": "ok", "message": "Welcome to the SUNSPIRA API"}

@app.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED, tags=["Users"])
async def create_user(user_in: UserCreate):
    """新しいユーザーを作成します。"""
    existing_user = await User.find_one(User.email == user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="このメールアドレスは既に使用されています。",
        )
    hashed_password = get_password_hash(user_in.password)
    new_user = User(
        email=user_in.email,
        hashed_password=hashed_password
    )
    await new_user.insert()
    return new_user

@app.post("/login/token", response_model=Token, tags=["Users"])
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    """ユーザー名（メールアドレス）とパスワードでログインし、アクセストークンを発行します。"""
    user = await User.find_one(User.email == form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="メールアドレスまたはパスワードが正しくありません",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"sub": user.email}
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=UserRead, tags=["Users"])
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    現在ログインしているユーザーの情報を取得します。
    このエンドポイントは認証が必要です。
    """
    return current_user