import random
import datetime
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, func, update
from ...database import SessionLocal
from ... import models
from ..keyboards.inline import get_go_home_keyboard, get_play_keyboard, get_completed_keyboard

router = Router()

class QuizStates(StatesGroup):
    WaitingForQuizCode = State()

@router.callback_query(F.data == "solve_test_code")
async def cb_solve_test_code(callback: types.CallbackQuery, state: FSMContext):
    """
    Prompts user to enter their 6-digit access code.
    """
    await state.set_state(QuizStates.WaitingForQuizCode)
    await callback.message.edit_text(
        "🔑 **Kod orqali Test Yechish**\n\n"
        "Iltimos, do'stingiz ulashgan 6 xonali unikal test kodini kiriting:\n"
        "*(Masalan: `509823`)*",
        reply_markup=get_go_home_keyboard(),
        parse_mode="Markdown"
    )

@router.message(QuizStates.WaitingForQuizCode)
async def handle_waiting_quiz_code(message: types.Message, state: FSMContext):
    """
    Processes the entered quiz code.
    """
    code = message.text.strip()
    
    if not code.isdigit() or len(code) != 6:
        await message.answer(
            "⚠️ Kod faqat **6 xonali raqamlardan** iborat bo'lishi kerak. Iltimos, qaytadan kiriting:",
            reply_markup=get_go_home_keyboard()
        )
        return
        
    await state.clear()
    await start_quiz_by_code(message, code)

async def start_quiz_by_code(message: types.Message, code: str, user: types.User = None):
    """
    Loads the quiz by its 6-digit code.
    Displays parts selection inline keyboard if quiz has multiple chunks.
    """
    player = user or message.from_user
    async with SessionLocal() as db:
        q = await db.execute(select(models.Quiz).where(models.Quiz.unique_code == code))
        quiz = q.scalar_one_or_none()
        
        if not quiz:
            await message.answer(
                f"😔 **Test topilmadi!**\n"
                f"`{code}` kodli test bazamizda mavjud emas. Iltimos, kodni tekshirib qaytadan kiriting.",
                reply_markup=get_go_home_keyboard(),
                parse_mode="Markdown"
            )
            return
            
        # If chunking is disabled or equals total questions, play directly
        if quiz.chunk_size <= 0 or quiz.chunk_size >= quiz.total_questions:
            await start_actual_quiz(message.bot, player, quiz, chunk_index=0)
        else:
            # Display inline keyboard options for parts selection
            from ..keyboards.inline import get_parts_keyboard
            await message.answer(
                f"📋 **'{quiz.title}' testi topildi!**\n\n"
                f"❓ **Jami savollar:** {quiz.total_questions} ta\n"
                f"📦 **Har bir qismda:** {quiz.chunk_size} tadan savol\n\n"
                f"⚡ Iltimos, topshirmoqchi bo'lgan test qismingizni tanlang:",
                reply_markup=get_parts_keyboard(quiz.id, quiz.total_questions, quiz.chunk_size),
                parse_mode="Markdown"
            )

@router.callback_query(F.data.startswith("playchunk_"))
async def cb_play_chunk(callback: types.CallbackQuery):
    """
    Callback trigger for the selected chunk index. Starts the actual quiz.
    """
    _, quiz_id, chunk_index = callback.data.split("_")
    chunk_index = int(chunk_index)
    
    await callback.message.delete()
    
    async with SessionLocal() as db:
        q = await db.execute(select(models.Quiz).where(models.Quiz.id == quiz_id))
        quiz = q.scalar_one_or_none()
        
        if not quiz:
            await callback.answer("Quiz topilmadi.", show_alert=True)
            return
            
        await start_actual_quiz(callback.bot, callback.from_user, quiz, chunk_index)

