import time
from .celery_app import celery

@celery.task
def long_running_task(message: str):
    """
    時間のかかる処理をシミュレートするCeleryタスク
    """
    print(f"非同期タスク開始: メッセージ '{message}' を受け取りました。")
    time.sleep(10) # 10秒間、重い処理をしていると仮定
    print("非同期タスク完了。")
    return {"status": "complete", "message": message}