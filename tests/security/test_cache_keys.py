
import pytest

from app.cache.cache_keys import (
    policy_metadata_key,
    policy_search_key,
)
from app.cache.cache_keys import policy_search_prefix

# Use a predictable secret for testing.
@pytest.fixture(autouse=True)
def set_cache_secret(monkeypatch):
    monkeypatch.setattr(
        "app.cache.cache_keys.settings.CACHE_KEY_SECRET",
        "test-cache-secret"
    )


# 1. Same organization and policy produce the same metadata key.
def test_same_organization_and_policy_produce_same_metadata_key():
    first_key = policy_metadata_key(
        organization_id=1,
        policy_id=10
    )

    second_key = policy_metadata_key(
        organization_id=1,
        policy_id=10
    )

    assert first_key == second_key


# 2. Different organizations produce different metadata keys.
def test_different_organizations_produce_different_metadata_keys():
    first_key = policy_metadata_key(
        organization_id=1,
        policy_id=10
    )

    second_key = policy_metadata_key(
        organization_id=2,
        policy_id=10
    )

    assert first_key != second_key


# 3. Different policies produce different metadata keys.
def test_different_policies_produce_different_metadata_keys():
    first_key = policy_metadata_key(
        organization_id=1,
        policy_id=10
    )

    second_key = policy_metadata_key(
        organization_id=1,
        policy_id=20
    )

    assert first_key != second_key


# 4. Different organizations produce different policy-search keys.
def test_different_organizations_produce_different_search_keys():
    first_key = policy_search_key(
        organization_id=1,
        policy_version_id=10,
        query="General policy question"
    )

    second_key = policy_search_key(
        organization_id=2,
        policy_version_id=10,
        query="General policy question"
    )

    assert first_key != second_key


# 5. Empty queries are rejected.
@pytest.mark.parametrize("query", ["", " ", "\n", "\t"])
def test_empty_search_query_is_rejected(query):
    with pytest.raises(ValueError):
        policy_search_key(
            organization_id=1,
            policy_version_id=10,
            query=query
        )


# 6. Invalid organization and policy IDs are rejected.
@pytest.mark.parametrize(
    "organization_id, policy_id",
    [
        (0, 10),
        (-1, 10),
        (1, 0),
        (1, -10),
        (True, 10),
        (1, False),
        ("1", 10),
        (1, "10"),
    ]
)
def test_invalid_ids_are_rejected(organization_id, policy_id):
    with pytest.raises(ValueError):
        policy_metadata_key(
            organization_id=organization_id,
            policy_id=policy_id
        )


@pytest.mark.parametrize(
    "organization_id, policy_version_id",
    [
        (0, 10),
        (-1, 10),
        (1, 0),
        (1, -10),
        (True, 10),
        (1, False),
        ("1", 10),
        (1, "10"),
    ]
)
def test_invalid_search_key_ids_are_rejected(
    organization_id,
    policy_version_id
):
    with pytest.raises(ValueError):
        policy_search_key(
            organization_id=organization_id,
            policy_version_id=policy_version_id,
            query="General policy question"
        )

def test_policy_search_prefix_is_tenant_scoped():

    first = policy_search_prefix(
        organization_id=1,
        policy_version_id=10
    )

    second = policy_search_prefix(
        organization_id=2,
        policy_version_id=10
    )

    assert first != second
    assert first.startswith(
        "hg:rag:policy-search:v1:org:1:"
    )
