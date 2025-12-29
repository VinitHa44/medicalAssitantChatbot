import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.persona import (
    format_response,
    detect_emergency_keywords,
    get_emergency_response,
    DISCLAIMER_MESSAGES
)


def test_format_response():
    """Test response formatting with Dr. Asha persona"""
    raw_response = "Diabetes is a chronic condition affecting blood sugar levels."
    
    formatted = format_response(raw_response, confidence=0.9)
    
    assert raw_response in formatted
    assert isinstance(formatted, str)


def test_format_response_low_confidence():
    """Test response formatting with low confidence"""
    raw_response = "Some information about a condition."
    
    formatted = format_response(raw_response, confidence=0.5)
    
    assert raw_response in formatted
    assert isinstance(formatted, str)


def test_format_response_high_confidence():
    """Test response with high confidence"""
    raw_response = "Clear medical information."
    
    formatted = format_response(raw_response, confidence=0.95)
    
    assert raw_response in formatted


def test_detect_emergency_keywords():
    """Test emergency keyword detection"""
    # Should detect emergencies
    assert detect_emergency_keywords("I'm having severe chest pain")
    assert detect_emergency_keywords("Can't breathe properly")
    assert detect_emergency_keywords("Is this a heart attack?")
    assert detect_emergency_keywords("severe bleeding from wound")
    assert detect_emergency_keywords("having a stroke")
    assert detect_emergency_keywords("unconscious person")
    
    # Should not detect for normal queries
    assert not detect_emergency_keywords("What are diabetes symptoms?")
    assert not detect_emergency_keywords("How to manage hypertension?")
    assert not detect_emergency_keywords("Tell me about nutrition")


def test_emergency_keywords_case_insensitive():
    """Test emergency detection is case insensitive"""
    assert detect_emergency_keywords("CHEST PAIN")
    assert detect_emergency_keywords("Chest Pain")
    assert detect_emergency_keywords("chest pain")


def test_get_emergency_response():
    """Test emergency response message"""
    response = get_emergency_response()
    
    assert isinstance(response, str)
    assert "emergency" in response.lower() or "911" in response or "immediate" in response.lower()
    assert len(response) > 50  # Should be substantive message


def test_format_response_with_sources():
    """Test response formatting (sources handled in response text)"""
    raw_response = "Diabetes information from WHO."
    
    formatted = format_response(raw_response, confidence=0.9)
    
    assert raw_response in formatted
    assert isinstance(formatted, str)


def test_response_templates():
    """Test that response templates are properly formatted"""
    from core.persona import SYSTEM_PROMPT, CHAIN_OF_THOUGHT_PROMPT
    
    assert "Dr. Asha" in SYSTEM_PROMPT
    assert "NOT diagnose" in SYSTEM_PROMPT
    assert "NOT prescribe" in SYSTEM_PROMPT
    
    assert "{context}" in CHAIN_OF_THOUGHT_PROMPT
    assert "{question}" in CHAIN_OF_THOUGHT_PROMPT
