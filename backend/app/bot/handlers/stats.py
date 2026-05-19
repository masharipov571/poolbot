from aiogram import Router, types, F
from sqlalchemy import select, func
from ...database import SessionLocal
from ... import models
from ..keyboards.inline import get_go_home_keyboard

router = Router()

@router.callback_query(F.data == "my_stats")
async def cb_my_stats(callback: types.CallbackQuery):
    """
    Queries and displays average score logs and historic statistics of the active player.
    """
    async with SessionLocal() as db:
        # Fetch sessions count and sum scores
        sess_q = await db.execute(
            select(func.count(models.QuizSession.id), func.sum(models.QuizSession.score))
            .where(models.QuizSession.user_id == callback.from_user.id)
            .where(models.QuizSession.status == "completed")
        )
        total_sessions, total_score = sess_q.first()
        total_sessions = total_sessions or 0
        total_score = total_score or 0
        
        success_text = (
            f"📊 **Sizning Natijalaringiz:**\n\n"
            f"😔 Hozircha birorta ham test topshirmagansiz. "
            f"Do'stingiz bergan kodni kiritib birinchi testni topshiring!"
        )
        
        if total_sessions > 0:
            q_count_q = await db.execute(
                select(func.sum(models.QuizSession.selected_question_count))
                .where(models.QuizSession.user_id == callback.from_user.id)
                .where(models.QuizSession.status == "completed")
            )
            total_questions = q_count_q.scalar_one_or_none() or 0
            pct = round((total_score / total_questions) * 100, 1) if total_questions > 0 else 0
            
            success_text = (
                f"📊 **Sizning Natijalaringiz:**\n\n"
                f"📝 **Topshirilgan testlar:** {total_sessions} ta\n"
                f"🎯 **To'g'ri javoblar:** {total_score}/{total_questions} ({pct}%)\n"
                f"✨ **O'rtacha muvaffaqiyat:** {pct}%"
            )
            
        await callback.message.edit_text(
            success_text,
            reply_markup=get_go_home_keyboard(),
            parse_mode="Markdown"
        )
