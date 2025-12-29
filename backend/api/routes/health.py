from fastapi import APIRouter
from models.schemas import HealthResponse
from core.database import mongodb_client, redis_client
from services.vector_store import vector_db
from loguru import logger


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Check health status of all services
    """
    status = {
        "status": "healthy",
        "cache": "unknown",
        "llm": "unknown",
        "vector_db": "unknown",
        "database": "unknown"
    }
    
    # Check Redis
    try:
        await redis_client.ping()
        status["cache"] = "connected"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        status["cache"] = "disconnected"
        status["status"] = "degraded"
    
    # Check MongoDB
    try:
        await mongodb_client.db.command('ping')
        status["database"] = "connected"
    except Exception as e:
        logger.error(f"MongoDB health check failed: {e}")
        status["database"] = "disconnected"
        status["status"] = "degraded"
    
    # Check Pinecone
    try:
        stats = vector_db.get_stats()
        if stats['total_vectors'] > 0:
            status["vector_db"] = "ready"
        else:
            status["vector_db"] = "empty"
    except Exception as e:
        logger.error(f"Pinecone health check failed: {e}")
        status["vector_db"] = "error"
        status["status"] = "degraded"
    
    # LLM is always ready (API-based)
    status["llm"] = "ready"
    
    return HealthResponse(**status)
