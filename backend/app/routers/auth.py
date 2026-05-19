from fastapi import APIRouter, HTTPException, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..schemas import TokenRequest, TokenResponse
from ..auth import verify_and_consume_login_token, create_access_token
from ..config import settings
from .. import models

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=TokenResponse)
async def login(payload: TokenRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """
    Exchanges a single-use login token for a long-lived JWT access token.
    Enforces IP-based rate limiting on token consumption.
    """
    client_ip = request.client.host if request.client else "unknown"
    
    # Verify and consume the token
    user_id = verify_and_consume_login_token(payload.token, client_ip)
    
    if not user_id or user_id != settings.ADMIN_TELEGRAM_ID:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Noto'g'ri, muddati o'tgan yoki ruxsat etilmagan kirish tokeni."
        )
        
    # User is valid admin, log the action
    admin_log = models.AdminLog(
        admin_id=user_id,
        action="LOGIN",
        details=f"Admin panelga muvaffaqiyatli kirdi. IP: {client_ip}"
    )
    db.add(admin_log)
    await db.commit()
    
    # Create JWT
    jwt_token = create_access_token(user_id=user_id, username="admin")
    
    return TokenResponse(
        access_token=jwt_token,
        token_type="bearer",
        username="admin"
    )
