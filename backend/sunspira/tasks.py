import time
import json
import redis # Celeryタスク内では標準のredisライブラリを使用
from .celery_app import celery
from .models import Message
import os

# --- 新しいタスクの定義 ---
@celery.task
def process_agent_response_task(message_id: str, task_id: str):
    """
    ユーザーからのメッセージを受け取り、AIの応答を処理し、進捗をRedisに発行するタスク
    """
    # Redisクライアントを初期化
    redis_url = os.getenv("REDIS_URL")
    r = redis.from_url(redis_url)
    
    # このタスク専用の通知チャンネル
    channel = f"progress:{task_id}"

    def publish_progress(step: str, details: str):
        """進捗をJSON形式でRedisにPublishするヘルパー関数"""
        message = json.dumps({"step": step, "details": details})
        r.publish(channel, message)
        print(f"Published to {channel}: {message}")

    try:
        publish_progress("開始", f"メッセージID {message_id} の処理を開始します。")
        time.sleep(2)

        publish_progress("思考中", "データベースで関連情報を検索しています...")
        time.sleep(3)

        publish_progress("思考中", "応答の骨子を組み立てています...")
        time.sleep(3)

        # AIからの応答を生成したと仮定
        agent_response_content = "これはAIエージェントからのリアルタイム応答です。"
        publish_progress("応答生成", agent_response_content)
        time.sleep(1)
        
        publish_progress("完了", "タスクが正常に完了しました。")

    except Exception as e:
        publish_progress("エラー", f"タスク実行中にエラーが発生しました: {str(e)}")
    
    finally:
        # 接続を閉じる
        r.close()

    return {"status": "complete", "message_id": message_id}