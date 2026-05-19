import asyncio
import datetime
from sqlalchemy import select, update
from ...database import SessionLocal
from ... import models

async def send_broadcast_message_to_user(
    bot, 
    user_id: int, 
    message_type: str, 
    content: str, 
    buttons = None
) -> bool:
    """
    Sends a broadcast message to a single user.
    If the user has blocked the bot, flags them as blocked in the DB automatically.
    """
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    try:
        reply_markup = None
        if buttons:
            builder = InlineKeyboardBuilder()
            for btn in buttons:
                builder.button(text=btn.get("text", "Batafsil"), url=btn.get("url", ""))
            reply_markup = builder.as_markup()
            
        if message_type == "text":
            await bot.send_message(chat_id=user_id, text=content, reply_markup=reply_markup, parse_mode="HTML")
        elif message_type == "photo":
            await bot.send_photo(chat_id=user_id, photo=content, reply_markup=reply_markup, caption=content if len(content) < 100 else None)
        elif message_type == "video":
            await bot.send_video(chat_id=user_id, video=content, reply_markup=reply_markup)
        elif message_type == "file":
            await bot.send_document(chat_id=user_id, document=content, reply_markup=reply_markup)
        return True
    except Exception as e:
        # Flag user as blocked in database
        async with SessionLocal() as db:
            await db.execute(
                update(models.User)
                .where(models.User.id == user_id)
                .values(is_blocked=True)
            )
            await db.commit()
        raise e

async def run_broadcast_task(broadcast_id: int):
    """
    Background worker that runs the broadcast process.
    Pre-populates the target status logs and progress indicators in real-time.
    """
    from .. import bot
    
    async with SessionLocal() as db:
        # 1. Fetch broadcast
        b_q = await db.execute(select(models.BroadcastMessage).where(models.BroadcastMessage.id == broadcast_id))
        broadcast = b_q.scalar_one_or_none()
        if not broadcast or broadcast.status in ["completed", "cancelled"]:
            return
            
        broadcast.status = "sending"
        await db.commit()
        
        # 2. Fetch target users
        users_q = await db.execute(select(models.User).where(models.User.is_blocked == False))
        targets = users_q.scalars().all()
        
        broadcast.total_targets = len(targets)
        await db.commit()
        
        if not targets:
            broadcast.status = "completed"
            await db.commit()
            return
            
        # 3. Create pending target logs in DB for real-time dashboard progress
        # Delete old targets if somehow present
        from sqlalchemy import delete
        await db.execute(delete(models.BroadcastTarget).where(models.BroadcastTarget.broadcast_id == broadcast_id))
        await db.commit()
        
        for u in targets:
            target_log = models.BroadcastTarget(
                broadcast_id=broadcast_id,
                user_id=u.id,
                username=u.username,
                first_name=u.first_name,
                status="pending"
            )
            db.add(target_log)
        await db.commit()
        
        sent = 0
        failed = 0
        
        for u in targets:
            # Check for dynamic cancellation
            await db.refresh(broadcast)
            if broadcast.status == "cancelled":
                break
                
            success = False
            err_msg = None
            try:
                success = await send_broadcast_message_to_user(
                    bot=bot,
                    user_id=u.id,
                    message_type=broadcast.type,
                    content=broadcast.content,
                    buttons=broadcast.buttons
                )
            except Exception as e:
                success = False
                err_msg = str(e)
                
            # Update target record state
            status_str = "sent" if success else "failed"
            await db.execute(
                update(models.BroadcastTarget)
                .where(models.BroadcastTarget.broadcast_id == broadcast_id)
                .where(models.BroadcastTarget.user_id == u.id)
                .values(
                    status=status_str,
                    error_message=err_msg,
                    sent_at=datetime.datetime.utcnow()
                )
            )
            
            if success:
                sent += 1
            else:
                failed += 1
                
            # Increment broadcast progressive counters
            broadcast.sent_count = sent
            broadcast.failed_count = failed
            await db.commit()
            
            # Rate limit check: ~20 messages/sec
            await asyncio.sleep(0.05)
            
        # Complete session
        await db.refresh(broadcast)
        if broadcast.status != "cancelled":
            broadcast.status = "completed"
        await db.commit()
