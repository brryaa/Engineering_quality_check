import time
from collections import defaultdict
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import logger

MAX_BODY_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
RATE_LIMIT_REQUESTS = 300  # requests per minute
RATE_LIMIT_WINDOW_SECONDS = 60


class SecurityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.request_records = defaultdict(list)

    def reset_rate_limits(self):
        self.request_records.clear()

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "127.0.0.1"

        # 1. Rate Limiting Check (exempt internal test suite unless X-Test-Rate-Limit header is present)
        if client_ip != "testclient" or request.headers.get("X-Test-Rate-Limit") == "1":
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

        # 2. Request Body Size Limiting
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_BODY_SIZE_BYTES:
            logger.warning(f"Request body too large ({content_length} bytes) from {client_ip}")
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
