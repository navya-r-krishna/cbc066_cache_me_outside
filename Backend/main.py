import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import get_settings
from db import connect_to_mongo, close_mongo_connection

# Shared AI Models state (Loaded once at startup)
app_state = {}

logger = logging.getLogger("uvicorn")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP LOGIC ---
    settings = get_settings()
    logger.info("Starting up application...")
    
    # 1. Connect to MongoDB
    await connect_to_mongo()
    
    # 2. Warm up embedding model for De-duplication (Task 3 preview)
    try:
        logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL_NAME}...")
        from sentence_transformers import SentenceTransformer
        app_state["embedding_model"] = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
        logger.info("Embedding model loaded successfully!")
    except Exception as e:
        logger.warning(f"Could not load SentenceTransformer on startup: {e}")

    yield

    # --- SHUTDOWN LOGIC ---
    logger.info("Shutting down application...")
    await close_mongo_connection()

settings = get_settings()

app = FastAPI(
    title="AI-Based Interview Question Generator API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Standardized Global Error Handler for Frontend Consistency
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception caught on {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "message": "An unexpected server error occurred.",
            "detail": str(exc),
            "path": str(request.url.path)
        }
    )

# Healthcheck Endpoint
@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    from db import get_database
    db = get_database()
    db_status = "connected" if db is not None else "disconnected"
    
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "database": db_status,
        "embedding_model_loaded": "embedding_model" in app_state
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=settings.PORT, reload=True)