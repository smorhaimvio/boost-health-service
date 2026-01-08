"""BH Service - Biomedical Search API.

A secure FastAPI service providing biomedical literature search capabilities
using MedCPT embeddings, Qdrant vector database, and Grok LLM integration.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from api.api.routes import router
from api.core.config import get_settings
from api.core.auth import setup_auth_middleware
from api.core.dependencies import set_bh_core, BHCore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='{"level":"%(levelname)s","logger":"%(name)s","time":%(created)d,"message":"%(message)s"}',
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan managing BH Core."""
    logger.info("Initializing BH Service (MedCPT + Qdrant + Grok)...")
    
    bh_core = BHCore()
    await bh_core.initialize()
    set_bh_core(bh_core)
    
    logger.info("BH Service initialized successfully")
    logger.info("API ready to accept requests")

    yield

    logger.info("Shutting down BH Service...")
    await bh_core.close()
    logger.info("BH Service closed")


# Create FastAPI app
settings = get_settings()
app = FastAPI(
    title="BH Service",
    description="Biomedical Search API with MedCPT + Qdrant + Grok",
    version="1.0.0",
    lifespan=lifespan,
)

# Setup authentication middleware
setup_auth_middleware(app)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": exc.body},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


# Include routers
app.include_router(router)


# Health check endpoints
@app.get("/health_check", tags=["Health"])
async def health_check():
    """Health check endpoint for BoostHealth Service."""
    return {
        "status": "healthy",
        "service": settings.service_name,
        "version": "1.0.0",
    }


# Legacy endpoint for backward compatibility
@app.get("/health", tags=["Health"])
async def health_check_legacy():
    """Legacy health check endpoint (deprecated, use /health_check)."""
    return await health_check()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.debug,
    )

