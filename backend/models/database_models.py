from datetime import datetime
from typing import Optional, List


class QueryDocument:
    """MongoDB document for storing queries"""
    
    def __init__(
        self,
        session_id: str,
        user_query: str,
        response: str,
        sources: List[dict],
        confidence: float,
        cached: bool = False,
        timestamp: Optional[datetime] = None
    ):
        self.session_id = session_id
        self.user_query = user_query
        self.response = response
        self.sources = sources
        self.confidence = confidence
        self.cached = cached
        self.timestamp = timestamp or datetime.utcnow()
    
    def to_dict(self):
        return {
            "session_id": self.session_id,
            "user_query": self.user_query,
            "response": self.response,
            "sources": self.sources,
            "confidence": self.confidence,
            "cached": self.cached,
            "timestamp": self.timestamp
        }


class DocumentChunk:
    """MongoDB document for storing scraped medical content"""
    
    def __init__(
        self,
        doc_id: str,
        source_url: str,
        title: str,
        chunk_text: str,
        chunk_index: int,
        topic: str,
        section: str = "General",
        section_chunk_index: int = 0,
        metadata: Optional[dict] = None
    ):
        self.doc_id = doc_id
        self.source_url = source_url
        self.title = title
        self.chunk_text = chunk_text
        self.chunk_index = chunk_index
        self.topic = topic
        self.section = section
        self.section_chunk_index = section_chunk_index
        self.metadata = metadata or {}
    
    def to_dict(self):
        return {
            "doc_id": self.doc_id,
            "source_url": self.source_url,
            "title": self.title,
            "chunk_text": self.chunk_text,
            "chunk_index": self.chunk_index,
            "topic": self.topic,
            "section": self.section,
            "section_chunk_index": self.section_chunk_index,
            "metadata": self.metadata
        }
