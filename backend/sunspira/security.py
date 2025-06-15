from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from typing import Optional
import os
from jose import JWTError, jwt
from dotenv import load_dotenv

# --- FastAPIとモデルのインポートを追加 ---
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import ValidationError

# ↓ BeanieのUserモデルをインポート
from .models import User 

load_dotenv()

# --- 定数の設定 ---
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 

if not SECRET_KEY:
    raise ValueError("No SECRET_KEY set for JWT encoding")

# --- トークンを取得するための設定 ---
# "login/token" は、トークンを取得できるAPIエンドポイントのURLです
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login/token")


# --- パスワードハッシュ化（既存のコード） ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# --- アクセストークン作成 ---
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    与えられたデータを含むアクセストークンを生成します。
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- 現在のユーザーを取得する関数 ---
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    リクエストで受け取ったトークンを検証し、現在のユーザー情報を返します。
    この関数自体が、APIエンドポイントの「依存関係」として機能します。
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # トークンから 'sub' (subject) を取得。なければエラー
        email: Optional[str] = payload.get("sub")
        if email is None:
            raise credentials_exception
    except (JWTError, ValidationError):
        raise credentials_exception
    
    # 取得したemailでデータベースからユーザーを検索
    user = await User.find_one(User.email == email)
    if user is None:
        raise credentials_exception
        
    return user