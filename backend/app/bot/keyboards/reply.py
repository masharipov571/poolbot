from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

def get_main_reply_keyboard() -> ReplyKeyboardMarkup:
    """
    Returns a premium, compact Telegram-style reply keyboard for the main menu.
    Uses resize_keyboard=True to ensure rounded, native height buttons.
    """
    builder = ReplyKeyboardBuilder()
    builder.button(text="📝 Avtomatik Test")
    builder.button(text="🔑 Kodli Test")
    builder.button(text="📊 Natijalarim")
    builder.button(text="📬 Murojaat")
    builder.button(text="⚙️ Yordam")
    builder.adjust(3, 2) # 3 columns first row, 2 columns second row
    return builder.as_markup(
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Kerakli bo'limni tanlang..."
    )
