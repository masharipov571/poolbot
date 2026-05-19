from aiogram import Router, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from ...config import settings
from ...auth import generate_admin_login_token

router = Router()

@router.message(Command("admin"))
async def cmd_admin(message: types.Message):
    """
    SSO login link generator for the Stealth Admin Portal.
    Only responds to the configured ADMIN_TELEGRAM_ID.
    """
    if message.from_user.id != settings.ADMIN_TELEGRAM_ID:
        # Strict silence to remain fully stealth
        return
        
    token = generate_admin_login_token(message.from_user.id)
    
    # Secure link targeting the dashboard entrypoint
    base_url = settings.WEBAPP_URL.rstrip('/') if settings.WEBAPP_URL else "http://localhost:5173"
    secret_url = f"{base_url}/secret-admin-portal?token={token}"
    
    admin_msg = (
        f"🔐 **Yopiq Web Admin Dashboard**\n\n"
        f"Siz tizim administratori sifatida muvaffaqiyatli tanindingiz. "
        f"Xavfsiz kirish uchun quyidagi havolani bosing.\n\n"
        f"⚠️ **Eslatma:** Ushbu havola faqat 5 daqiqa davomida faol bo'ladi va faqat bir marta kirish imkonini beradi."
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🌐 Dashboardga Kirish", url=secret_url)
    
    await message.answer(admin_msg, reply_markup=builder.as_markup(), parse_mode="Markdown")
