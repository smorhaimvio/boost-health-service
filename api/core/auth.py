"""Authentication middleware for BoostHealth Service."""

from fastapi import FastAPI, HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware

from api.core.config import get_settings


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Middleware to validate API keys."""
    
    def __init__(self, app: FastAPI):
        super().__init__(app)
        self.settings = get_settings()
    
    async def dispatch(self, request: Request, call_next):
        """Validate API key for all requests except health checks."""
        # Skip auth for health check endpoints and docs
        if request.url.path in ["/health", "/health_check", "/docs", "/openapi.json", "/redoc"]:
            return await call_next(request)
        
        # Get API key from header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing Authorization header",
            )
        
        # Check if Bearer token format
        if not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Authorization header format. Use 'Bearer <api_key>'",
            )
        
        # Extract API key
        api_key = auth_header.replace("Bearer ", "")
        
        # Validate API key
        valid_keys = self.settings.valid_api_keys
        if not valid_keys:
            # If no API keys configured, allow all requests (development mode)
            return await call_next(request)
        
        if api_key not in valid_keys:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
            )
        
        # Continue processing request
        return await call_next(request)


def setup_auth_middleware(app: FastAPI):
    """Setup authentication middleware."""
    app.add_middleware(APIKeyMiddleware)

