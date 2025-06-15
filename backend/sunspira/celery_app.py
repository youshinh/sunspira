import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

redis_url = os.getenv("REDIS_URL")
if not redis_url:
    raise ValueError("No REDIS_URL set for Celery")

# Celeryアプリケーションを作成
# backend.sunspira は、このプロジェクトのメインのPythonパッケージ名です
celery = Celery(
    "sunspira_celery",
    broker=redis_url,
    backend=redis_url,
    include=["sunspira.tasks"] # 実行するタスクが定義されているファイルを指定
)