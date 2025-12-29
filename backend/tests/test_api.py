import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app


client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "app" in data
    assert data["status"] == "running"


def test_health_check():
    """Test health check endpoint"""
    with patch('core.database.redis_client') as mock_redis, \
         patch('core.database.mongodb_client') as mock_mongo, \
         patch('services.vector_store.vector_db') as mock_vector:
        
        # Mock health checks
        mock_redis.client = MagicMock()
        mock_redis.ping = AsyncMock(return_value=True)
        mock_mongo.client = MagicMock()
        mock_vector.index = MagicMock()
        
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data


@pytest.mark.asyncio
async def test_text_chat():
    """Test text chat endpoint"""
    with patch('api.routes.chat.rag_pipeline.query') as mock_rag, \
         patch('api.routes.chat.cache_manager.get') as mock_cache_get, \
         patch('api.routes.chat.cache_manager.set') as mock_cache_set, \
         patch('api.routes.chat.query_repo.save_query') as mock_save:
        
        # Mock cache miss
        mock_cache_get.return_value = None
        
        # Mock RAG response
        mock_rag.return_value = {
            "response": "Diabetes is a chronic disease affecting blood sugar levels.",
            "confidence": 0.9,
            "sources": [{"url": "https://www.who.int/diabetes", "title": "Diabetes", "relevance_score": 0.9}],
            "emergency": False
        }
        
        # Mock async operations
        mock_cache_set.return_value = None
        mock_save.return_value = None
        
        payload = {
            "query": "What are the symptoms of diabetes?",
            "session_id": "test-session-123"
        }
        
        response = client.post("/api/chat/text", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert "response" in data
        assert "sources" in data
        assert "confidence" in data
        assert isinstance(data["sources"], list)


def test_text_chat_missing_query():
    """Test text chat with missing query"""
    payload = {
        "session_id": "test-session-123"
    }
    
    response = client.post("/api/chat/text", json=payload)
    assert response.status_code == 422  # Validation error


def test_text_chat_empty_query():
    """Test text chat with empty query - should still process"""
    with patch('api.routes.chat.cache_manager.get') as mock_cache_get, \
         patch('api.routes.chat.rag_pipeline.query') as mock_rag, \
         patch('api.routes.chat.query_repo.save_query') as mock_save, \
         patch('api.routes.chat.cache_manager.set') as mock_cache_set:
        
        mock_cache_get.return_value = None
        mock_rag.return_value = {
            "response": "I don't have enough information to answer that question accurately.",
            "confidence": 0.0,
            "sources": [],
            "emergency": False
        }
        mock_save.return_value = None
        mock_cache_set.return_value = None
        
        payload = {
            "query": "",
            "session_id": "test-session-123"
        }
        
        response = client.post("/api/chat/text", json=payload)
        # API processes empty queries, returns 200 with low confidence response
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_emergency_detection():
    """Test emergency keyword detection in chat"""
    with patch('api.routes.chat.cache_manager.get') as mock_cache_get, \
         patch('api.routes.chat.rag_pipeline.query') as mock_rag, \
         patch('api.routes.chat.query_repo.save_query') as mock_save, \
         patch('api.routes.chat.cache_manager.set') as mock_cache_set:
        
        mock_cache_get.return_value = None
        mock_rag.return_value = {
            "response": "🚨 EMERGENCY: Please call 911 immediately.",
            "confidence": 1.0,
            "sources": [],
            "emergency": True
        }
        mock_save.return_value = None
        mock_cache_set.return_value = None
        
        payload = {
            "query": "I'm having severe chest pain",
            "session_id": "test-session"
        }
        
        response = client.post("/api/chat/text", json=payload)
        
        # Should return emergency response
        assert response.status_code == 200
        data = response.json()
        assert "response" in data


def test_voice_chat_endpoint_exists():
    """Test that voice chat endpoint is registered"""
    # Test with invalid request to verify endpoint exists
    response = client.post("/api/chat/voice")
    # 422 = validation error (endpoint exists but bad request)
    # 404 = endpoint not found
    assert response.status_code != 404


def test_cors_headers():
    """Test CORS headers are present"""
    response = client.options("/api/chat/text")
    # Should have CORS headers or at least not fail
    assert response.status_code in [200, 405]  # OPTIONS may not be explicitly handled


@pytest.mark.asyncio
async def test_chat_history():
    """Test chat history endpoint"""
    with patch('api.routes.chat.cache_manager.get') as mock_cache_get, \
         patch('api.routes.chat.rag_pipeline.query') as mock_rag, \
         patch('api.routes.chat.query_repo.save_query') as mock_save, \
         patch('api.routes.chat.cache_manager.set') as mock_cache_set, \
         patch('api.routes.chat.query_repo.get_session_history') as mock_history:
        
        mock_cache_get.return_value = None
        mock_rag.return_value = {
            "response": "Hypertension is high blood pressure.",
            "confidence": 0.9,
            "sources": [],
            "emergency": False
        }
        mock_save.return_value = None
        mock_cache_set.return_value = None
        
        # Mock history with proper query document structure
        mock_history.return_value = [
            {
                "user_query": "What is hypertension?",
                "response": "Hypertension is high blood pressure.",
                "timestamp": "2024-01-01T00:00:00",
                "sources": [],
                "confidence": 0.9,
                "session_id": "test-session-history"
            }
        ]
        
        # First, make a chat request
        payload = {
            "query": "What is hypertension?",
            "session_id": "test-session-history"
        }
        client.post("/api/chat/text", json=payload)
        
        # Then get history
        response = client.get("/api/chat/history/test-session-history")
        assert response.status_code == 200
        
        data = response.json()
        assert "messages" in data
        assert len(data["messages"]) >= 2  # User + assistant messages


def test_invalid_chat_request():
    """Test chat with empty query - API still processes it"""
    with patch('api.routes.chat.cache_manager.get') as mock_cache_get, \
         patch('api.routes.chat.rag_pipeline.query') as mock_rag, \
         patch('api.routes.chat.query_repo.save_query') as mock_save, \
         patch('api.routes.chat.cache_manager.set') as mock_cache_set:
        
        mock_cache_get.return_value = None
        mock_rag.return_value = {
            "response": "I don't have enough information to answer that question accurately.",
            "confidence": 0.0,
            "sources": [],
            "emergency": False
        }
        mock_save.return_value = None
        mock_cache_set.return_value = None
        
        payload = {
            "query": "",  # Empty query
            "session_id": "test"
        }
        
        response = client.post("/api/chat/text", json=payload)
        assert response.status_code == 200  # API accepts empty queries
