import datetime
import secrets
from typing import Dict, Tuple, Optional
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from .config import settings

# In-memory store for temporary single-use login tokens: {token: (user_id, expires_at)}
_login_tokens: Dict[str, Tuple[int, datetime.datetime]] = {}

# Simple in-memory tracker for rate limits / brute force prevention on API
_failed_login_attempts: Dict[str, int] = {}

security_scheme = HTTPBearer()

def generate_admin_login_token(user_id: int) -> str:
    """
    Generates a secure, 5-minute single-use login token for the admin.
    """
    token = secrets.token_urlsafe(32)
    expiry = datetime.datetime.utcnow() + datetime.timedelta(minutes=5)
    _login_tokens[token] = (user_id, expiry)
    return token

def verify_and_consume_login_token(token: str, client_ip: str) -> Optional[int]:
    """
    Verifies a login token. Consumes it so it cannot be reused.
    Enforces basic anti-brute force tracking per IP.
    """
    # Simple anti brute-force: limit failed attempts per IP
    attempts = _failed_login_attempts.get(client_ip, 0)
    if attempts >= 5:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Juda ko'p urinishlar qilindi. Keyinroq qayta urining."
        )
        
    if token not in _login_tokens:
        _failed_login_attempts[client_ip] = attempts + 1
        return None
        
    user_id, expiry = _login_tokens[token]
    
    # Remove from store (single use)
    del _login_tokens[token]
    
    if datetime.datetime.utcnow() > expiry:
        _failed_login_attempts[client_ip] = attempts + 1
        return None
        
    # Reset failed attempts on success
    if client_ip in _failed_login_attempts:
        del _failed_login_attempts[client_ip]
        
    return user_id

def create_access_token(user_id: int, username: Optional[str] = None) -> str:
    """
    Creates a JWT Access Token.
    """
    expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "sub": str(user_id),
        "username": username or "admin",
        "exp": expire,
        "role": "admin" if user_id == settings.ADMIN_TELEGRAM_ID else "user"
    }
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def get_current_admin(credentials: HTTPAuthorizationCredentials = Security(security_scheme)) -> int:
    """
    Dependency that verifies JWT token and ensures the user is the Admin.
    """
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id_str: str = payload.get("sub")
        role: str = payload.get("role")
        
        if not user_id_str or role != "admin":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Ushbu amalni bajarish uchun ruxsatingiz yo'q.",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        user_id = int(user_id_str)
        if user_id != settings.ADMIN_TELEGRAM_ID:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Siz admin emassiz.",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessiya muddati tugadi yoki token noto'g'ri. Iltimos qayta kiring.",
            headers={"WWW-Authenticate": "Bearer"},
        )
