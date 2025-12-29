from fastapi import APIRouter, File, UploadFile, Form, HTTPException
import os
import uuid
from loguru import logger

from models.schemas import ChatResponse
from services.rag import rag_pipeline
from services.voice import voice_service
from core.cache import cache_manager
from repositories.mongo_repo import query_repo


# Add voice endpoint to chat router
from api.routes.chat import router


@router.post("/voice", response_model=ChatResponse)
async def chat_voice(
    audio_file: UploadFile = File(...),
    session_id: str = Form(...)
):
    """
    Handle voice-based chat queries
    
    Flow:
    1. Save uploaded audio
    2. Transcribe with Whisper
    3. Check cache with transcribed text
    4. Run RAG if cache miss
    5. Generate audio response with TTS
    6. Return response with audio URL
    """
    temp_audio_path = None
    
    try:
        logger.info(f"Voice chat request from session: {session_id}")
        
        # Validate file
        if not audio_file.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="Invalid audio file")
        
        # Save uploaded audio temporarily
        temp_audio_path = f"temp/{uuid.uuid4()}_{audio_file.filename}"
        os.makedirs("temp", exist_ok=True)
        
        with open(temp_audio_path, "wb") as f:
            content = await audio_file.read()
            f.write(content)
        
        logger.info(f"✓ Audio saved: {temp_audio_path}")
        
        # Transcribe audio to text
        transcription = voice_service.transcribe_audio(temp_audio_path)
        transcribed_query = transcription['text']
        
        logger.info(f"✓ Transcribed: {transcribed_query}")
        
        # Check cache
        cached_response = await cache_manager.get(transcribed_query, session_id)
        
        if cached_response:
            logger.info("⚡ Using cached response")
            text_response = cached_response['response']
            sources = cached_response['sources']
            confidence = cached_response['confidence']
            is_cached = True
        else:
            # Run RAG pipeline
            rag_result = await rag_pipeline.query(transcribed_query)
            
            text_response = rag_result['response']
            sources = rag_result['sources']
            confidence = rag_result['confidence']
            is_cached = False
            
            # Cache the result
            cache_data = {
                'response': text_response,
                'sources': [s.dict() for s in sources],
                'confidence': confidence
            }
            await cache_manager.set(transcribed_query, cache_data, session_id)
        
        # Generate audio response
        audio_url = voice_service.text_to_speech(text_response, session_id)
        
        # Save to MongoDB
        await query_repo.save_query(
            session_id=session_id,
            user_query=transcribed_query,
            response=text_response,
            sources=[s.dict() for s in sources] if not is_cached else sources,
            confidence=confidence,
            cached=is_cached
        )
        
        return ChatResponse(
            response=text_response,
            sources=sources,
            confidence=confidence,
            cached=is_cached,
            transcribed_query=transcribed_query,
            audio_url=audio_url
        )
        
    except Exception as e:
        logger.error(f"✗ Voice chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # Cleanup temp audio file
        if temp_audio_path and os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
            logger.info(f"✓ Cleaned up temp file: {temp_audio_path}")
