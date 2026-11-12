
import json
import logging

from redis import Redis
from redis.exceptions import RedisError


logger = logging.getLogger(__name__)


class CacheService:

    def __init__(self, client: Redis):
        self.client = client

    def get_json(self, key: str):
        """
        Return a cached JSON value.

        None means cache miss, Redis failure,
        or an invalid cache entry.
        """

        if not isinstance(key, str) or not key.strip():
            raise ValueError("Cache key must be a non-empty string.")

        try:
            cached_value = self.client.get(key)

            if cached_value is None:
                return None

            return json.loads(cached_value)

        except (RedisError, json.JSONDecodeError, UnicodeDecodeError):
            logger.warning("Cache read failed; treating as a miss")
            return None

    def set_json(
        self,
        key: str,
        value: dict | list,
        ttl_seconds: int = 120,
    ) -> bool:
        """
        Store JSON temporarily.

        Return False if Redis is unavailable.
        Invalid input raises ValueError or TypeError.
        """

        if not isinstance(key, str) or not key.strip():
            raise ValueError("Cache key must be a non-empty string.")

        if (
            not isinstance(ttl_seconds, int)
            or isinstance(ttl_seconds, bool)
            or ttl_seconds <= 0
        ):
            raise ValueError("TTL must be a positive integer.")

        if not isinstance(value, (dict, list)):
            raise TypeError("Cache value must be a dictionary or list.")

        try:
            serialized_value = json.dumps(
                value,
                ensure_ascii=False,
                allow_nan=False
            )

            self.client.set(
                key,
                serialized_value,
                ex=ttl_seconds
            )

            return True

        except (RedisError, TypeError, ValueError):
            logger.warning("Cache write failed")
            return False

    def delete(self, key: str) -> bool:
        """
        Delete one cache entry.
        """

        if not isinstance(key, str) or not key.strip():
            raise ValueError("Cache key must be a non-empty string.")

        try:
            self.client.delete(key)
            return True

        except RedisError:
            logger.warning("Cache invalidation failed")
            return False

    def delete_pattern(self, pattern: str) -> bool:
        """
        Delete matching keys using incremental scanning.

        Use only controlled, application-generated patterns.
        """

        if not isinstance(pattern, str) or not pattern.strip():
            raise ValueError("Cache pattern must be a non-empty string.")

        try:
            for key in self.client.scan_iter(
                match=pattern,
                count=100
            ):
                self.client.delete(key)

            return True

        except RedisError:
            logger.warning("Cache pattern invalidation failed")
            return False
