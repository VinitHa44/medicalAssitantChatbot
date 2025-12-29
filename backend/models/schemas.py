from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class ChatRequest(BaseModel):
    query: str = Field(..., max_length=500, description="User's medical question")
    session_id: str = Field(..., description="Unique session identifier")


class Source(BaseModel):
    url: str
    title: Optional[str] = None
    relevance_score: float


class ChatResponse(BaseModel):
    response: str
    sources: List[Source]
    confidence: float
    cached: bool = False
    transcribed_query: Optional[str] = None
    audio_url: Optional[str] = None


class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime
    sources: Optional[List[Source]] = None


class ChatHistory(BaseModel):
    session_id: str
    messages: List[Message]


class HealthResponse(BaseModel):
    status: str
    cache: str
    llm: str
    vector_db: str
    database: str
