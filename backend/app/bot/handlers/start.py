from aiogram import Router, types, F
from aiogram.filters import Command, CommandObject
from ..keyboards.inline import get_start_keyboard, get_go_home_keyboard

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message, command: CommandObject):
    """
    Handles the /start command. Supports unique deep-link launch codes (e.g., /start 102938).
    """
    if command.args:
        code = command.args.strip()
        from .quiz import start_quiz_by_code
        await start_quiz_by_code(message, code)
        return
        
    welcome_text = (
        f"👋 **Assalomu alaykum, {message.from_user.first_name or 'Foydalanuvchi'}!**\n\n"
        f"🤖 **PoolBot** - Professional Telegram Quiz platformasiga xush kelibsiz.\n\n"
        f"Bu yerda siz:\n"
        f"• 📝 **Avtomatik testlar:** DOCX, PDF, TXT fayllarini yuklab testlar yaratishingiz\n"
        f"• 🔑 **Kod orqali test:** Do'stlaringiz yaratgan testlarni yagona kod orqali yechishingiz\n"
        f"• 📊 **Natijalar:** Barcha testlaringiz va o'rtacha statistikani kuzatishingiz\n"
        f"• 📬 **Adminga murojaat:** Muammolar yuzasidan admin bilan bog'lanishingiz mumkin.\n\n"
        f"⚡ Kerakli bo'limni tanlash uchun quyidagi tugmalardan foydalaning:"
    )
    await message.answer(welcome_text, reply_markup=get_start_keyboard(), parse_mode="Markdown")

@router.callback_query(F.data == "go_home")
async def cb_go_home(callback: types.CallbackQuery):
    """
    Returns user back to the primary landing dashboard.
    """
    welcome_text = (
        f"🤖 **PoolBot** - Professional Telegram Quiz platformasiga xush kelibsiz.\n\n"
        f"⚡ Kerakli bo'limni tanlash uchun quyidagi tugmalardan foydalaning:"
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
        f"Bosh menyudan '📝 Avtomatik Test Tuzish' tugmasini bosing va test faylini (`DOCX`, `PDF`, `TXT`) yuboring.\n"
        f"Tizim faylni parse qilib bo'lgach, sizdan chunk (qism), taymer va aralashtirish sozlamalarini so'raydi. Yakunda boshqalarga ulashish uchun 6 xonali unikal kod beriladi.\n\n"
        f"2️⃣ **Kod orqali Test Yechish:**\n"
        f"Do'stingiz bergan 6 xonali unikal kodni kiritish orqali test topshirishni boshlang. "
        f"Savollar va javoblar yaratuvchi sozlamalari bo'yicha yuklanadi.\n\n"
        f"3️⃣ **Adminga murojaat:**\n"
        f"Admin bilan bog'lanish uchun xabar qoldiring. Admin sizga bot orqali javob yozadi."
    )
    await callback.message.edit_text(help_text, reply_markup=get_go_home_keyboard(), parse_mode="Markdown")
