from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from .config import settings

# If using PostgreSQL, verify driver. Standard asyncpg works with postgresql+asyncpg://
# Default is sqlite+aiosqlite:///./poolbot.db
DATABASE_URL = settings.DATABASE_URL
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    # SQLite requires some thread-safety arguments if running with multiple threads
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

Base = declarative_base()

async def get_db():
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_db():
    async with engine.begin() as conn:
        # Create all tables in database
        await conn.run_sync(Base.metadata.create_all)
        
    # Self-healing migration: Add new quiz columns if they don't exist
    from sqlalchemy import text
    async with engine.connect() as conn:
        # List of columns to dynamically append to the quizzes table
        columns_to_add = [
            ("unique_code", "VARCHAR"),
            ("chunk_size", "INTEGER DEFAULT 0"),
            ("timer_seconds", "INTEGER DEFAULT 0"),
            ("shuffle_mode", "VARCHAR DEFAULT 'none'")
        ]
        
        for col_name, col_type in columns_to_add:
            try:
                await conn.execute(text(f"ALTER TABLE quizzes ADD COLUMN {col_name} {col_type};"))
                await conn.commit()
                print(f"✨ Database migration: Column '{col_name}' added to quizzes table.")
            except Exception:
                # Silently catch and pass if the column already exists or other errors occur
                pass
                
        # Self-healing migration for quiz_sessions: Add chunk_index
        try:
            await conn.execute(text("ALTER TABLE quiz_sessions ADD COLUMN chunk_index INTEGER DEFAULT 0;"))
            await conn.commit()
            print("✨ Database migration: Column 'chunk_index' added to quiz_sessions table.")
        except Exception:
            pass

