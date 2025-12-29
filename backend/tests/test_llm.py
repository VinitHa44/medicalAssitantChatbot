import pytest
import sys
import os
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.llm import GeminiLLM


def test_llm_generate_response():
    """Test LLM response generation"""
    with patch('google.genai.Client') as mock_client:
        mock_model = MagicMock()
        mock_model.generate_content.return_value.text = "Diabetes is a chronic disease affecting blood sugar levels."
        
        mock_client.return_value.models = MagicMock()
        mock_client.return_value.models.generate_content = mock_model.generate_content
        
        llm = GeminiLLM()
        
        context = [
            {"text": "Diabetes is characterized by high blood glucose.", "title": "Diabetes", "source_url": "https://who.int"},
            {"text": "Type 1 diabetes is an autoimmune condition.", "title": "Type 1", "source_url": "https://who.int"}
        ]
        
        result = llm.generate_response("What is diabetes?", context)
        
        assert result is not None
        assert 'response' in result
        assert 'confidence' in result


def test_llm_with_chain_of_thought():
    """Test LLM with chain of thought prompting"""
    with patch('google.genai.Client') as mock_client:
        mock_model = MagicMock()
        mock_model.generate_content.return_value.text = """
        <thinking>Analyzing diabetes information</thinking>
        <response>Diabetes is a metabolic disorder.</response>
        <confidence>0.9</confidence>
        """
        
        mock_client.return_value.models = MagicMock()
        mock_client.return_value.models.generate_content = mock_model.generate_content
        
        llm = GeminiLLM()
        
        context = [{"text": "Medical text", "title": "Source", "source_url": "https://who.int"}]
        
        result = llm.generate_response("What is diabetes?", context)
        
        assert result is not None


def test_llm_error_handling():
    """Test LLM error handling"""
    with patch('google.genai.Client') as mock_client:
        mock_client.return_value.models.generate_content.side_effect = Exception("API Error")
        
        llm = GeminiLLM()
        
        # Should handle errors gracefully
        try:
            result = llm.generate_response("Query", [{"text": "Context", "title": "Source", "source_url": "https://who.int"}])
            # Should return error response or None
            assert result is None or 'error' in result
        except Exception as e:
            # Or raise the exception
            assert "API Error" in str(e)


def test_llm_confidence_extraction():
    """Test confidence score extraction from LLM response"""
    with patch('google.genai.Client') as mock_client:
        mock_model = MagicMock()
        mock_model.generate_content.return_value.text = """
        <response>Medical information here</response>
        <confidence>0.85</confidence>
        """
        
        mock_client.return_value.models = MagicMock()
        mock_client.return_value.models.generate_content = mock_model.generate_content
        
        llm = GeminiLLM()
        
        result = llm.generate_response("Query", [{"text": "Context", "title": "Source", "source_url": "https://who.int"}])
        
        if result and 'confidence' in result:
            assert 0 <= result['confidence'] <= 1


def test_llm_empty_context():
    """Test LLM with empty context"""
    with patch('google.genai.Client') as mock_client:
        mock_model = MagicMock()
        mock_model.generate_content.return_value.text = "I don't have specific information."
        
        mock_client.return_value.models = MagicMock()
        mock_client.return_value.models.generate_content = mock_model.generate_content
        
        llm = GeminiLLM()
        
        result = llm.generate_response("Query", [])
        
        # Should still generate response even with empty context
        assert result is not None


def test_llm_long_context():
    """Test LLM with long context"""
    with patch('google.genai.Client') as mock_client:
        mock_model = MagicMock()
        mock_model.generate_content.return_value.text = "Comprehensive response based on context."
        
        mock_client.return_value.models = MagicMock()
        mock_client.return_value.models.generate_content = mock_model.generate_content
        
        llm = GeminiLLM()
        
        # Long context
        context = [{"text": f"Context paragraph {i}", "title": f"Source {i}", "source_url": "https://who.int"} for i in range(100)]
        
        result = llm.generate_response("Query", context)
        
        assert result is not None
