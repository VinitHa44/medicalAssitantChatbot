import hashlib
import json
from typing import Optional, Any
from core.database import redis_client
from config import settings
from loguru import logger


class CacheManager:
    """Manages Redis caching for queries and responses"""
    
    def __init__(self):
        self.ttl = settings.CACHE_TTL
    
    @staticmethod
    def _generate_key(query: str, session_id: str = "") -> str:
        """Generate cache key from query"""
        content = f"{query.lower().strip()}:{session_id}"
        return f"chat:{hashlib.md5(content.encode()).hexdigest()}"
    
    async def get(self, query: str, session_id: str = "") -> Optional[dict]:
        """Retrieve cached response"""
        try:
            key = self._generate_key(query, session_id)
            cached = await redis_client.client.get(key)
            
            if cached:
                logger.info(f"Cache HIT for query: {query[:50]}...")
                return json.loads(cached)
            
            logger.info(f"Cache MISS for query: {query[:50]}...")
            return None
            
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    async def set(self, query: str, response: dict, session_id: str = "") -> bool:
        """Store response in cache"""
        try:
            key = self._generate_key(query, session_id)
            await redis_client.client.setex(
                key,
                self.ttl,
                json.dumps(response)
            )
            logger.info(f"Cached response for: {query[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    async def clear_session(self, session_id: str) -> bool:
        """Clear all cache for a session"""
        try:
            pattern = f"chat:*:{session_id}"
            keys = await redis_client.client.keys(pattern)
            if keys:
                await redis_client.client.delete(*keys)
            return True
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False


cache_manager = CacheManager()
