import os
from aiogram import Bot, Dispatcher
from ..config import settings

# Initialize Bot and Dispatcher
bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher()

# Directories for temp uploads
UPLOAD_DIR = "./data/temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Central dispatcher setup
def setup_bot():
    from .handlers import register_all_handlers
    from .middlewares.db import register_all_middlewares
    
    register_all_middlewares(dp)
    register_all_handlers(dp)

setup_bot()

# Expose send_broadcast_message_to_user for external routers
from .utils.broadcast import send_broadcast_message_to_user
