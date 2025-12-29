from motor.motor_asyncio import AsyncIOMotorClient
from redis.asyncio import Redis
from config import settings
from loguru import logger


class MongoDB:
    """MongoDB connection manager"""
    
    def __init__(self):
        self.client: AsyncIOMotorClient = None
        self.db = None
    
    def connect(self):
        """Initialize MongoDB connection"""
        self.client = AsyncIOMotorClient(settings.MONGODB_URL)
        self.db = self.client[settings.MONGODB_DB_NAME]
        logger.info("MongoDB connection initialized")
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
    
    async def get_queries_collection(self):
        """Get queries collection"""
        return self.db.queries
    
    async def get_documents_collection(self):
        """Get documents collection"""
        return self.db.documents


class RedisCache:
    """Redis connection manager"""
    
    def __init__(self):
        self.client: Redis = None
    
    async def connect(self):
        """Initialize Redis connection"""
        self.client = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            decode_responses=True
        )
        logger.info("Redis connection initialized")
    
    async def close(self):
        """Close Redis connection"""
        if self.client:
            await self.client.close()
            logger.info("Redis connection closed")
    
    async def ping(self):
        """Test Redis connection"""
        if not self.client:
            await self.connect()
        return await self.client.ping()


# Singleton instances
mongodb_client = MongoDB()
mongodb_client.connect()

redis_client = RedisCache()
