# backend/sunspira/main.py

from fastapi import FastAPI
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

# .envファイルから環境変数を読み込む（開発用）
# 本番環境ではCloud Runの環境変数機能を使用します
load_dotenv()

# --- モデルのインポート ---
# Link機能のために、すべてのモデルをインポートしておく必要があります
from .models import User, Agent, Conversation, Message


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
    
    # Secret Managerから取得した接続文字列を環境変数経由で利用
    # ローカル開発では .env ファイルから読み込む
    mongodb_connection_string = os.getenv("MONGO_CONNECTION_STRING_SECRET")
    
    if not mongodb_connection_string:
        raise ValueError("MongoDB connection string not found. Please set MONGO_CONNECTION_STRING_SECRET environment variable.")

    app.mongodb_client = AsyncIOMotorClient(mongodb_connection_string)
    app.mongodb = app.mongodb_client.get_database("sunspira_db") # データベース名を指定

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
    """
    APIサーバーが正常に動作しているかを確認するための
    ヘルスチェック用エンドポイントです。
    """
    return {"status": "ok", "message": "Welcome to the SUNSPIRA API"}