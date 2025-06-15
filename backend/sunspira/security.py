from passlib.context import CryptContext

# パスワードのハッシュ化に使用するアルゴリズムを指定
# bcryptが現在推奨される安全なアルゴリズムです
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """平文のパスワードがハッシュ化されたパスワードと一致するかを検証します"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """平文のパスワードをハッシュ化します"""
    return pwd_context.hash(password)