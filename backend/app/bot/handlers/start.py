from aiogram import Router, types, F
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, func
from ...database import SessionLocal
from ... import models
from ..keyboards.inline import get_go_home_keyboard, get_start_keyboard
from ..keyboards.reply import get_main_reply_keyboard
from .upload import UploadStates
from .quiz import QuizStates
from .support import SupportStates

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message, command: CommandObject):
    """
    Handles the /start command. Supports unique deep-link launch codes (e.g., /start 102938).
    Attaches the new premium, compact Reply Keyboard at the bottom of the screen.
    """
    if command.args:
        code = command.args.strip()
        from .quiz import start_quiz_by_code
        await start_quiz_by_code(message, code)
        return
        
    welcome_text = (
        f"👋 **Assalomu alaykum, {message.from_user.first_name or 'Foydalanuvchi'}!**\n\n"
        f"🤖 **PoolBot** - Professional Telegram Quiz platformasiga xush kelibsiz.\n\n"
        f"⚡ Quyidagi **pastki ixcham menyu** orqali kerakli bo'limni tanlang:"
    )
    await message.answer(welcome_text, reply_markup=get_main_reply_keyboard(), parse_mode="Markdown")

@router.message(F.text == "📝 Avtomatik Test")
async def msg_auto_test(message: types.Message, state: FSMContext):
    """
    Triggers the FSM state for uploading quiz files directly from the reply keyboard.
    """
    await state.set_state(UploadStates.WaitingForDocument)
    instruction_text = (
        "📄 **Fayl yuboring**\n\n"
        "📁 **Qo'llab-quvvatlanadigan formatlar:** DOCX, DOC, TXT, PDF\n\n"
        "📋 **Fayl formati:**\n"
        "Har bir savol quyidagi shaklda bo'lishi kerak:\n\n"
        "```text\n"
        "+++\n"
        "Savol matni?\n"
        "===\n"
        "#To'g'ri javob\n"
        "===\n"
        "Noto'g'ri javob 1\n"
        "===\n"
        "Noto'g'ri javob 2\n"
        "===\n"
        "Noto'g'ri javob 3\n"
        "+++\n"
        "```\n\n"
        "⚠️ **Muhim:**\n"
        "• `+++` — savol boshlanishi va tugashi\n"
        "• `===` — variantlar orasidagi ajratuvchi\n"
        "• `#` — to'g'ri javob oldiga qo'yiladi\n"
        "• Har bir savolda faqat bitta to'g'ri javob bo'lek kerak\n"
        "• Variantlar soni 2 dan 10 gacha bo'lishi mumkin"
    )
    await message.answer(
        instruction_text,
        reply_markup=get_go_home_keyboard(),
        parse_mode="Markdown"
    )

@router.message(F.text == "🔑 Kodli Test")
async def msg_solve_test(message: types.Message, state: FSMContext):
    """
    Triggers FSM code entry directly from the reply keyboard.
    """
    await state.set_state(QuizStates.WaitingForQuizCode)
    await message.answer(
        "🔑 **Kod orqali Test Yechish**\n\n"
        "Iltimos, do'stingiz ulashgan 6 xonali unikal test kodini kiriting:\n"
        "*(Masalan: `509823`)*",
        reply_markup=get_go_home_keyboard(),
        parse_mode="Markdown"
    )