async def start_actual_quiz(bot, user, quiz, chunk_index: int):
    """
    Slices the exact questions for the chosen chunk, shuffles, sets up QuizSession, and sends the first question.
    """
    async with SessionLocal() as db:
        # Fetch all questions in ascending order of their creation (original order)
        q_q = await db.execute(
            select(models.Question)
            .where(models.Question.quiz_id == quiz.id)
            .order_by(models.Question.id.asc())
        )
        all_questions = q_q.scalars().all()
        
        if not all_questions:
            await bot.send_message(chat_id=user.id, text="😔 Ushbu testda hech qanday yaroqli savol topilmadi.")
            return
            
        # Slice for the selected chunk index
        if quiz.chunk_size > 0:
            start_idx = chunk_index * quiz.chunk_size
            end_idx = start_idx + quiz.chunk_size
            selected_questions = all_questions[start_idx:end_idx]
        else:
            selected_questions = all_questions
            
        if not selected_questions:
            await bot.send_message(chat_id=user.id, text="😔 Tanlangan qismda savollar topilmadi.")
            return
            
        # Handle Shuffling configurations
        shuf_mode = quiz.shuffle_mode or "none"
        
        # Make a copy of selected questions so we can shuffle inside this chunk
        selected_questions = list(selected_questions)
        if shuf_mode in ["questions", "both"]:
            random.shuffle(selected_questions)
            
        shuffled_q_ids = [q.id for q in selected_questions]
        
        shuffled_options_map = {}
        for q in selected_questions:
            opts = list(q.options)
            correct_opt = opts[q.correct_option_index]
            
            if shuf_mode in ["options", "both"]:
                random.shuffle(opts)
                
            new_correct_idx = opts.index(correct_opt)
            
            shuffled_options_map[str(q.id)] = {
                "options": opts,
                "correct_option_index": new_correct_idx
            }
            
        # Create a new active QuizSession
        session = models.QuizSession(
            user_id=user.id,
            quiz_id=quiz.id,
            selected_question_count=len(selected_questions),
            timer_seconds=quiz.timer_seconds or 0,
            current_question_index=0,
            score=0,
            status="active",
            shuffled_questions=shuffled_q_ids,
            shuffled_options_map=shuffled_options_map
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        
        # Send first question
        await send_next_question_to_user(bot, user.id, session.id)

@router.callback_query(F.data.startswith("start_code_quiz_"))
async def cb_start_code_quiz(callback: types.CallbackQuery):
    """
    Launches a quiz by code directly from the final completion screen.
    """
    code = callback.data.split("start_code_quiz_")[1]
    await callback.message.delete()
    await start_quiz_by_code(callback.message, code, user=callback.from_user)

async def send_next_question_to_user(bot, user_id: int, session_id: str):
    """
    Dispatches the active question for a session using Telegram Polls.
    """
    async with SessionLocal() as db:
        sess_q = await db.execute(select(models.QuizSession).where(models.QuizSession.id == session_id))
        session = sess_q.scalar_one_or_none()
        
        if not session or session.status != "active":
            return
            
        # Check if completed
        if session.current_question_index >= session.selected_question_count:
            await complete_quiz_session(bot, user_id, session)
            return
            
        # Get active question ID
        q_id = session.shuffled_questions[session.current_question_index]
        q_q = await db.execute(select(models.Question).where(models.models.Question.id == q_id))
        question = q_q.scalar_one_or_none()
        
        if not question:
            # Skip if database error
            session.current_question_index += 1
            await db.commit()
            await send_next_question_to_user(bot, user_id, session_id)
            return
            
        # Fetch options config
        opt_config = session.shuffled_options_map[str(q_id)]
        options = opt_config["options"]
        correct_idx = opt_config["correct_option_index"]
        
        progress_lbl = f"Savol {session.current_question_index + 1}/{session.selected_question_count}"
        
        # Check if question text is too long for TG Poll (Max 300 characters)
        poll_text = f"[{progress_lbl}] {question.question_text}"
        if len(poll_text) > 300:
            await bot.send_message(
                chat_id=user_id,
                text=f"📚 **{progress_lbl}**\n\n{question.question_text}",
                parse_mode="Markdown"
            )
            poll_text = "Yuqoridagi savol javobini belgilang 👇:"
            
        # Telegram send_poll arguments
        poll_kwargs = {
            "chat_id": user_id,
            "question": poll_text,
            "options": options[:10],
            "type": "quiz",
            "correct_option_id": correct_idx,
            "is_anonymous": False,
        }
        
        # Apply timer if active
        if session.timer_seconds > 0:
            poll_kwargs["open_period"] = session.timer_seconds
            
        try:
            poll_msg = await bot.send_poll(**poll_kwargs, reply_markup=get_play_keyboard(session.id))
            
            session.active_poll_id = poll_msg.poll.id
            session.active_message_id = poll_msg.message_id
            await db.commit()
        except Exception as e:
            # Fallback if poll creation fails
            await bot.send_message(
                chat_id=user_id,
                text=f"❌ Ushbu savolni yuklashda xatolik: {str(e)}. Keyingisiga o'tilmoqda..."
            )
            session.current_question_index += 1
            await db.commit()
            await send_next_question_to_user(bot, user_id, session_id)

@router.poll_answer()
async def handle_poll_answer(poll_answer: types.PollAnswer):
    """
    Listens to live poll answers, scores them and triggers the next question automatically.
    """
    async with SessionLocal() as db:
        # Match active session
        sess_q = await db.execute(
            select(models.QuizSession)
            .where(models.QuizSession.active_poll_id == poll_answer.poll_id)
            .where(models.QuizSession.status == "active")
        )
        session = sess_q.scalar_one_or_none()
        
        if not session:
            return
            
        # Record answer
        q_id = session.shuffled_questions[session.current_question_index]
        opt_config = session.shuffled_options_map[str(q_id)]
        correct_idx = opt_config["correct_option_index"]
        
        selected_idx = poll_answer.option_ids[0] if poll_answer.option_ids else -1
        is_correct = (selected_idx == correct_idx)
        
        # Store detailed answer
        answer = models.PollAnswer(
            session_id=session.id,
            question_id=q_id,
            user_id=poll_answer.user.id,
            selected_option_index=selected_idx,
            is_correct=is_correct
        )
        db.add(answer)
        
        if is_correct:
            session.score += 1
            
        session.current_question_index += 1
        session.active_poll_id = None
        
        # Clean up inline skip button of past poll
        try:
            await poll_answer.bot.edit_message_reply_markup(
                chat_id=poll_answer.user.id,
                message_id=session.active_message_id,
                reply_markup=None
            )
        except Exception:
            pass
            
        await db.commit()
        await send_next_question_to_user(poll_answer.bot, poll_answer.user.id, session.id)

@router.callback_query(F.data.startswith("skip_"))
async def cb_skip_question(callback: types.CallbackQuery):
    """
    Enables user to manually skip or advance when stuck.
    """
    session_id = callback.data.split("skip_")[1]
    
    async with SessionLocal() as db:
        sess_q = await db.execute(select(models.QuizSession).where(models.QuizSession.id == session_id))
        session = sess_q.scalar_one_or_none()
        
        if not session or session.status != "active":
            await callback.answer()
            return
            
        # Skip count
        q_id = session.shuffled_questions[session.current_question_index]
        
        # Save empty answer
        answer = models.PollAnswer(
            session_id=session.id,
            question_id=q_id,
            user_id=callback.from_user.id,
            selected_option_index=-1,
            is_correct=False
        )
        db.add(answer)
        
        session.current_question_index += 1
        session.active_poll_id = None
        await db.commit()
        
        # Clear reply markup
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
            
        await callback.answer("Savol o'tkazib yuborildi.")
        await send_next_question_to_user(callback.bot, callback.from_user.id, session.id)

async def complete_quiz_session(bot, user_id: int, session: models.QuizSession):
    """
    Completes the session, calculates the percentages, and displays final score card.
    """
    session.status = "completed"
    session.completed_at = datetime.datetime.utcnow()
    
    # Calculate percentages
    pct = round((session.score / session.selected_question_count) * 100, 1) if session.selected_question_count > 0 else 0
    duration = (session.completed_at - session.started_at).seconds
    mins = duration // 60
    secs = duration % 60
    
    # Get quiz unique code to reload cleanly
    async with SessionLocal() as db:
        q_res = await db.execute(select(models.Quiz.unique_code).where(models.Quiz.id == session.quiz_id))
        code = q_res.scalar_one_or_none() or ""
        
        db.add(session)
        await db.commit()
        
    performance_msg = {
        pct >= 90: "🔥 A'lo! Mukammal natija. Siz ushbu mavzuni juda yaxshi bilasiz!",
        pct >= 70: "✨ Juda yaxshi! Ajoyib bilim ko'rsatkichi.",
        pct >= 50: "👍 Qoniqarli. Yana harakat qilib natijani yaxshilashingiz mumkin.",
    }.get(True, "📚 Bo'shashmang! O'rganishda davom eting va yana harakat qilib ko'ring.")
    
    user_name = "O'yinchi"
    if hasattr(session, 'user') and session.user and session.user.first_name:
        user_name = session.user.first_name
        
    score_card = (
        f"🏁 **Test Yakunlandi!**\n\n"
        f"🏆 **Natija:** {session.score}/{session.selected_question_count} ({pct}%)\n"
        f"⏱️ **Sarflangan vaqt:** {mins}m {secs}s\n"
        f"👤 **Foydalanuvchi:** {user_name}\n\n"
        f"{performance_msg}"
    )
    
    await bot.send_message(
        chat_id=user_id, 
        text=score_card, 
        reply_markup=get_completed_keyboard(code), 
        parse_mode="Markdown"
    )
