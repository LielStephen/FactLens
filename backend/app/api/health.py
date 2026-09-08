from fastapi import APIRouter
from app.config import settings

router = APIRouter()


@router.get("/health")
def health_check():
    """
    Health check endpoint.
    Fast, reliable, does NOT invoke an LLM call.
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "llm_provider": "Groq",
        "llm_model": settings.GROQ_MODEL
    }
