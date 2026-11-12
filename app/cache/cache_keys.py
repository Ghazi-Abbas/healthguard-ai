
import hashlib
import hmac

from app.core.config import settings


def validate_ids(organization_id: int, policy_id: int) -> None:
    if (
        not isinstance(organization_id, int)
        or isinstance(organization_id, bool)
        or organization_id <= 0
    ):
        raise ValueError("Invalid organization ID")

    if (
        not isinstance(policy_id, int)
        or isinstance(policy_id, bool)
        or policy_id <= 0
    ):
        raise ValueError("Invalid policy ID")


def policy_metadata_key(
    organization_id: int,
    policy_id: int
) -> str:
    validate_ids(organization_id, policy_id)

    return (
        f"hg:policy:metadata:v1:"
        f"org:{organization_id}:"
        f"policy:{policy_id}"
    )


def active_policy_version_key(
    organization_id: int,
    policy_id: int
) -> str:
    validate_ids(organization_id, policy_id)

    return (
        f"hg:policy:active-version:v1:"
        f"org:{organization_id}:"
        f"policy:{policy_id}"
    )


def policy_search_key(
    organization_id: int,
    policy_version_id: int,
    query: str
) -> str:
    validate_ids(organization_id, policy_version_id)

    if not isinstance(query, str) or not query.strip():
        raise ValueError("Search query cannot be empty")

    if not settings.CACHE_KEY_SECRET:
        raise ValueError("Cache key secret is not configured")

    normalized_query = " ".join(query.lower().split())

    digest = hmac.new(
        settings.CACHE_KEY_SECRET.encode("utf-8"),
        normalized_query.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    return (
        f"hg:rag:policy-search:v1:"
        f"org:{organization_id}:"
        f"version:{policy_version_id}:"
        f"query:{digest}"
    )


def policy_search_prefix(
    organization_id: int,
    policy_version_id: int
) -> str:

    validate_ids(
        organization_id,
        policy_version_id
    )

    return (
        f"hg:rag:policy-search:v1:"
        f"org:{organization_id}:"
        f"version:{policy_version_id}:"
    )
