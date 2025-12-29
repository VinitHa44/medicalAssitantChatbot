"""
Pytest configuration and shared fixtures for backend tests
"""
import pytest
import sys
import os
from unittest.mock import MagicMock, AsyncMock

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture
def mock_redis_client():
    """Mock Redis client"""
    client = AsyncMock()
    client.get = AsyncMock(return_value=None)
    client.setex = AsyncMock(return_value=True)
    client.delete = AsyncMock(return_value=True)
    client.ping = AsyncMock(return_value=True)
    return client


@pytest.fixture
def mock_mongo_client():
    """Mock MongoDB client"""
    client = MagicMock()
    db = MagicMock()
    collection = AsyncMock()
    
    collection.insert_one = AsyncMock(return_value=MagicMock(inserted_id="test-id"))
    collection.insert_many = AsyncMock(return_value=MagicMock(inserted_ids=["id1", "id2"]))
    collection.find_one = AsyncMock(return_value=None)
    
    cursor = AsyncMock()
    cursor.to_list = AsyncMock(return_value=[])
    collection.find = MagicMock(return_value=cursor)
    
    db.__getitem__ = MagicMock(return_value=collection)
    client.__getitem__ = MagicMock(return_value=db)
    
    return client


@pytest.fixture
def mock_pinecone_index():
    """Mock Pinecone index"""
    index = MagicMock()
    index.upsert = MagicMock(return_value={'upserted_count': 10})
    index.query = MagicMock(return_value={
        'matches': [
            {'id': 'chunk1', 'score': 0.9, 'metadata': {}},
            {'id': 'chunk2', 'score': 0.8, 'metadata': {}}
        ]
    })
    index.describe_index_stats = MagicMock(return_value={
        'dimension': 384,
        'total_vector_count': 1000
    })
    return index


@pytest.fixture
def mock_llm_client():
    """Mock Google Gemini LLM client"""
    client = MagicMock()
    model = AsyncMock()
    
    model.generate_content_async = AsyncMock(return_value=MagicMock(
        text="This is a test response from the LLM."
    ))
    
    client.models = MagicMock()
    client.models.generate_content_async = model.generate_content_async
    
    return client


@pytest.fixture
def sample_chunks():
    """Sample document chunks for testing"""
    return [
        {
            'id': 'chunk1',
            'text': 'Diabetes is a chronic disease that affects blood sugar levels.',
            'chunk_index': 0,
            'section': 'Introduction',
            'section_chunk_index': 0,
            'embedding': [0.1] * 384,
            'metadata': {
                'title': 'Diabetes',
                'url': 'https://www.who.int/diabetes',
                'category': 'Non-communicable Diseases'
            }
        },
        {
            'id': 'chunk2',
            'text': 'Common symptoms include increased thirst and frequent urination.',
            'chunk_index': 1,
            'section': 'Symptoms',
            'section_chunk_index': 0,
            'embedding': [0.2] * 384,
            'metadata': {
                'title': 'Diabetes',
                'url': 'https://www.who.int/diabetes',
                'category': 'Non-communicable Diseases'
            }
        }
    ]


@pytest.fixture
def sample_query():
    """Sample query for testing"""
    return "What are the symptoms of diabetes?"


@pytest.fixture
def sample_rag_response():
    """Sample RAG response for testing"""
    return {
        'response': 'Diabetes symptoms include increased thirst, frequent urination, and fatigue.',
        'confidence': 0.9,
        'sources': ['https://www.who.int/diabetes'],
        'cached': False
    }


@pytest.fixture
async def cleanup_test_files():
    """Cleanup test files after tests"""
    yield
    # Cleanup logic here if needed
    import glob
    test_audio_files = glob.glob('static/audio/test-*.mp3')
    for f in test_audio_files:
        try:
            os.remove(f)
        except:
            pass


# Async test configuration
pytest_plugins = ('pytest_asyncio',)


# Configure pytest-asyncio
def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )
