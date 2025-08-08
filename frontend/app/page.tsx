"use client";

import { useState, useEffect, useRef } from 'react';

// --- 型定義 ---
interface Message {
  id: string;
  sender: { sender_type: 'USER' | 'AGENT' };
  content: string;
  created_at: string;
}

interface Progress {
  step: string;
  details: string;
}

export default function Home() {
  // --- 認証関連のState ---
  const [token, setToken] = useState<string | null>(null);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  // --- チャット関連のState ---
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [userInput, setUserInput] = useState('');
  const [progress, setProgress] = useState<Progress | null>(null);
  const ws = useRef<WebSocket | null>(null);


  // --- 認証関連のロジック (変更なし) ---
  useEffect(() => {
    const storedToken = localStorage.getItem('authToken');
    if (storedToken) {
      setToken(storedToken);
    }
  }, []);

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setMessage('');
    try {
      const response = await fetch('http://localhost:8000/users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || '登録に失敗しました。');
      }
      await handleLogin(e);
      setMessage('登録が成功しました。自動的にログインします。');
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setMessage('');
    try {
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);

      const response = await fetch('http://localhost:8000/login/token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData,
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'ログインに失敗しました。');
      }
      const data = await response.json();
      localStorage.setItem('authToken', data.access_token);
      setToken(data.access_token);
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('authToken');
    setToken(null);
    setEmail('');
    setPassword('');
    // チャットの状態もリセット
    setConversationId(null);
    setMessages([]);
    setError('');
    setMessage('');
  };

  // --- チャット関連のロジック ---
  const getOrCreateConversation = async (): Promise<string> => {
    if (conversationId) {
      return conversationId;
    }

    const response = await fetch('http://localhost:8000/conversations', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errData = await response.json();
      throw new Error(errData.detail || '会話の作成に失敗しました。');
    }

    const convData = await response.json();
    setConversationId(convData.id);
    return convData.id;
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!userInput.trim() || !token) return;

    setError('');
    setProgress({ step: '送信中...', details: '' });

    const currentUserMessage: Message = {
      id: `user-${Date.now()}`,
      sender: { sender_type: 'USER' },
      content: userInput,
      created_at: new Date().toISOString(),
    };
    setMessages(prev => [...prev, currentUserMessage]);
    const messageToSend = userInput;
    setUserInput('');

    try {
      const convId = await getOrCreateConversation();

      const response = await fetch(`http://localhost:8000/conversations/${convId}/messages`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ content: messageToSend }),
      });

      if (response.status !== 202) {
        const errData = await response.json();
        throw new Error(errData.detail || 'メッセージの送信に失敗しました。');
      }

      const result = await response.json();
      connectWebSocket(result.task_id);

    } catch (err: any) {
      setError(err.message);
      setProgress(null); // エラー時は進捗表示を消す
      // 送信失敗したメッセージをUIから削除する
      setMessages(prev => prev.filter(msg => msg.id !== currentUserMessage.id));
    }
  };

  const connectWebSocket = (taskId: string) => {
    // 既存の接続があれば閉じる
    if (ws.current) {
      ws.current.close();
    }

    const socket = new WebSocket(`ws://localhost:8000/ws/v1/tasks/${taskId}/subscribe`);
    ws.current = socket;

    socket.onopen = () => {
      console.log("WebSocket connection established for task:", taskId);
      setProgress({ step: "接続完了", details: "AIの応答を待っています..." });
    };

    socket.onmessage = (event) => {
      const progressData: Progress = JSON.parse(event.data);
      setProgress(progressData);

      if (progressData.step === "完了") {
        const aiMessage: Message = {
          id: `agent-${Date.now()}`,
          sender: { sender_type: 'AGENT' },
          content: progressData.details,
          created_at: new Date().toISOString(),
        };
        setMessages(prev => [...prev, aiMessage]);
        setProgress(null);
        socket.close();
      }
    };

    socket.onerror = (error) => {
      console.error("WebSocket error:", error);
      setError("リアルタイム更新中にエラーが発生しました。");
      setProgress(null);
    };

    socket.onclose = () => {
      console.log("WebSocket connection closed.");
      ws.current = null;
    };
  };

  // コンポーネントのアンマウント時にWebSocket接続を閉じる
  useEffect(() => {
    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, []);

  // --- レンダリング ---
  if (token) {
    // --- チャットUI ---
    return (
      <div className="min-h-screen bg-gray-100 flex flex-col items-center justify-center font-sans">
        <div className="w-full max-w-3xl h-[90vh] bg-white rounded-lg shadow-xl flex flex-col">
          <header className="flex justify-between items-center p-4 border-b">
            <h1 className="text-xl font-bold">SUNSPIRA</h1>
            <button
              onClick={handleLogout}
              className="px-3 py-1 bg-red-500 text-white rounded text-sm hover:bg-red-600"
            >
              ログアウト
            </button>
          </header>

          {/* メッセージ表示エリア */}
          <main className="flex-1 p-4 overflow-y-auto bg-gray-50">
            <div className="space-y-4">
              {messages.map((msg) => (
                <div key={msg.id} className={`flex ${msg.sender.sender_type === 'USER' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-xl ${
                    msg.sender.sender_type === 'USER'
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-200 text-gray-800'
                  }`}>
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                  </div>
                </div>
              ))}
            </div>
             {/* AIの進捗表示エリア */}
            {progress && (
              <div className="flex justify-center items-center my-4">
                <div className="text-sm text-gray-500 p-2 bg-gray-200 rounded-lg shadow-sm">
                  <span className="font-semibold">{progress.step}:</span> {progress.details}
                </div>
              </div>
            )}
          </main>

          {/* メッセージ入力フォーム */}
          <footer className="p-4 border-t">
            <form onSubmit={handleSendMessage} className="flex gap-2">
              <input
                type="text"
                value={userInput}
                onChange={(e) => setUserInput(e.target.value)}
                className="flex-1 p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="メッセージを入力..."
              />
              <button
                type="submit"
                className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-blue-300"
                disabled={!userInput.trim()}
              >
                送信
              </button>
            </form>
          </footer>
        </div>
      </div>
    );
  }

  // --- 認証フォーム (変更なし) ---
  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center">
      <div className="bg-white p-8 rounded-lg shadow-md w-full max-w-md">
        <h1 className="text-2xl font-bold text-center mb-6">SUNSPIRAへようこそ</h1>
        <form>
          <div className="mb-4">
            <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="email">
              メールアドレス
            </label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
              placeholder="email@example.com"
            />
          </div>
          <div className="mb-6">
            <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="password">
              パスワード
            </label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 mb-3 leading-tight focus:outline-none focus:shadow-outline"
              placeholder="******************"
            />
          </div>
          {error && <p className="text-red-500 text-xs italic mb-4">{error}</p>}
          {message && <p className="text-green-500 text-xs italic mb-4">{message}</p>}
          <div className="flex items-center justify-between">
            <button
              onClick={handleLogin}
              className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline"
              type="button"
            >
              ログイン
            </button>
            <button
              onClick={handleRegister}
              className="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline"
              type="button"
            >
              新規登録
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
