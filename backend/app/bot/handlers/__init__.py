from aiogram import Dispatcher

def register_all_handlers(dp: Dispatcher):
    """
    Registers all modular bot routers sequentially to the Dispatcher.
    """
    from .start import router as start_router
    from .admin import router as admin_router
    from .upload import router as upload_router
    from .quiz import router as quiz_router
    from .support import router as support_router
    from .stats import router as stats_router
    
    # Start and support go first to capture commands cleanly
    dp.include_router(start_router)
    dp.include_router(admin_router)
    dp.include_router(support_router)
    dp.include_router(upload_router)
    dp.include_router(quiz_router)
    dp.include_router(stats_router)
