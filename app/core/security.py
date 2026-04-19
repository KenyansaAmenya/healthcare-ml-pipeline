from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_ipaddr
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import settings


limiter = Limiter(
    key_func=get_ipaddr,
    default_limits=[settings.api_rate_limit],
)


def setup_rate_limiting(app):
    
    app.state.limiter = limiter

    app.add_middleware(SlowAPIMiddleware)

    app.add_exception_handler(
        RateLimitExceeded,
        _rate_limit_exceeded_handler
    )