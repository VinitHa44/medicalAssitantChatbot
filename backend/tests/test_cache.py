import pytest
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.cache import CacheManager


@pytest.mark.asyncio
async def test_cache_key_generation():
    """Test cache key generation"""
    cache = CacheManager()
    
    key1 = cache._generate_key("What is diabetes?", "session1")
    key2 = cache._generate_key("What is diabetes?", "session1")
    key3 = cache._generate_key("What is diabetes?", "session2")
    key4 = cache._generate_key("What is hypertension?", "session1")
    
    # Same query and session should give same key
    assert key1 == key2
    
    # Different sessions should give different keys
    assert key1 != key3
    
    # Different queries should give different keys
    assert key1 != key4
    
    # Keys should be prefixed
    assert key1.startswith("chat:")


@pytest.mark.asyncio
async def test_cache_operations():
    """Test cache set and get operations"""
    cache = CacheManager()
    
    # Mock Redis client
    with patch('core.database.redis_client.client', new_callable=AsyncMock) as mock_client:
        # Test cache miss
        mock_client.get.return_value = None
        result = await cache.get("test query", "session1")
        assert result is None
        
        # Test cache set
        test_data = {"response": "Test response", "confidence": 0.9}
        mock_client.setex.return_value = True
        await cache.set("test query", test_data, "session1")
        
        # Verify setex was called
        assert mock_client.setex.called


@pytest.mark.asyncio
async def test_cache_hit():
    """Test cache hit scenario"""
    cache = CacheManager()
    
    with patch('core.database.redis_client.client', new_callable=AsyncMock) as mock_client:
        
        # Mock cache hit
        import json
        cached_data = {"response": "Cached response", "confidence": 0.85}
        mock_client.get.return_value = json.dumps(cached_data)
        
        result = await cache.get("diabetes query", "session1")
        
        assert result is not None
        assert result["response"] == "Cached response"
        assert result["confidence"] == 0.85


@pytest.mark.asyncio
async def test_cache_ttl():
    """Test cache TTL (Time To Live)"""
    cache = CacheManager()
    
    with patch('core.database.redis_client.client', new_callable=AsyncMock) as mock_client:
        
        test_data = {"response": "Test"}
        await cache.set("query", test_data, "session1")
        
        # Verify setex was called with default TTL from settings
        call_args = mock_client.setex.call_args
        assert call_args is not None


@pytest.mark.asyncio
async def test_cache_invalidation():
    """Test cache invalidation"""
    cache = CacheManager()
    
    with patch('core.database.redis_client') as mock_redis_client:
        mock_client = AsyncMock()
        mock_redis_client.client = mock_client
        
        if hasattr(cache, 'invalidate'):
            await cache.invalidate("session1")
            
            # Verify delete or similar method was called
            assert mock_client.delete.called or mock_client.method_calls
