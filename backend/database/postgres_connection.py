# backend/database/postgres_connection.py

import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from contextlib import contextmanager
from backend.utils.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# SQLAlchemy setup
SQLALCHEMY_DATABASE_URL = settings.POSTGRES_URL

# Check if we're using asyncpg driver
is_async = "asyncpg" in SQLALCHEMY_DATABASE_URL

# Create sync URL for synchronous operations
if is_async:
    SYNC_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
else:
    SYNC_DATABASE_URL = SQLALCHEMY_DATABASE_URL

# Synchronous engine (for migrations, admin tasks, etc.)
engine = create_engine(
    SYNC_DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,  # Recycle connections after 30 minutes
    echo=settings.DEBUG  # Set to True for SQL query logging
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Async engine setup
async_engine = None
AsyncSessionLocal = None

if is_async:
    try:
        async_engine = create_async_engine(
            SQLALCHEMY_DATABASE_URL,
            echo=settings.DEBUG,
            pool_size=10,
            max_overflow=5,
            pool_timeout=30
        )
        
        AsyncSessionLocal = sessionmaker(
            bind=async_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
    except ImportError:
        logger.warning("Async database support not available. Install asyncpg for async support.")

def get_db():
    """
    Dependency function to get database session (synchronous)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_session():
    """
    Context manager for database sessions (synchronous)
    """
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        db.close()

async def get_async_db():
    """
    Async dependency for database session
    """
    if not is_async or AsyncSessionLocal is None:
        raise RuntimeError("Async database not configured. Check asyncpg installation and connection string.")
    
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Async database error: {e}")
            raise
        finally:
            await session.close()

def init_db():
    """
    Initialize database tables (synchronous)
    """
    try:
        # Import models here to ensure they are registered with Base
        from backend.database import models
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except SQLAlchemyError as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

async def async_init_db():
    """
    Initialize database tables asynchronously
    """
    if not is_async or async_engine is None:
        raise RuntimeError("Async database not configured")
    
    try:
        async with async_engine.begin() as conn:
            # Import models here to ensure they are registered with Base
            from backend.database import models
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Async database tables created successfully")
    except SQLAlchemyError as e:
        logger.error(f"Failed to initialize database asynchronously: {e}")
        raise

def test_connection():
    """
    Test database connection (synchronous)
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("PostgreSQL connection test successful")
        return True
    except SQLAlchemyError as e:
        logger.error(f"PostgreSQL connection test failed: {e}")
        return False

# Database health check
def check_db_health():
    """
    Check database health status (synchronous)
    """
    try:
        with engine.connect() as conn:
            # Check connection
            conn.execute(text("SELECT 1"))
            
            # Check if tables exist
            result = conn.execute(
                "SELECT COUNT(*) FROM information_schema.tables "
                "WHERE table_schema = 'public'"
            )
            table_count = result.scalar()
            
            return {
                "status": "healthy",
                "tables_count": table_count,
                "connection": "ok"
            }
    except SQLAlchemyError as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "connection": "failed"
        }