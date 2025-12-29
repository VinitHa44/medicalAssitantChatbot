from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from loguru import logger
import os

from config import settings
from api.routes import chat, health
from core.database import mongodb_client, redis_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info("Starting Medical Assistant Chatbot...")
    
    # Create necessary directories
    os.makedirs("static/audio", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # Test connections
    try:
        # Test MongoDB
        await mongodb_client.db.command('ping')
        logger.info("✓ MongoDB connected")
        
        # Test Redis
        await redis_client.ping()
        logger.info("✓ Redis connected")
        
    except Exception as e:
        logger.error(f"✗ Connection failed: {e}")
        raise
    
    yield
    
    # Cleanup
    logger.info("Shutting down...")
    mongodb_client.close()
    await redis_client.close()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(health.router, prefix="/api", tags=["health"])

# Static files (mount after routes to avoid conflicts)
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
else:
    logger.warning("Static directory not found - static file serving disabled")


@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
