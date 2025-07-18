import asyncio

class PersonalAgent:
    """
    ユーザーの個人的なAIエージェント。
    """
    def __init__(self, system_prompt: str = "You are a helpful assistant."):
        self.system_prompt = system_prompt

    async def generate_response(self, message_content: str, task_id: str, redis_client):
        """
        ユーザーのメッセージに対して、ダミーの応答を生成します。
        進捗をRedisに発行します。
        """
        try:
            # 1. 思考中であることを示す
            await redis_client.publish(f"progress:{task_id}", "Thinking...")
            await asyncio.sleep(1)

            # 2. ダミーの応答を生成
            response_content = f"This is a dummy response to your message: '{message_content}'"

            # 3. 応答生成中であることを示す
            await redis_client.publish(f"progress:{task_id}", "Generating response...")
            await asyncio.sleep(1)

            # 4. 最終的な応答を返す
            await redis_client.publish(f"progress:{task_id}", f"STREAM_COMPLETE:{response_content}")

            return response_content

        except Exception as e:
            error_message = f"An error occurred: {e}"
            await redis_client.publish(f"progress:{task_id}", f"ERROR:{error_message}")
            return None
