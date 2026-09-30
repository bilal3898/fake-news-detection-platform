from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.security import OAuth2PasswordBearer
import jwt
from datetime import datetime
from backend.utils.config import get_settings
from backend.utils.logger import get_logger
from backend.database.postgres_connection import get_db_session
from backend.database.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
logger = get_logger(__name__)

settings = get_settings()

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip auth for public endpoints
        if request.url.path in [
            "/",
            "/health",
            "/status",
            "/info",
            "/docs",
            "/redoc",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/request-password-reset",
            "/api/v1/auth/reset-password"
        ]:
            response = await call_next(request)
        else:
            # Check for API key in headers for machine-to-machine communication
            api_key = request.headers.get("X-API-Key")
            if api_key and api_key == settings.SECRET_KEY:
                response = await call_next(request)
            else:
                # ✅ Right now no JWT enforcement, just pass through
                response = await call_next(request)

        # 🔑 Ensure CORS headers are not lost
        if "access-control-allow-origin" not in response.headers:
            response.headers["Access-Control-Allow-Origin"] = ",".join(settings.ALLOWED_ORIGINS)
            response.headers["Access-Control-Allow-Credentials"] = "true"

        return response