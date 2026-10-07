"""
Shared Pytest configuration and fixtures for FastAPI backend tests.
"""
import os
from typing import Any, Generator
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.db.session import Base, get_db
from app.main import app as fastapi_app
from app.core.auth.jwt import verify_jwt
from app.models.user import User  # noqa: F401
from app.models.organization import Organization  # noqa: F401
from app.models.organization_membership import OrganizationMembership  # noqa: F401
from app.models.rfq import RFQ, RFQItem, RFQSupplierInvitation  # noqa: F401
from app.models.quotation import Quotation, QuotationItem  # noqa: F401
from app.models.negotiation import NegotiationNote  # noqa: F401

TEST_DB_FILE = "./test_suite.db"
TEST_DB_URL = f"sqlite:///{TEST_DB_FILE}"

test_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db() -> Generator[Session, None, None]:
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


fastapi_app.dependency_overrides[get_db] = override_get_db


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_and_teardown_db():
    """Create all tables before each test and clear data after."""
    Base.metadata.create_all(bind=test_engine)
    yield
    with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_file():
    yield
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except OSError:
            pass


@pytest.fixture()
def client() -> TestClient:
    return TestClient(fastapi_app)


def _make_claims(sub: str, email: str = "test@example.com", name: str = "Test User") -> dict[str, Any]:
    return {"sub": sub, "email": email, "name": name}


@pytest.fixture()
def user_a_claims() -> dict[str, Any]:
    return _make_claims(sub="auth0|user-a", email="a@example.com", name="User A")


@pytest.fixture()
def user_b_claims() -> dict[str, Any]:
    return _make_claims(sub="auth0|user-b", email="b@example.com", name="User B")


@contextmanager
def as_user(claims: dict[str, Any]):
    """
    Context manager that overrides the verify_jwt FastAPI dependency so requests
    within this block appear authenticated as the user described by `claims`.
    """
    old_override = fastapi_app.dependency_overrides.get(verify_jwt)

    def _fake_jwt():
        return claims

    fastapi_app.dependency_overrides[verify_jwt] = _fake_jwt
    try:
        yield
    finally:
        if old_override is not None:
            fastapi_app.dependency_overrides[verify_jwt] = old_override
        else:
            fastapi_app.dependency_overrides.pop(verify_jwt, None)
