from pymongo.errors import ConnectionFailure
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

from ..utils.config import get_settings
from ..utils.logger import get_logger

logger = get_logger(__name__)

load_dotenv()
settings = get_settings()

class MongoDB:
    client: AsyncIOMotorClient = None
    database = None
    database_name = None  # ✅ Yeh add karen

mongodb = MongoDB()

async def connect_to_mongo():
    """Connect to MongoDB at app startup"""
    try:
        if mongodb.client is None:  # ✅ 'is None' use karen
            mongodb.client = AsyncIOMotorClient(settings.MONGODB_URL)
            mongodb.database_name = settings.MONGODB_DB_NAME  # ✅ Yeh set karen
            mongodb.database = mongodb.client[settings.MONGODB_DB_NAME]

            # Test connection
            await mongodb.client.admin.command("ping")
            logger.info("✅ Connected to MongoDB successfully")
    except ConnectionFailure as e:
        logger.error(f"❌ Failed to connect to MongoDB: {e}")
        raise

async def close_mongo_connection():
    """Close MongoDB connection at app shutdown"""
    if mongodb.client:
        mongodb.client.close()
        mongodb.client = None
        mongodb.database = None
        mongodb.database_name = None
        logger.info("🔌 MongoDB connection closed")

async def get_database():  # ✅ 'async' add karen
    """Return active MongoDB database instance"""
    if mongodb.database is None:  # ✅ Direct database check karen
        await connect_to_mongo()
    return mongodb.database