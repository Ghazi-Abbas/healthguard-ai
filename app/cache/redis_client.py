
import logging

from redis import Redis

from app.core.config import settings


logger = logging.getLogger(__name__)


redis_client = Redis.from_url(
    settings.REDIS_URL,

    # Return strings instead of bytes
    encoding="utf-8",
    decode_responses=True,

    # Connection timeouts
    socket_connect_timeout=2,
    socket_timeout=2,

    # Check connection health
    health_check_interval=30,

    max_connections=20,
)


def get_redis_client() -> Redis:
    return redis_client
