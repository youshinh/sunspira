from fastapi import WebSocket
from typing import Dict, List
from collections import defaultdict

class ConnectionManager:
    def __init__(self):
        # タスクIDごとにWebSocket接続のリストを保持する辞書
        self.active_connections: Dict[str, List[WebSocket]] = defaultdict(list)

    async def connect(self, websocket: WebSocket, task_id: str):
        """新しいWebSocket接続を受け入れ、管理下に追加します。"""
        await websocket.accept()
        self.active_connections[task_id].append(websocket)
        print(f"WebSocket connected for task_id: {task_id}")

    def disconnect(self, websocket: WebSocket, task_id: str):
        """WebSocket接続を切断し、管理下から削除します。"""
        self.active_connections[task_id].remove(websocket)
        print(f"WebSocket disconnected for task_id: {task_id}")

    async def broadcast_to_task(self, task_id: str, message: str):
        """特定のタスクIDに紐づく全ての接続にメッセージを送信します。"""
        if task_id in self.active_connections:
            for connection in self.active_connections[task_id]:
                await connection.send_text(message)