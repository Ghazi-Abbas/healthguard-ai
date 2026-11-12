
import json
import pytest

from unittest.mock import Mock
from redis.exceptions import RedisError

from app.cache.cache_service import CacheService


@pytest.fixture
def redis_client():
    return Mock()


@pytest.fixture
def cache_service(redis_client):
    return CacheService(redis_client)


# --------------------------------------------------
# 1. Test cache write
# --------------------------------------------------

def test_set_json_success(cache_service, redis_client):

    data = {
        "policy_id": 101,
        "policy_name": "Medical Policy"
    }

    result = cache_service.set_json(
        key="policy:101",
        value=data,
        ttl_seconds=120
    )

    assert result is True

    redis_client.set.assert_called_once_with(
        "policy:101",
        json.dumps(data, ensure_ascii=False, allow_nan=False),
        ex=120
    )


# --------------------------------------------------
# 2. Test cache read
# --------------------------------------------------

def test_get_json_success(cache_service, redis_client):

    data = {
        "policy_id": 101,
        "policy_name": "Medical Policy"
    }

    redis_client.get.return_value = json.dumps(data)

    result = cache_service.get_json("policy:101")

    assert result == data


# --------------------------------------------------
# 3. Test cache miss
# --------------------------------------------------

def test_get_json_cache_miss(cache_service, redis_client):

    redis_client.get.return_value = None

    result = cache_service.get_json("policy:101")

    assert result is None


# --------------------------------------------------
# 4. Test invalid JSON
# --------------------------------------------------

def test_get_json_invalid_json(cache_service, redis_client):

    redis_client.get.return_value = "{invalid json}"

    result = cache_service.get_json("policy:101")

    assert result is None


# --------------------------------------------------
# 5. Test Redis read failure
# --------------------------------------------------

def test_get_json_redis_error(cache_service, redis_client):

    redis_client.get.side_effect = RedisError("Connection failed")

    result = cache_service.get_json("policy:101")

    assert result is None


# --------------------------------------------------
# 6. Test TTL validation
# --------------------------------------------------

@pytest.mark.parametrize(
    "ttl",
    [0, -1, 1.5, True, "120", None]
)
def test_set_json_invalid_ttl(cache_service, redis_client, ttl):

    with pytest.raises(ValueError):
        cache_service.set_json(
            key="policy:101",
            value={"policy_id": 101},
            ttl_seconds=ttl
        )

    redis_client.set.assert_not_called()


# --------------------------------------------------
# 7. Test invalid cache key
# --------------------------------------------------

@pytest.mark.parametrize(
    "key",
    ["", "   ", None]
)
def test_set_json_invalid_key(cache_service, redis_client, key):

    with pytest.raises(ValueError):
        cache_service.set_json(
            key=key,
            value={"policy_id": 101}
        )

    redis_client.set.assert_not_called()


# --------------------------------------------------
# 8. Test unsupported cache value
# --------------------------------------------------

def test_set_json_unsupported_value(cache_service, redis_client):

    with pytest.raises(TypeError):
        cache_service.set_json(
            key="policy:101",
            value="not a dictionary or list"
        )

    redis_client.set.assert_not_called()


# --------------------------------------------------
# 9. Test Redis write failure
# --------------------------------------------------

def test_set_json_redis_error(cache_service, redis_client):

    redis_client.set.side_effect = RedisError("Connection failed")

    result = cache_service.set_json(
        key="policy:101",
        value={"policy_id": 101}
    )

    assert result is False


# --------------------------------------------------
# 10. Test cache deletion
# --------------------------------------------------

def test_delete_success(cache_service, redis_client):

    redis_client.delete.return_value = 1

    result = cache_service.delete("policy:101")

    assert result is True

    redis_client.delete.assert_called_once_with("policy:101")


# --------------------------------------------------
# 11. Test cache deletion failure
# --------------------------------------------------

def test_delete_redis_error(cache_service, redis_client):

    redis_client.delete.side_effect = RedisError("Connection failed")

    result = cache_service.delete("policy:101")

    assert result is False


# --------------------------------------------------
# 12. Test pattern deletion
# --------------------------------------------------

def test_delete_pattern_success(cache_service, redis_client):

    redis_client.scan_iter.return_value = [
        "policy:101",
        "policy:102"
    ]

    result = cache_service.delete_pattern("policy:*")

    assert result is True

    redis_client.scan_iter.assert_called_once_with(
        match="policy:*",
        count=100
    )

    assert redis_client.delete.call_count == 2


# --------------------------------------------------
# 13. Test pattern deletion with no matching keys
# --------------------------------------------------

def test_delete_pattern_no_matching_keys(cache_service, redis_client):

    redis_client.scan_iter.return_value = []

    result = cache_service.delete_pattern("policy:*")

    assert result is True

    redis_client.delete.assert_not_called()


# --------------------------------------------------
# 14. Test pattern deletion failure
# --------------------------------------------------

def test_delete_pattern_redis_error(cache_service, redis_client):

    redis_client.scan_iter.side_effect = RedisError("Connection failed")

    result = cache_service.delete_pattern("policy:*")

    assert result is False


# --------------------------------------------------
# 15. Test NaN rejection
# --------------------------------------------------

def test_set_json_rejects_nan(cache_service, redis_client):

    result = cache_service.set_json(
        key="policy:101",
        value={"score": float("nan")}
    )

    assert result is False

    redis_client.set.assert_not_called()
