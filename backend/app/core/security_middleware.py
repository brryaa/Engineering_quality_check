import time
from collections import defaultdict
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings
from app.core.logging import logger

MAX_BODY_SIZE_BYTES = settings.MAX_BODY_SIZE_BYTES
RATE_LIMIT_REQUESTS = settings.RATE_LIMIT_REQUESTS
RATE_LIMIT_WINDOW_SECONDS = settings.RATE_LIMIT_WINDOW_SECONDS


class SecurityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.request_records = defaultdict(list)

    def reset_rate_limits(self):
        self.request_records.clear()

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "127.0.0.1"

        # 1. Rate Limiting Check
        # Enforce rate limiting across all clients.
        # Internal test client is exempt unless explicit test flag X-Test-Rate-Limit is set.
        # NO client-supplied bypass headers (e.g. X-Benchmark) are permitted in production logic.
        if settings.RATE_LIMIT_ENABLED and (client_ip != "testclient" or request.headers.get("X-Test-Rate-Limit") == "1"):
            now = time.time()
            timestamps = self.request_records[client_ip]
            # Keep only timestamps within window
            self.request_records[client_ip] = [ts for ts in timestamps if now - ts < RATE_LIMIT_WINDOW_SECONDS]

            if len(self.request_records[client_ip]) >= RATE_LIMIT_REQUESTS:
                logger.warning(f"Rate limit exceeded for client {client_ip}")
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"success": False, "error": "Too many requests. Rate limit exceeded, please slow down."}
                )

            self.request_records[client_ip].append(now)

        # 2. Request Body Size Limiting with robust header parsing
        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                length = int(content_length)
            except (ValueError, TypeError):
                logger.warning(f"Malformed Content-Length header ({content_length}) from {client_ip}")
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"success": False, "error": "Invalid Content-Length header. Must be a valid integer."}
                )

            if length < 0:
                logger.warning(f"Negative Content-Length header ({length}) from {client_ip}")
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"success": False, "error": "Content-Length header cannot be negative."}
                )

            if length > MAX_BODY_SIZE_BYTES:
                logger.warning(f"Request body too large ({length} bytes) from {client_ip}")
                return JSONResponse(
                    status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                    content={"success": False, "error": f"Request body exceeds maximum allowed size ({MAX_BODY_SIZE_BYTES} bytes)."}
                )

        # Process Request
        response = await call_next(request)

        # 3. Add Security Headers (OWASP Recommended)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response
