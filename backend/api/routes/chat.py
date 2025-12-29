from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime

from models.schemas import ChatRequest, ChatResponse, Source, Message, ChatHistory
from services.rag import rag_pipeline
from core.cache import cache_manager
from repositories.mongo_repo import query_repo
from loguru import logger


router = APIRouter()

# Import voice routes to register them with this router
from api.routes import voice  # noqa: F401, E402


@router.post("/text", response_model=ChatResponse)
async def chat_text(request: ChatRequest):
    """
    Handle text-based chat queries
    
    Flow:
    1. Check cache
    2. If miss, run RAG pipeline
    3. Save to MongoDB
    4. Cache result
    5. Return response
    """
    try:
        logger.info(f"Text chat request: {request.query[:100]}")
        
        # Check cache first
        cached_response = await cache_manager.get(request.query, request.session_id)
        
        if cached_response:
            logger.info("⚡ Returning cached response")
            return ChatResponse(
                response=cached_response['response'],
                sources=cached_response['sources'],
                confidence=cached_response['confidence'],
                cached=True
            )
        
        # RAG pipeline
        rag_result = await rag_pipeline.query(request.query)
        
        # Prepare response
        response = ChatResponse(
            response=rag_result['response'],
            sources=rag_result['sources'],
            confidence=rag_result['confidence'],
            cached=False
        )
        
        # Save to MongoDB
        await query_repo.save_query(
            session_id=request.session_id,
            user_query=request.query,
            response=response.response,
            sources=[s.dict() for s in response.sources],
            confidence=response.confidence,
            cached=False
        )
        
        # Cache the response
        cache_data = {
            'response': response.response,
            'sources': [s.dict() for s in response.sources],
            'confidence': response.confidence
        }
        await cache_manager.set(request.query, cache_data, request.session_id)
        
        return response
        
    except Exception as e:
        logger.error(f"✗ Text chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{session_id}", response_model=ChatHistory)
async def get_chat_history(session_id: str):
    """
    Get chat history for a session
    """
    try:
        logger.info(f"Fetching history for session: {session_id}")
        
        queries = await query_repo.get_session_history(session_id)
        
        # Format messages
        messages = []
        for query in queries:
            # User message
            messages.append(Message(
                role="user",
                content=query['user_query'],
                timestamp=query['timestamp']
            ))
            
            # Assistant message
            sources = [Source(**s) for s in query.get('sources', [])]
            messages.append(Message(
                role="assistant",
                content=query['response'],
                timestamp=query['timestamp'],
                sources=sources
            ))
        
        return ChatHistory(
            session_id=session_id,
            messages=messages
        )
        
    except Exception as e:
        logger.error(f"✗ Failed to get history: {e}")
        raise HTTPException(status_code=500, detail=str(e))
