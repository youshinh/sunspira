import asyncio
import os
import redis.asyncio as redis
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from .celery_app import celery
from .models import User, Agent, Conversation, Message
from .agents.personal_agent import PersonalAgent


async def run_agent_task(message_id: str, task_id: str):
    """非同期でエージェントのタスクを実行する"""
    # データベース接続
    mongodb_connection_string = os.getenv("MONGO_CONNECTION_STRING_SECRET")
    client = AsyncIOMotorClient(mongodb_connection_string)
    database = client.get_database("sunspira_db")
    await init_beanie(database=database, document_models=[User, Agent, Conversation, Message])

    # Redisクライアントを初期化
    redis_url = os.getenv("REDIS_URL")
    redis_client = redis.from_url(redis_url, decode_responses=True)

    try:
        user_message = await Message.get(message_id)
        if not user_message:
            await redis_client.publish(f"progress:{task_id}", "ERROR:Message not found")
            return

        # ここでは簡略化のため、デフォルトのエージェントを取得または作成します
        # 本来は会話に紐づくエージェントを取得すべきです
        agent = PersonalAgent()

        # エージェントに応答を生成させる
        await agent.generate_response(user_message.content, task_id, redis_client)

    except Exception as e:
        await redis_client.publish(f"progress:{task_id}", f"ERROR:An error occurred: {e}")
    finally:
        await redis_client.close()
        client.close()

@celery.task
def process_agent_response_task(message_id: str, task_id: str):
    """
    ユーザーからのメッセージを受け取り、AIの応答を処理し、進捗をRedisに発行するタスク
    """
    asyncio.run(run_agent_task(message_id, task_id))
    return {"status": "complete", "message_id": message_id}