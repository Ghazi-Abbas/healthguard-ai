
import os

import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base


# =====================================================
# TEST DATABASE CONFIGURATION
# =====================================================

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://healthguard:healthguard@127.0.0.1:5433/healthguard_test"
)


# =====================================================
# SAFETY CHECK
# =====================================================

if not TEST_DATABASE_URL.endswith("/healthguard_test"):
    raise RuntimeError(
        "Tests must use the separate healthguard_test database."
    )


# =====================================================
# TEST DATABASE ENGINE
# =====================================================

test_engine = create_engine(
    TEST_DATABASE_URL,
    echo=False
)


# =====================================================
# TEST SESSION FACTORY
# =====================================================

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    expire_on_commit=False
)


# =====================================================
# DATABASE FIXTURE
# =====================================================

@pytest.fixture(scope="function")
def db_session():

    # Create all tables before the test
    Base.metadata.create_all(bind=test_engine)

    db = TestingSessionLocal()

    try:
        yield db

    finally:
        db.close()

        # Remove test tables after the test
        Base.metadata.drop_all(bind=test_engine)
