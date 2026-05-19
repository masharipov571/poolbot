from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_
from typing import List, Dict, Any, Optional
from ..database import get_db
from ..schemas import UserResponse
from ..auth import get_current_admin
from .. import models

router = APIRouter(prefix="/users", tags=["Users Management"])

@router.get("", response_model=Dict[str, Any])
async def get_users(
    page: int = Query(1, ge=1),
    limit: int = Query(15, ge=1, le=100),
    search: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None), # "blocked" or "active"
    admin_id: int = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns a paginated list of users with search and blocking filters for administration.
    """
    offset = (page - 1) * limit
    
    # Base query
    query = select(models.User)
    count_query = select(func.count(models.User.id))
    
    # Apply search filter (ID, username, first_name, last_name)
    if search:
        search_filter = or_(
            models.User.username.ilike(f"%{search}%"),
            models.User.first_name.ilike(f"%{search}%"),
            models.User.last_name.ilike(f"%{search}%")
        )
        # Check if search is a valid integer for ID search
        if search.isdigit():
            search_filter = or_(search_filter, models.User.id == int(search))
            
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)
        
    # Apply status filter
    if status_filter == "blocked":
        query = query.where(models.User.is_blocked == True)
        count_query = count_query.where(models.User.is_blocked == True)
    elif status_filter == "active":
        query = query.where(models.User.is_blocked == False)
        count_query = count_query.where(models.User.is_blocked == False)
        
    # Apply ordering and pagination
    query = query.order_by(desc(models.User.created_at)).offset(offset).limit(limit)
    
    # Execute queries
    total_q = await db.execute(count_query)
    total = total_q.scalar_one_or_none() or 0
    
    users_q = await db.execute(query)
    users = users_q.scalars().all()
    
    # Parse to schemas
    users_list = []
    for user in users:
        # Get completion statistics for each user
        sess_count_q = await db.execute(
            select(func.count(models.QuizSession.id))
            .where(models.QuizSession.user_id == user.id)
            .where(models.QuizSession.status == "completed")
        )
        completions = sess_count_q.scalar_one_or_none() or 0
        
        users_list.append({
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "created_at": user.created_at,
            "last_active_at": user.last_active_at,
            "is_blocked": user.is_blocked,
            "completions_count": completions
        })
        
    return {
        "users": users_list,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit
    }

@router.post("/{user_id}/block", response_model=Dict[str, Any])
async def toggle_user_block(
    user_id: int,
    admin_id: int = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Blocks or unblocks a specific user.
    """
    if user_id == admin_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O'zingizni bloklay olmaysiz."
        )
        
    user_q = await db.execute(select(models.User).where(models.User.id == user_id))
    user = user_q.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Foydalanuvchi topilmadi."
        )
        
    user.is_blocked = not user.is_blocked
    action = "BLOCKED" if user.is_blocked else "UNBLOCKED"
    
    admin_log = models.AdminLog(
        admin_id=admin_id,
        action=action,
        details=f"Foydalanuvchi {user.first_name or ''} (ID: {user.id}) {action.lower()} qilindi."
    )
    db.add(admin_log)
    await db.commit()
    
    return {
        "message": f"Foydalanuvchi muvaffaqiyatli {'bloklandi' if user.is_blocked else 'blokdan chiqarildi'}.",
        "is_blocked": user.is_blocked
    }
