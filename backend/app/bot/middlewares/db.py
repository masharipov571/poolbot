from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable
import datetime
from sqlalchemy import select
from ...database import SessionLocal
from ... import models

class DatabaseUserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user = None
        if hasattr(event, "from_user") and event.from_user:
            user = event.from_user
            
        if user:
            # Register or update user details in DB dynamically
            async with SessionLocal() as db:
                q = await db.execute(select(models.User).where(models.User.id == user.id))
                db_user = q.scalar_one_or_none()
                
                if not db_user:
                    db_user = models.User(
                        id=user.id,
                        username=user.username,
                        first_name=user.first_name,
                        last_name=user.last_name,
                        is_blocked=False,
                        created_at=datetime.datetime.utcnow()
                    )
                    db.add(db_user)
                else:
                    db_user.username = user.username
                    db_user.first_name = user.first_name
                    db_user.last_name = user.last_name
                    db_user.last_active_at = datetime.datetime.utcnow()
                    db_user.is_blocked = False
                    
                await db.commit()
                
        return await handler(event, data)

def register_all_middlewares(dp):
    dp.message.outer_middleware(DatabaseUserMiddleware())
    dp.callback_query.outer_middleware(DatabaseUserMiddleware())
