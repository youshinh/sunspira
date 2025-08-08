# SUNSPIRA プロジェクト

## 概要
`SUNSPIRA` は、FastAPI製のバックエンドAPIとNext.js製のフロントエンドで構成されるWebアプリケーションです。バックエンドはAIエージェントとの対話を模した非同期タスク処理や、WebSocketによるリアルタイム通信機能を備えています。

## 技術スタック
- **バックエンド**:
  - Python / FastAPI
  - MongoDB (Beanie ODM)
  - Redis (Celeryブローカー, Pub/Sub)
  - Celery (非同期タスクキュー)
  - WebSocket
- **フロントエンド**:
  - TypeScript / Next.js
  - (現在はデフォルトのテンプレートです)

## セットアップと実行 (バックエンド)
1. `backend/`ディレクトリに`.env`ファイルを作成し、以下の環境変数を設定します。
   - `SECRET_KEY` (JWTの署名キー、例: `openssl rand -hex 32` で生成)
   - `MONGO_CONNECTION_STRING_SECRET` (MongoDBの接続文字列, 例: `mongodb://localhost:27017`)
   - `REDIS_URL` (Redisの接続URL, 例: `redis://localhost:6379/0`)
2. 必要なライブラリをインストールします。
   ```bash
   pip install -r backend/requirements.txt
   ```
3. FastAPIサーバーを起動します。(backendディレクトリ内から実行)
   ```bash
   uvicorn sunspira.main:app --reload
   ```
4. Celeryワーカーを起動します。(backendディレクトリ内から実行)
   ```bash
   celery -A sunspira.celery_app worker -l info
   ```

## 現状
- バックエンドAPIの主要な機能と非同期タスク処理の基盤が実装されています。
- フロントエンドは現在、Next.jsのデフォルトテンプレートの状態であり、バックエンドと連携するUIは未実装です。
