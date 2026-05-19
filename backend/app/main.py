import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from .config import settings
from .database import init_db
from .bot import bot, dp
from .routers import auth, analytics, users, quizzes, broadcast

# Lifespan manager for FastAPI
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Initialize database tables on startup
    await init_db()
    print("✨ Database initialized successfully!")
    
    # 2. Start Telegram Bot Polling concurrently
    polling_task = asyncio.create_task(dp.start_polling(bot))
    print("🤖 Telegram Bot polling started successfully!")
    
    yield
    
    # 3. Shutdown logic
    print("⏳ Closing Telegram Bot session...")
    polling_task.cancel()
    await bot.session.close()
    print("👋 Shutdown complete!")

app = FastAPI(
    title="PoolBot API",
    description="Professional Telegram Quiz Bot & Admin Dashboard API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration for secure React development environment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for local dev, can restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(auth.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(quizzes.router, prefix="/api")
app.include_router(broadcast.router, prefix="/api")

# Serve Admin frontend build static files if available
# This allows hosting the entire app on a single port!
STATIC_DIR = "./static"
if os.path.exists(STATIC_DIR):
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
else:
    @app.get("/")
    def index():
        return {"status": "running", "message": "FastAPI is running! Build static files inside './static' to serve admin dashboard."}