@router.message(F.text == "📊 Natijalarim")
async def msg_my_stats(message: types.Message):
    """
    Queries and displays average score logs and statistics of the player.
    """
    async with SessionLocal() as db:
        sess_q = await db.execute(
            select(func.count(models.QuizSession.id), func.sum(models.QuizSession.score))
            .where(models.QuizSession.user_id == message.from_user.id)
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
                .where(models.QuizSession.user_id == message.from_user.id)
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
            
        await message.answer(
            success_text,
            reply_markup=get_go_home_keyboard(),
            parse_mode="Markdown"
        )

@router.message(F.text == "📬 Murojaat")
async def msg_support_contact(message: types.Message, state: FSMContext):
    """
    Triggers support ticket creation from the reply keyboard.
    """
    await state.set_state(SupportStates.WaitingForSupportMessage)
    await message.answer(
        "📬 **Adminga Murojaat bo'limi**\n\n"
        "Iltimos, adminga yubormoqchi bo'lgan savolingiz yoki taklifingizni matn ko'rinishida yozib yuboring.\n"
        "Admin javob yozganida bot sizga real-time rejimda xabar beradi! ⚡",
        reply_markup=get_go_home_keyboard(),
        parse_mode="Markdown"
    )

@router.message(F.text == "⚙️ Yordam")
async def msg_quiz_help(message: types.Message):
    """
    Renders step-by-step help manual directly.
    """
    help_text = (
        f"ℹ️ **PoolBot yordam qo'llanmasi:**\n\n"
        f"1️⃣ **Avtomatik Test Tuzish:**\n"
        f"Bosh menyudan '📝 Avtomatik Test' tugmasini bosing va test faylini (`DOCX`, `PDF`, `TXT`) yuboring.\n"
        f"Tizim faylni parse qilib bo'lgach, sizdan chunk (qism), taymer va aralashtirish sozlamalarini so'raydi. Yakunda boshqalarga ulashish uchun 6 xonali unikal kod beriladi.\n\n"
        f"2️⃣ **Kod orqali Test Yechish:**\n"
        f"Do'stingiz bergan 6 xonali unikal kodni kiritish orqali test topshirishni boshlang. "
        f"Savollar va javoblar yaratuvchi sozlamalari bo'yicha yuklanadi.\n\n"
        f"3️⃣ **Adminga murojaat:**\n"
        f"Admin bilan bog'lanish uchun xabar qoldiring. Admin sizga bot orqali javob yozadi."
    )
    await message.answer(help_text, reply_markup=get_go_home_keyboard(), parse_mode="Markdown")

@router.callback_query(F.data == "go_home")
async def cb_go_home(callback: types.CallbackQuery, state: FSMContext):
    """
    Returns user back to the primary landing dashboard.
    Clears FSM state cleanly.
    """
    await state.clear()
    welcome_text = (
        f"🤖 **PoolBot** - Professional Telegram Quiz platformasiga xush kelibsiz.\n\n"
        f"⚡ Boshqarish uchun pastdagi ixcham menyudan foydalanishingiz mumkin:"
    )
    await callback.message.edit_text(welcome_text, reply_markup=get_start_keyboard(), parse_mode="Markdown")

@router.callback_query(F.data == "quiz_help")
async def cb_quiz_help(callback: types.CallbackQuery):
    """
    Renders comprehensive step-by-step help manual.
    """
    help_text = (
        f"ℹ️ **PoolBot yordam qo'llanmasi:**\n\n"
        f"1️⃣ **Avtomatik Test Tuzish:**\n"
        f"Bosh menyudan '📝 Avtomatik Test' tugmasini bosing va test faylini (`DOCX`, `PDF`, `TXT`) yuboring.\n"
        f"Tizim faylni parse qilib bo'lgach, sizdan chunk (qism), taymer va aralashtirish sozlamalarini so'raydi. Yakunda boshqalarga ulashish uchun 6 xonali unikal kod beriladi.\n\n"
        f"2️⃣ **Kod orqali Test Yechish:**\n"
        f"Do'stingiz bergan 6 xonali unikal kodni kiritish orqali test topshirishni boshlang. "
        f"Savollar va javoblar yaratuvchi sozlamalari bo'yicha yuklanadi.\n\n"
        f"3️⃣ **Adminga murojaat:**\n"
        f"Admin bilan bog'lanish uchun xabar qoldiring. Admin sizga bot orqali javob yozadi."
    )
    await callback.message.edit_text(help_text, reply_markup=get_go_home_keyboard(), parse_mode="Markdown")
