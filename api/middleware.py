"""
Custom middleware for production features
"""
import time
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, Tuple


logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using sliding window algorithm
    """
    
    def __init__(self, app, requests_per_window: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.requests_per_window = requests_per_window
        self.window_seconds = window_seconds
        self.request_counts: Dict[str, list] = defaultdict(list)
    
    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Clean old requests outside window
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.window_seconds)
        self.request_counts[client_ip] = [
            req_time for req_time in self.request_counts[client_ip]
            if req_time > cutoff
        ]
        
        # Check rate limit
        if len(self.request_counts[client_ip]) >= self.requests_per_window:
            logger.warning(
                f"Rate limit exceeded for {client_ip}: "
                f"{len(self.request_counts[client_ip])} requests in {self.window_seconds}s"
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too many requests",
                    "message": f"Rate limit: {self.requests_per_window} requests per {self.window_seconds} seconds"
                },
                headers={
                    "Retry-After": str(self.window_seconds)
                }
            )
        
        # Add current request
        self.request_counts[client_ip].append(now)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = self.requests_per_window - len(self.request_counts[client_ip])
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_window)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        response.headers["X-RateLimit-Reset"] = str(int((now + timedelta(seconds=self.window_seconds)).timestamp()))
        
        return response


class TimingMiddleware(BaseHTTPMiddleware):
    """
    Add request timing and logging
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.request_count = 0
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        self.request_count += 1
        
        # Store count in app state for access by status endpoint
        request.app.state.request_count = getattr(request.app.state, 'request_count', 0) + 1
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000
        
        # Add timing header
        response.headers["X-Process-Time"] = f"{duration_ms:.2f}ms"
        
        # Log request
        client_ip = request.client.host if request.client else "unknown"
        logger.info(
            f"{request.method} {request.url.path} - {response.status_code} - {duration_ms:.2f}ms",
            extra={
                'endpoint': f'{request.method} {request.url.path}',
                'status_code': response.status_code,
                'duration_ms': round(duration_ms, 2),
                'client_ip': client_ip
            }
        )
        
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses
    """
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        return response
