import time
from .celery_app import celery
from beanie import PydanticObjectId
from .models import Message

@celery.task
def process_agent_response_task(message_id: str):
    """
    ユーザーからのメッセージを受け取り、AIエージェントの応答を処理するタスク
    """
    print(f"AIタスク開始: メッセージID {message_id} の処理を開始します。")

    # ここで、将来的にADKエージェントを呼び出す
    print("AIが思考中...")
    time.sleep(5) # 5秒間、AIが考えていると仮定

    # AIからの応答を生成したと仮定
    agent_response_content = "これはAIエージェントからの応答です。"
    print(f"AIの応答生成完了: {agent_response_content}")

    # 本来はここで、AIの応答メッセージをDBに保存したり、
    # WebSocketでユーザーに通知したりする処理が入る

    print(f"AIタスク完了: メッセージID {message_id} の処理が完了しました。")
    return {"status": "complete", "message_id": message_id}