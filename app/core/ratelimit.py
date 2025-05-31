from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.requests import Request
from starlette.responses import JSONResponse

# Kural: Kullanıcı başına (IP adresi) dakikada 5 istek
RATE_LIMIT_STRING = "5/minute"

limiter = Limiter(key_func=get_remote_address, default_limits=[RATE_LIMIT_STRING])

async def custom_rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Rate limit aşıldığında özel bir yanıt döndürür."""
    return JSONResponse(
        status_code=429,
        content={
            "detail": f"Rate limit exceeded: {exc.detail}",
            "message": "Çok fazla istek gönderdiniz. Lütfen biraz bekleyip tekrar deneyin."
        }
    ) 