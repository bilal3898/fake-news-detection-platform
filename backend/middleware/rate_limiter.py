# backend/middleware/rate_limiter.py
from fastapi import Request, HTTPException
from datetime import datetime, timedelta
import redis
import json

# Simple in-memory rate limiter (replace with Redis in production)
class RateLimiter:
    def __init__(self):
        self.requests = {}
    
    def is_rate_limited(self, key: str, limit: int, window: int) -> bool:
        now = datetime.now()
        window_start = now - timedelta(seconds=window)
        
        if key not in self.requests:
            self.requests[key] = []
        
        # Remove old requests
        self.requests[key] = [req_time for req_time in self.requests[key] if req_time > window_start]
        
        # Check if limit exceeded
        if len(self.requests[key]) >= limit:
            return True
        
        # Add current request
        self.requests[key].append(now)
        return False

rate_limiter = RateLimiter()

def rate_limit(identifier: str, limit: int, window: int):
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            client_ip = request.client.host
            key = f"{identifier}:{client_ip}"
            
            if rate_limiter.is_rate_limited(key, limit, window):
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded. Try again in {window} seconds."
                )
            
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator