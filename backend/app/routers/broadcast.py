import asyncio
import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import List, Dict, Any
from ..database import get_db, SessionLocal
from ..schemas import BroadcastCreate, BroadcastResponse, BroadcastTargetResponse
from ..auth import get_current_admin
from .. import models
from ..bot.utils.broadcast import run_broadcast_task

router = APIRouter(prefix="/broadcast", tags=["Broadcast System"])

# Keep track of active background task references to allow dynamic control
active_broadcast_tasks = {}

@router.get("/{broadcast_id}/targets", response_model=List[BroadcastTargetResponse])
async def get_broadcast_targets(
    broadcast_id: int,
    admin_id: int = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns the real-time list of all recipients and their specific delivery status for a broadcast.
    """
    query = select(models.BroadcastTarget).where(models.BroadcastTarget.broadcast_id == broadcast_id).order_by(models.BroadcastTarget.id)
    res = await db.execute(query)
    return res.scalars().all()

@router.post("", response_model=BroadcastResponse)
async def create_broadcast(
    payload: BroadcastCreate,
    background_tasks: BackgroundTasks,
    admin_id: int = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Creates a text/media broadcast, schedules it, and launches background dispatching.
    """
    broadcast = models.BroadcastMessage(
        type=payload.type,
        content=payload.content,
        buttons=payload.buttons,
        status="pending",
        scheduled_at=payload.scheduled_at
    )
    db.add(broadcast)
    await db.commit()
    await db.refresh(broadcast)
    
    # Log admin action
    admin_log = models.AdminLog(
        admin_id=admin_id,
        action="CREATE_BROADCAST",
        details=f"Xabar yuborish yaratildi (ID: {broadcast.id}, Turi: {broadcast.type})"
    )
    db.add(admin_log)
    await db.commit()
    
    # If not scheduled (or scheduled for immediate run), kick off task
    if not payload.scheduled_at or payload.scheduled_at <= datetime.datetime.utcnow():
        task = asyncio.create_task(run_broadcast_task(broadcast.id))
        active_broadcast_tasks[broadcast.id] = task
        
    return broadcast

@router.get("", response_model=List[BroadcastResponse])
async def list_broadcasts(
    admin_id: int = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns list of all historic and pending broadcasts.
    """
    query = select(models.BroadcastMessage).order_by(desc(models.BroadcastMessage.created_at))
    res = await db.execute(query)
    return res.scalars().all()

@router.post("/{broadcast_id}/cancel", response_model=Dict[str, Any])
async def cancel_broadcast(
    broadcast_id: int,
    admin_id: int = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Cancels a running or pending broadcast.
    """
    query = select(models.BroadcastMessage).where(models.BroadcastMessage.id == broadcast_id)
    res = await db.execute(query)
    broadcast = res.scalar_one_or_none()
    
    if not broadcast:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Xabar yuborish topilmadi."
        )
        
    if broadcast.status not in ["pending", "sending"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ushbu xabarni bekor qilib bo'lmaydi, status: {broadcast.status}"
        )
        
    broadcast.status = "cancelled"
    await db.commit()
    
    # Cancel background task if active
    if broadcast_id in active_broadcast_tasks:
        active_broadcast_tasks[broadcast_id].cancel()
        del active_broadcast_tasks[broadcast_id]
        
    # Log admin action
    admin_log = models.AdminLog(
        admin_id=admin_id,
        action="CANCEL_BROADCAST",
        details=f"Xabar yuborish bekor qilindi (ID: {broadcast_id})"
    )
    db.add(admin_log)
    await db.commit()
    
    return {
        "message": "Xabar yuborish bekor qilindi.",
        "broadcast_id": broadcast_id
    }
