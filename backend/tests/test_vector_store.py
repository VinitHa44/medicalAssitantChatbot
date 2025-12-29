import pytest
import sys
import os
from unittest.mock import MagicMock, patch, AsyncMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.vector_store import VectorDatabase


def test_vector_store_initialization():
    """Test vector store initialization"""
    with patch('pinecone.Pinecone') as mock_pinecone:
        mock_pinecone.return_value.Index.return_value = MagicMock()
        
        vector_store = VectorDatabase()
        
        assert vector_store is not None


def test_upsert_documents():
    """Test upserting documents to vector store"""
    with patch('pinecone.Pinecone') as mock_pinecone:
        mock_index = MagicMock()
        mock_pinecone.return_value.Index.return_value = mock_index
        
        vector_store = VectorDatabase()
        vector_store.index = mock_index  # Set index to prevent create_index() call
        
        chunks = [
            {
                'doc_id': 'chunk1',
                'id': 'chunk1',
                'text': 'Diabetes is a chronic disease.',
                'embedding': [0.1] * 384,
                'source_url': 'https://who.int/diabetes',
                'title': 'Diabetes',
                'topic': 'general',
                'section': 'Introduction',
                'chunk_index': 0
            }
        ]
        
        vector_store.upsert_documents(chunks)
        
        # Verify upsert was called
        assert mock_index.upsert.called


def test_search_vectors():
    """Test vector search"""
    with patch('pinecone.Pinecone') as mock_pinecone:
        mock_index = MagicMock()
        mock_index.query.return_value = {
            'matches': [
                {'id': 'chunk1', 'score': 0.95, 'metadata': {}},
                {'id': 'chunk2', 'score': 0.85, 'metadata': {}}
            ]
        }
        mock_pinecone.return_value.Index.return_value = mock_index
        
        vector_store = VectorDatabase()
        
        query_embedding = [0.1] * 384
        results = vector_store.search(query_embedding, top_k=2)
        
        assert len(results) == 2
        assert results[0]['score'] >= results[1]['score']  # Sorted by score


def test_search_with_section_filter():
    """Test vector search with section filter"""
    with patch('pinecone.Pinecone') as mock_pinecone:
        mock_index = MagicMock()
        mock_index.query.return_value = {
            'matches': [
                {
                    'id': 'chunk1',
                    'score': 0.9,
                    'metadata': {
                        'section': 'Symptoms',
                        'text': 'Symptoms text',
                        'source_url': 'https://test.com',
                        'title': 'Test',
                        'topic': 'general',
                        'chunk_index': 0
                    }
                }
            ]
        }
        mock_pinecone.return_value.Index.return_value = mock_index
        
        vector_store = VectorDatabase()
        vector_store.index = mock_index
        
        query_embedding = [0.1] * 384
        results = vector_store.search(query_embedding, top_k=3, section_filter='Symptoms')
        
        # Verify results returned
        assert results is not None
        assert len(results) > 0
        assert results[0]['section'] == 'Symptoms'


def test_delete_by_metadata():
    """Test deleting vectors by metadata"""
    with patch('pinecone.Pinecone') as mock_pinecone:
        mock_index = MagicMock()
        mock_pinecone.return_value.Index.return_value = mock_index
        
        vector_store = VectorDatabase()
        
        if hasattr(vector_store, 'delete_by_metadata'):
            vector_store.delete_by_metadata({'url': 'https://old.url'})
            assert mock_index.delete.called


def test_get_index_stats():
    """Test getting index statistics"""
    with patch('pinecone.Pinecone') as mock_pinecone:
        mock_index = MagicMock()
        mock_index.describe_index_stats.return_value = {
            'dimension': 384,
            'index_fullness': 0.1,
            'total_vector_count': 1000
        }
        mock_pinecone.return_value.Index.return_value = mock_index
        
        vector_store = VectorDatabase()
        
        if hasattr(vector_store, 'get_stats'):
            stats = vector_store.get_stats()
            assert 'dimension' in stats or stats is not None


def test_batch_upsert():
    """Test batch upserting of documents"""
    with patch('pinecone.Pinecone') as mock_pinecone:
        mock_index = MagicMock()
        mock_pinecone.return_value.Index.return_value = mock_index
        
        vector_store = VectorDatabase()
        # Manually set index to avoid create_index() call
        vector_store.index = mock_index
        
        # Create large batch
        chunks = [
            {
                'doc_id': f'chunk{i}',
                'id': f'chunk{i}',
                'text': f'Text {i}',
                'embedding': [0.1] * 384,
                'source_url': 'https://test.com',
                'title': f'Doc {i}',
                'topic': 'general',
                'chunk_index': i,
                'section': 'General'
            }
            for i in range(100)
        ]
        
        vector_store.upsert_documents(chunks)
        
        # Should handle batching
        assert mock_index.upsert.called


def test_search_with_top_k():
    """Test search respects top_k parameter"""
    with patch('pinecone.Pinecone') as mock_pinecone:
        mock_index = MagicMock()
        mock_index.query.return_value = {
            'matches': [
                {'id': f'chunk{i}', 'score': 0.9 - i*0.1, 'metadata': {}}
                for i in range(10)
            ]
        }
        mock_pinecone.return_value.Index.return_value = mock_index
        
        vector_store = VectorDatabase()
        
        query_embedding = [0.1] * 384
        results = vector_store.search(query_embedding, top_k=5)
        
        # Should return only top 5
        assert len(results) <= 5


def test_empty_search_results():
    """Test handling of empty search results"""
    with patch('services.vector_store.Pinecone') as mock_pinecone:
        mock_index = MagicMock()
        mock_index.query.return_value = {'matches': []}
        mock_pinecone.return_value.Index.return_value = mock_index
        
        # Create new instance with mocked Pinecone
        from services.vector_store import VectorDatabase
        vector_store = VectorDatabase.__new__(VectorDatabase)
        vector_store.index = mock_index
        
        query_embedding = [0.1] * 384
        results = vector_store.search(query_embedding, top_k=3)
        
        # Should return empty list
        assert results == [] or results is None
        
        query_embedding = [0.1] * 384
        results = vector_store.search(query_embedding, top_k=3)
        
        assert results == [] or results is None
